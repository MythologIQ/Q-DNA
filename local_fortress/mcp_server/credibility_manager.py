"""
Q-DNA Source Credibility System (v2.4 Aligned)

Implements P1 features per Q-DNA_SPECIFICATION.md v2.4:
- Source Credibility Index (SCI) management
- Reference Tier Classification (T1-T4)
- Automatic risk grade escalation based on source quality
- Quarantine time enforcement for manipulation track

Thresholds aligned with v2.4 spec:
- Hard Rejection: <35 (was 30 in v2.0)
- T4 Initial: 45 (was 40 in v2.0) - provides probationary buffer
"""

import sqlite3
import time
import json
import hashlib
import deal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent.parent / "ledger" / "qdna_soa_ledger.db"


class ReferenceTier(Enum):
    """Reference quality tiers per Q-DNA Spec Section 5.1"""
    T1 = 1  # Formal Proofs, Primary Records, Official Specs - 100% credibility
    T2 = 2  # Reviewed Standards (MISRA, OWASP), Textbooks - 90% credibility
    T3 = 3  # Reputable Reporting - 70% credibility
    T4 = 4  # Community/Generative (Stack Overflow, LLM) - 40% credibility


# Default credibility scores by tier
# Default credibility scores by tier (v2.4 aligned)
# T4 changed from 40 to 45 per spec §5.3.2 to prevent single-failure blocking
TIER_CREDIBILITY = {
    ReferenceTier.T1: 100,
    ReferenceTier.T2: 90,
    ReferenceTier.T3: 70,
    ReferenceTier.T4: 45  # v2.4: Changed from 40 for probationary buffer
}


@dataclass
class SourceRecord:
    """A tracked source with credibility scoring."""
    source_id: str
    domain: str
    tier: int
    base_credibility: int
    current_sci: float
    citation_count: int
    last_verified: float
    verification_failures: int
    created_at: float


@dataclass
class QuarantineRecord:
    """A quarantined agent record."""
    quarantine_id: int
    agent_did: str
    reason: str
    track: str  # HONEST_ERROR or MANIPULATION
    start_time: float
    end_time: float
    status: str  # ACTIVE, COMPLETED, LIFTED


class CredibilityManager:
    """Manages Source Credibility Index (SCI) and Reference Tiers."""
    
    # Escalation thresholds (v2.4 aligned per spec §5.3.1)
    SCI_ESCALATE_L2 = 60       # Below this, L1 → L2 (Human-in-the-Loop zone)
    SCI_ESCALATE_L3 = 40       # Below this, L2 → L3
    SCI_REJECT = 35            # v2.4: Changed from 30 to prevent cold-start blocking
    
    def __init__(self):
        self._ensure_schema()
    
    @contextmanager
    def get_db(self):
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _ensure_schema(self):
        """Ensure the SCI tables exist."""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            # Source Credibility Index table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS source_credibility (
                    source_id TEXT PRIMARY KEY,
                    domain TEXT NOT NULL,
                    tier INTEGER NOT NULL CHECK(tier BETWEEN 1 AND 4),
                    base_credibility INTEGER NOT NULL,
                    current_sci REAL NOT NULL,
                    citation_count INTEGER DEFAULT 0,
                    last_verified REAL,
                    verification_failures INTEGER DEFAULT 0,
                    created_at REAL NOT NULL
                )
            """)
            
            # Quarantine tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_quarantine (
                    quarantine_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_did TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    track TEXT NOT NULL CHECK(track IN ('HONEST_ERROR', 'MANIPULATION')),
                    start_time REAL NOT NULL,
                    end_time REAL NOT NULL,
                    status TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'COMPLETED', 'LIFTED')),
                    ledger_ref_id INTEGER,
                    FOREIGN KEY (agent_did) REFERENCES agent_registry(did)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sci_domain ON source_credibility(domain)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_quarantine_status ON agent_quarantine(status)
            """)
            
            conn.commit()
    
    def classify_source_tier(self, url: str) -> ReferenceTier:
        """
        Automatically classify a source URL into a tier.
        """
        return self._classify_source_tier(url)

    @deal.post(lambda result: isinstance(result, ReferenceTier))
    def _classify_source_tier(self, url: str) -> ReferenceTier:
        url_lower = url.lower()
        
        # T1: Official specs, RFCs, IEEE, government
        t1_patterns = [
            'rfc-editor.org', 'ieee.org', 'iso.org', 'w3.org',
            'ietf.org', '.gov', 'arxiv.org/abs', 'doi.org'
        ]
        if any(p in url_lower for p in t1_patterns):
            return ReferenceTier.T1
        
        # T2: Reviewed standards, major documentation
        t2_patterns = [
            'owasp.org', 'docs.python.org', 'docs.microsoft.com',
            'developer.mozilla.org', 'kubernetes.io/docs',
            'docs.aws.amazon.com', 'cloud.google.com/docs'
        ]
        if any(p in url_lower for p in t2_patterns):
            return ReferenceTier.T2
        
        # T3: Reputable reporting
        t3_patterns = [
            'github.com', 'medium.com', 'dev.to', 'hackernews',
            'techcrunch.com', 'arstechnica.com', 'wired.com'
        ]
        if any(p in url_lower for p in t3_patterns):
            return ReferenceTier.T3
        
        # T4: Community/Generative (default)
        return ReferenceTier.T4
    
    def register_source(self, url: str, tier: ReferenceTier = None) -> SourceRecord:
        """
        Register a new source with initial credibility scoring.
        
        Args:
            url: The source URL
            tier: Optional tier override (auto-classified if not provided)
            
        Returns:
            SourceRecord
        """
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        domain = parsed.netloc or url[:50]
        
        if tier is None:
            tier = self.classify_source_tier(url)
        
        source_id = hashlib.sha256(url.encode()).hexdigest()[:16]
        base_cred = TIER_CREDIBILITY[tier]
        now = time.time()
        
        record = SourceRecord(
            source_id=source_id,
            domain=domain,
            tier=tier.value,
            base_credibility=base_cred,
            current_sci=float(base_cred),
            citation_count=0,
            last_verified=now,
            verification_failures=0,
            created_at=now
        )
        
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO source_credibility
                (source_id, domain, tier, base_credibility, current_sci, 
                 citation_count, last_verified, verification_failures, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.source_id, record.domain, record.tier,
                record.base_credibility, record.current_sci,
                record.citation_count, record.last_verified,
                record.verification_failures, record.created_at
            ))
            conn.commit()
        
        return record
    
    def get_source_sci(self, url: str) -> Optional[float]:
        """Get the current SCI for a source URL."""
        source_id = hashlib.sha256(url.encode()).hexdigest()[:16]
        
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT current_sci FROM source_credibility WHERE source_id = ?",
                (source_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    
            return row[0] if row else None
    
    @deal.pre(lambda _self, url, success: isinstance(success, bool))
    @deal.post(lambda result: 0 <= result <= 100)
    def update_sci_on_verification(self, url: str, success: bool) -> float:
        """
        Update SCI based on verification result.
        
        - Success: +2 points (max to base)
        - Failure: -10 points (min 0)
        """
        source_id = hashlib.sha256(url.encode()).hexdigest()[:16]
        
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM source_credibility WHERE source_id = ?",
                (source_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                # Register and return
                record = self.register_source(url)
                return record.current_sci
            
            current = row["current_sci"]
            base = row["base_credibility"]
            failures = row["verification_failures"]
            
            if success:
                new_sci = min(base, current + 2)
                new_failures = failures
            else:
                new_sci = max(0, current - 10)
                new_failures = failures + 1
            
            cursor.execute("""
                UPDATE source_credibility 
                SET current_sci = ?, verification_failures = ?, 
                    last_verified = ?, citation_count = citation_count + 1
                WHERE source_id = ?
            """, (new_sci, new_failures, time.time(), source_id))
            conn.commit()
            
            return new_sci
    
            return new_sci
    
    @deal.pre(lambda _self, source_url, current_grade: current_grade in ["L1", "L2", "L3"])
    @deal.post(lambda result: isinstance(result[0], bool))
    @deal.post(lambda result: result[1] in ["L1", "L2", "L3"] or result[1].startswith("REJECT"))
    def should_escalate_risk(self, source_url: str, current_grade: str) -> Tuple[bool, str]:
        """
        Check if risk grade should be escalated based on source SCI.
        
        Returns:
            (should_escalate, new_grade or rejection reason)
        """
        sci = self.get_source_sci(source_url)
        
        if sci is None:
            # Unknown source - register and check tier
            record = self.register_source(source_url)
            sci = record.current_sci
        
        if sci < self.SCI_REJECT:
            return True, "REJECT: Source SCI below threshold"
        
        if current_grade == "L1" and sci < self.SCI_ESCALATE_L2:
            return True, "L2"
        
        if current_grade == "L2" and sci < self.SCI_ESCALATE_L3:
            return True, "L3"
        
        return False, current_grade
    
    def get_low_credibility_sources(self, threshold: float = 50) -> List[Dict]:
        """Get all sources below credibility threshold."""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM source_credibility 
                WHERE current_sci < ?
                ORDER BY current_sci ASC
            """, (threshold,))
            
            return [dict(row) for row in cursor.fetchall()]


class QuarantineManager:
    """Manages agent quarantine for manipulation track."""
    
    # Quarantine durations in seconds
    HONEST_ERROR_DURATION = 0  # No quarantine, just coaching
    MANIPULATION_DURATION = 48 * 60 * 60  # 48 hours
    
    def __init__(self):
        # Ensure schema exists via CredibilityManager
        CredibilityManager()._ensure_schema()
    
    @contextmanager
    def get_db(self):
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def quarantine_agent(self, agent_did: str, reason: str, track: str) -> QuarantineRecord:
        """
        Put an agent in quarantine.
        
        Args:
            agent_did: The agent's DID
            reason: Why they're being quarantined
            track: HONEST_ERROR or MANIPULATION
            
        Returns:
            QuarantineRecord
        """
        now = time.time()
        
        if track == "MANIPULATION":
            duration = self.MANIPULATION_DURATION
        else:
            duration = self.HONEST_ERROR_DURATION
        
        end_time = now + duration
        
        record = QuarantineRecord(
            quarantine_id=0,  # Will be set by DB
            agent_did=agent_did,
            reason=reason,
            track=track,
            start_time=now,
            end_time=end_time,
            status="ACTIVE" if duration > 0 else "COMPLETED"
        )
        
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO agent_quarantine (agent_did, reason, track, start_time, end_time, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (record.agent_did, record.reason, record.track, 
                  record.start_time, record.end_time, record.status))
            
            record.quarantine_id = cursor.lastrowid
            
            # Also update agent status in registry
            cursor.execute("""
                UPDATE agent_registry SET status = 'QUARANTINED', updated_at = datetime('now')
                WHERE did = ?
            """, (agent_did,))
            
            conn.commit()
        
        return record
    
    def is_agent_quarantined(self, agent_did: str) -> Tuple[bool, Optional[QuarantineRecord]]:
        """Check if an agent is currently quarantined."""
        now = time.time()
        
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM agent_quarantine 
                WHERE agent_did = ? AND status = 'ACTIVE' AND end_time > ?
                ORDER BY end_time DESC LIMIT 1
            """, (agent_did, now))
            
            row = cursor.fetchone()
            
            if row:
                return True, QuarantineRecord(
                    quarantine_id=row["quarantine_id"],
                    agent_did=row["agent_did"],
                    reason=row["reason"],
                    track=row["track"],
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    status=row["status"]
                )
            
            return False, None
    
    def release_expired_quarantines(self) -> List[str]:
        """Release all agents whose quarantine has expired."""
        now = time.time()
        released = []
        
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            # Find expired quarantines
            cursor.execute("""
                SELECT agent_did FROM agent_quarantine 
                WHERE status = 'ACTIVE' AND end_time <= ?
            """, (now,))
            
            for row in cursor.fetchall():
                released.append(row["agent_did"])
            
            # Update quarantine status
            cursor.execute("""
                UPDATE agent_quarantine SET status = 'COMPLETED'
                WHERE status = 'ACTIVE' AND end_time <= ?
            """, (now,))
            
            # Update agent registry
            for did in released:
                cursor.execute("""
                    UPDATE agent_registry SET status = 'ACTIVE', updated_at = datetime('now')
                    WHERE did = ?
                """, (did,))
            
            conn.commit()
        
        return released
    
    def get_quarantine_status(self, agent_did: str) -> Dict:
        """Get detailed quarantine status for an agent."""
        is_quarantined, record = self.is_agent_quarantined(agent_did)
        
        if not is_quarantined:
            return {
                "agent_did": agent_did,
                "quarantined": False,
                "status": "ACTIVE"
            }
        
        remaining = max(0, record.end_time - time.time())
        
        return {
            "agent_did": agent_did,
            "quarantined": True,
            "track": record.track,
            "reason": record.reason,
            "remaining_hours": remaining / 3600,
            "ends_at": record.end_time
        }
    
    def get_all_active_quarantines(self) -> List[Dict]:
        """Get all currently active quarantines."""
        now = time.time()
        
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM agent_quarantine 
                WHERE status = 'ACTIVE' AND end_time > ?
            """, (now,))
            
            results = []
            for row in cursor.fetchall():
                remaining = max(0, row["end_time"] - now)
                results.append({
                    "quarantine_id": row["quarantine_id"],
                    "agent_did": row["agent_did"],
                    "track": row["track"],
                    "reason": row["reason"],
                    "remaining_hours": remaining / 3600
                })
            
            return results


class SentinelFallback:
    """Handles Sentinel unavailable fallback logic."""
    
    def __init__(self):
        self.last_sentinel_check = 0
        self.sentinel_available = True
    
    def check_sentinel_health(self) -> bool:
        """Check if Sentinel is available."""
        try:
            from local_fortress.mcp_server.sentinel_engine import SentinelEngine
            sentinel = SentinelEngine()
            # Simple health check - can we instantiate?
            self.sentinel_available = True
            self.last_sentinel_check = time.time()
            return True
        except Exception:
            self.sentinel_available = False
            self.last_sentinel_check = time.time()
            return False
    
    def escalate_grade_on_unavailable(self, current_grade: str) -> str:
        """
        Escalate risk grade if Sentinel is unavailable.
        Per spec: "If Sentinel is unavailable, Judge raises grade by one level"
        """
        if self.sentinel_available:
            return current_grade
        
        escalation = {
            "L1": "L2",
            "L2": "L3",
            "L3": "L3"  # Can't escalate beyond L3
        }
        
        return escalation.get(current_grade, "L3")
    
    def get_fallback_status(self) -> Dict:
        """Get current fallback status."""
        return {
            "sentinel_available": self.sentinel_available,
            "last_check": self.last_sentinel_check,
            "fallback_active": not self.sentinel_available
        }


def run_p1_demo():
    """Demonstrate P1 features."""
    print("\n" + "="*60)
    print("Q-DNA P1 FEATURES DEMONSTRATION")
    print("="*60)
    
    # 1. Source Credibility
    print("\n📊 Source Credibility Index (SCI)")
    print("-" * 40)
    
    cred_mgr = CredibilityManager()
    
    test_sources = [
        "https://www.rfc-editor.org/rfc/rfc2616",
        "https://owasp.org/www-project-top-ten/",
        "https://medium.com/@someone/article",
        "https://stackoverflow.com/questions/123"
    ]
    
    for url in test_sources:
        record = cred_mgr.register_source(url)
        tier_name = ReferenceTier(record.tier).name
        print(f"  {tier_name}: {record.domain} → SCI: {record.current_sci}")
    
    # 2. Risk Escalation
    print("\n⚠️ Risk Escalation Check")
    print("-" * 40)
    
    low_cred_url = "https://random-blog.xyz/post"
    record = cred_mgr.register_source(low_cred_url, ReferenceTier.T4)
    # Simulate failures
    cred_mgr.update_sci_on_verification(low_cred_url, False)
    cred_mgr.update_sci_on_verification(low_cred_url, False)
    
    should_escalate, new_grade = cred_mgr.should_escalate_risk(low_cred_url, "L1")
    print(f"  Low-credibility source: Escalate={should_escalate}, New Grade={new_grade}")
    
    # 3. Quarantine
    print("\n🔒 Quarantine System")
    print("-" * 40)
    
    quar_mgr = QuarantineManager()
    
    # Demo quarantine
    record = quar_mgr.quarantine_agent(
        "did:myth:test:demo",
        "Demo: Citation fabrication detected",
        "MANIPULATION"
    )
    print(f"  Quarantined: {record.agent_did}")
    print(f"  Duration: {(record.end_time - record.start_time) / 3600:.1f} hours")
    
    status = quar_mgr.get_quarantine_status("did:myth:test:demo")
    print(f"  Remaining: {status['remaining_hours']:.1f} hours")
    
    # 4. Sentinel Fallback
    print("\n🛡️ Sentinel Fallback")
    print("-" * 40)
    
    fallback = SentinelFallback()
    available = fallback.check_sentinel_health()
    print(f"  Sentinel available: {available}")
    
    if not available:
        print(f"  L1 → {fallback.escalate_grade_on_unavailable('L1')}")
        print(f"  L2 → {fallback.escalate_grade_on_unavailable('L2')}")
    
    print("\n✨ P1 Demo Complete")


if __name__ == "__main__":
    run_p1_demo()
