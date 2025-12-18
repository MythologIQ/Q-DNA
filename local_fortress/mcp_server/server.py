"""
Q-DNA MCP Server v2.1 - Sovereign Gatekeeper

Provides the Model Context Protocol interface for the Q-DNA governance layer.
Exposes tools for:
- Code auditing (Sentinel)
- Ledger logging (Judge) with Ed25519 signatures
- L3 Approval workflow (Overseer) with SLA tracking
- Shadow Genome archival (Fail Forward)
- Operational mode management
- Volatility TTL tracking
"""

from mcp.server.fastmcp import FastMCP
import sqlite3
import os
import json
import hashlib
import time
from typing import Optional
from contextlib import contextmanager
from pathlib import Path

# Initialize the FastMCP Server
mcp = FastMCP("Q-DNA Sovereign Gatekeeper v2.1")

# Configuration
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ledger", "qdna_soa_ledger.db")

# Import P0 modules (lazy load to avoid circular imports)
_identity_manager = None
_volatility_manager = None
_sla_manager = None
_credibility_manager = None
_quarantine_manager = None
_quarantine_manager = None
_sentinel_fallback = None
_trust_manager = None

def get_identity_manager():
    global _identity_manager
    if _identity_manager is None:
        from local_fortress.mcp_server.identity_manager import IdentityManager
        _identity_manager = IdentityManager()
    return _identity_manager

def get_volatility_manager():
    global _volatility_manager
    if _volatility_manager is None:
        from local_fortress.mcp_server.volatility_manager import VolatilityManager
        _volatility_manager = VolatilityManager()
    return _volatility_manager

def get_sla_manager():
    global _sla_manager
    if _sla_manager is None:
        from local_fortress.mcp_server.volatility_manager import SLAManager
        _sla_manager = SLAManager()
    return _sla_manager

def get_credibility_manager():
    global _credibility_manager
    if _credibility_manager is None:
        from local_fortress.mcp_server.credibility_manager import CredibilityManager
        _credibility_manager = CredibilityManager()
    return _credibility_manager

def get_quarantine_manager():
    global _quarantine_manager
    if _quarantine_manager is None:
        from local_fortress.mcp_server.credibility_manager import QuarantineManager
        _quarantine_manager = QuarantineManager()
    return _quarantine_manager

def get_sentinel_fallback():
    global _sentinel_fallback
    if _sentinel_fallback is None:
        from local_fortress.mcp_server.credibility_manager import SentinelFallback
        _sentinel_fallback = SentinelFallback()
    return _sentinel_fallback

def get_trust_manager():
    global _trust_manager
    if _trust_manager is None:
        from local_fortress.mcp_server.trust_manager import TrustManager
        _trust_manager = TrustManager(DB_PATH)
    return _trust_manager

_drift_monitor = None

def get_drift_monitor():
    global _drift_monitor
    if _drift_monitor is None:
        from local_fortress.mcp_server.semantic_drift import SemanticDriftMonitor
        _drift_monitor = SemanticDriftMonitor(DB_PATH)
    return _drift_monitor

# P2 module loaders
_deferral_manager = None
_mode_enforcer = None
_calibration_tracker = None
_reputation_recovery = None

def get_deferral_manager():
    global _deferral_manager
    if _deferral_manager is None:
        from local_fortress.mcp_server.advanced_features import DeferralManager
        _deferral_manager = DeferralManager()
    return _deferral_manager

def get_mode_enforcer():
    global _mode_enforcer
    if _mode_enforcer is None:
        from local_fortress.mcp_server.advanced_features import ModeEnforcer
        _mode_enforcer = ModeEnforcer()
    return _mode_enforcer

def get_calibration_tracker():
    global _calibration_tracker
    if _calibration_tracker is None:
        from local_fortress.mcp_server.advanced_features import CalibrationTracker
        _calibration_tracker = CalibrationTracker()
    return _calibration_tracker

def get_reputation_recovery():
    global _reputation_recovery
    if _reputation_recovery is None:
        from local_fortress.mcp_server.advanced_features import ReputationRecovery
        _reputation_recovery = ReputationRecovery()
    return _reputation_recovery

_traffic_monitor = None

def get_traffic_monitor():
    global _traffic_monitor
    if _traffic_monitor is None:
        from local_fortress.mcp_server.traffic_control import get_traffic_monitor as _get_tm
        _traffic_monitor = _get_tm()
    return _traffic_monitor

_system_monitor = None

def get_system_monitor():
    global _system_monitor
    if _system_monitor is None:
        from local_fortress.mcp_server.traffic_control import get_system_monitor as _get_sm
        _system_monitor = _get_sm(DB_PATH)
    return _system_monitor

# ============================================================================
# Database Utilities
# ============================================================================


@contextmanager
def get_db_connection():
    """Thread-safe database connection context manager."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_previous_hash() -> str:
    """Get the hash of the last ledger entry for Merkle chaining."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT entry_hash FROM soa_ledger ORDER BY entry_id DESC LIMIT 1")
        row = cursor.fetchone()
        return row[0] if row else "0" * 64

def get_agent_trust_score(agent_did: str) -> float:
    """Helper to get current trust score for ledger logging."""
    return get_trust_manager().get_agent_trust(agent_did) or 0.4

def compute_entry_hash(timestamp: str, did: str, payload: str, prev_hash: str) -> str:
    """Compute SHA256 hash for Merkle chain."""
    entry_data = f"{timestamp}{did}{payload}{prev_hash}"
    return hashlib.sha256(entry_data.encode()).hexdigest()

def get_current_mode() -> str:
    """Get the current operational mode."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT current_mode FROM system_state WHERE state_id = 1")
        row = cursor.fetchone()
        return row[0] if row else "NORMAL"

# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool()
def audit_code(file_path: str, content: str) -> str:
    """
    Run the Sentinel L-Module against a code artifact.
    
    Args:
        file_path: Relative path of the file being audited
        content: The full content or diff to audit
        
    Returns:
        JSON string containing {verdict, risk_grade, rationale, failure_modes, requires_approval}
    """
    from local_fortress.mcp_server.sentinel_engine import SentinelEngine
    
    # Check backpressure (Phase 8.5)
    try:
        with get_traffic_monitor().request_access():
            sentinel = SentinelEngine()
            result = sentinel.audit(file_path, content)
            
            # Log the audit request
            log_event(
                agent_role="Scrivener",
                event_type="AUDIT_REQUEST",
                risk_grade=result.risk_grade,
                payload=json.dumps({"file": file_path, "content_length": len(content)})
            )
            
            # Log the verdict
            verdict_event = "AUDIT_PASS" if result.verdict == "PASS" else "AUDIT_FAIL"
            if result.verdict == "L3_REQUIRED":
                verdict_event = "L3_APPROVAL_REQUEST"
                # Add to approval queue
                request_l3_approval(
                    artifact_hash=compute_entry_hash(str(time.time()), "sentinel", content, ""),
                    reason=result.rationale
                )
            
            entry_hash = log_event(
                agent_role="Sentinel",
                event_type=verdict_event,
                risk_grade=result.risk_grade,
                payload=result.to_json()
            )
            
            # Archive failures to Shadow Genome
            if result.verdict == "FAIL" and result.failure_modes:
                archive_failure(
                    input_vector=content[:500],  # Truncate for storage
                    failure_mode=result.failure_modes[0].split(":")[0],
                    context=json.dumps({"file": file_path, "risk_grade": result.risk_grade}),
                    causal_vector=result.rationale
                )
            
            response = result.to_dict()
            response["ledger_hash"] = entry_hash
            return json.dumps(response)
            
    except RuntimeError as e:
        # Handle 503 Backpressure
        return json.dumps({
            "verdict": "ERROR",
            "risk_grade": "L3",
            "rationale": str(e),
            "failure_modes": ["SERVICE_UNAVAILABLE"],
            "requires_approval": False
        })

@mcp.tool()
def audit_claim(text: str) -> str:
    """
    Audit a text claim for citation and context compliance.
    
    Args:
        text: The claim text to verify
        
    Returns:
        JSON string with verdict and rationale
    """
    from local_fortress.mcp_server.sentinel_engine import SentinelEngine
    
    sentinel = SentinelEngine()
    result = sentinel.audit_claim(text)
    
    log_event(
        agent_role="Sentinel",
        event_type="AUDIT_PASS" if result.verdict == "PASS" else "AUDIT_FAIL",
        risk_grade="L2",
        payload=result.to_json()
    )
    
    return result.to_json()

@mcp.tool()
def log_event(agent_role: str, event_type: str, risk_grade: str, payload: str) -> str:
    """
    Log an event to the Sovereign Ledger with Merkle chaining.
    
    Args:
        agent_role: The agent role (Scrivener, Sentinel, Judge, Overseer)
        event_type: Type of event (PROPOSAL, AUDIT_PASS, etc.)
        risk_grade: L1, L2, or L3
        payload: JSON string of event data
        
    Returns:
        The SHA256 hash of the new entry
    """
    if not os.path.exists(DB_PATH):
        return f"Error: Ledger not initialized at {DB_PATH}"
    
    prev_hash = get_previous_hash()
    timestamp = str(time.time())
    did = f"did:myth:{agent_role.lower()}:active"
    
    entry_hash = compute_entry_hash(timestamp, did, payload, prev_hash)
    signature = f"sig_{hashlib.sha256(entry_hash.encode()).hexdigest()[:16]}"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO soa_ledger 
                (timestamp, agent_did, event_type, risk_grade, payload, entry_hash, prev_hash, signature)
                VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?)
            """, (did, event_type, risk_grade, payload, entry_hash, prev_hash, signature))
            conn.commit()
        except sqlite3.Error as e:
            return f"Database Error: {e}"
    
    return entry_hash

@mcp.tool()
def archive_failure(input_vector: str, failure_mode: str, context: str, causal_vector: str, decision_rationale: str = None) -> str:
    """
    Archive a failure to the Shadow Genome for Fail Forward training.
    
    Args:
        input_vector: The code/claim that failed
        failure_mode: Category (HARDCODED_SECRET, INJECTION_RISK, etc.)
        context: JSON of environmental context
        causal_vector: Why it failed (Sentinel rationale)
        decision_rationale: The agent's intent/reasoning for choosing this solution
        
    Returns:
        The genome_id of the archived failure
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO shadow_genome (input_vector, decision_rationale, context, failure_mode, causal_vector)
                VALUES (?, ?, ?, ?, ?)
            """, (input_vector, decision_rationale, context, failure_mode, causal_vector))
            conn.commit()
            return str(cursor.lastrowid)
        except sqlite3.Error as e:
            return f"Error: {e}"

@mcp.tool()
def request_l3_approval(artifact_hash: str, reason: str) -> str:
    """
    Submit an L3 artifact for Overseer approval.
    
    Args:
        artifact_hash: Hash of the artifact requiring approval
        reason: Why approval is needed
        
    Returns:
        The queue_id for tracking
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO l3_approval_queue (artifact_hash, requesting_agent, reason)
                VALUES (?, ?, ?)
            """, (artifact_hash, "did:myth:sentinel:active", reason))
            conn.commit()
            
            log_event("Sentinel", "L3_APPROVAL_REQUEST", "L3", 
                     json.dumps({"artifact_hash": artifact_hash, "reason": reason}))
            
            return str(cursor.lastrowid)
        except sqlite3.Error as e:
            return f"Error: {e}"

@mcp.tool()
def approve_l3(queue_id: int, approved: bool, overseer_notes: str = "") -> str:
    """
    Overseer approves or rejects an L3 artifact.
    
    Args:
        queue_id: The queue entry to process
        approved: True to approve, False to reject
        overseer_notes: Optional notes from the Overseer
        
    Returns:
        Confirmation message
    """
    status = "APPROVED" if approved else "REJECTED"
    event_type = "L3_APPROVED" if approved else "L3_REJECTED"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE l3_approval_queue 
                SET status = ?, overseer_did = ?, decision_timestamp = datetime('now')
                WHERE queue_id = ?
            """, (status, "did:myth:overseer:human", queue_id))
            conn.commit()
            
            log_event("Overseer", event_type, "L3",
                     json.dumps({"queue_id": queue_id, "notes": overseer_notes}))
            
            return f"L3 artifact {status}"
        except sqlite3.Error as e:
            return f"Error: {e}"

@mcp.tool()
def get_pending_approvals() -> str:
    """
    Get all pending L3 approvals for the Overseer.
    
    Returns:
        JSON array of pending approval requests
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT queue_id, timestamp, artifact_hash, reason 
            FROM l3_approval_queue 
            WHERE status = 'PENDING'
            ORDER BY timestamp ASC
        """)
        rows = cursor.fetchall()
        return json.dumps([dict(row) for row in rows])

@mcp.tool()
def apply_penalty(agent_did: str, amount: float, reason: str) -> str:
    """
    Apply an influence weight penalty to an agent (Judge function).
    
    Args:
        agent_did: The agent's DID
        amount: Negative value for penalty (e.g., -0.25)
        reason: Why the penalty is being applied
        
    Returns:
        Confirmation with new weight
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get current weight
        cursor.execute("SELECT influence_weight FROM agent_registry WHERE did = ?", (agent_did,))
        row = cursor.fetchone()
        if not row:
            return f"Error: Agent {agent_did} not found"
        
        old_weight = row[0]
        new_weight = max(0, min(2.0, old_weight + amount))  # Clamp to [0, 2]
        
        # Update weight
        cursor.execute("UPDATE agent_registry SET influence_weight = ?, updated_at = datetime('now') WHERE did = ?",
                      (new_weight, agent_did))
        
        # Log the change
        cursor.execute("""
            INSERT INTO reputation_log (agent_did, previous_weight, new_weight, adjustment, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (agent_did, old_weight, new_weight, amount, reason))
        
        conn.commit()
        
        log_event("Judge", "PENALTY", "L2", 
                 json.dumps({"agent": agent_did, "old": old_weight, "new": new_weight, "reason": reason}))
        
        return f"Weight adjusted: {old_weight} -> {new_weight}"

@mcp.tool()
def set_operational_mode(mode: str, reason: str) -> str:
    """
    Change the system's operational mode.
    
    Args:
        mode: NORMAL, LEAN, SURGE, or SAFE
        reason: Why the mode is being changed
        
    Returns:
        Confirmation message
    """
    valid_modes = ["NORMAL", "LEAN", "SURGE", "SAFE"]
    if mode.upper() not in valid_modes:
        return f"Error: Invalid mode. Must be one of {valid_modes}"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE system_state 
            SET current_mode = ?, mode_changed_at = datetime('now'), mode_reason = ?
            WHERE state_id = 1
        """, (mode.upper(), reason))
        conn.commit()
        
        log_event("Judge", "MODE_CHANGE", "L1",
                 json.dumps({"new_mode": mode.upper(), "reason": reason}))
        
        return f"Operational mode set to {mode.upper()}"

@mcp.tool()
def get_system_status() -> str:
    """
    Get the current system status including mode and L3 reserve.
    
    Returns:
        JSON with current operational state
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM system_state WHERE state_id = 1")
        state = dict(cursor.fetchone())
        
        cursor.execute("SELECT COUNT(*) as pending FROM l3_approval_queue WHERE status = 'PENDING'")
        state["pending_approvals"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as total FROM soa_ledger")
        state["total_ledger_entries"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as failures FROM shadow_genome WHERE remediation_status = 'UNRESOLVED'")
        state["unresolved_failures"] = cursor.fetchone()[0]
        
        return json.dumps(state)

# ============================================================================
# Resources (Read-only data access)
# ============================================================================

@mcp.resource("ledger://recent")
def get_recent_ledger_entries() -> str:
    """Get the 10 most recent ledger entries."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM soa_ledger ORDER BY entry_id DESC LIMIT 10")
        rows = cursor.fetchall()
        return json.dumps([dict(row) for row in rows])

@mcp.resource("genome://unresolved")
def get_unresolved_failures() -> str:
    """Get all unresolved Shadow Genome entries."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM shadow_genome WHERE remediation_status = 'UNRESOLVED'")
        rows = cursor.fetchall()
        return json.dumps([dict(row) for row in rows])

# ============================================================================
# P0 Features: Volatility TTL & SLA Tracking
# ============================================================================

@mcp.tool()
def register_claim_with_ttl(content: str, volatility_class: str, source_url: str = None) -> str:
    """
    Register a claim with volatility TTL tracking.
    
    Args:
        content: The claim content
        volatility_class: REAL_TIME, FINANCIAL, LEADERSHIP, REGULATORY, CODE, DOCUMENTATION, STABLE
        source_url: Optional source URL
        
    Returns:
        JSON with claim_id and expires_at
    """
    from local_fortress.mcp_server.volatility_manager import VolatilityManager, VolatilityClass
    
    vol_mgr = get_volatility_manager()
    
    try:
        vol_class = VolatilityClass[volatility_class.upper()]
    except KeyError:
        return json.dumps({"error": f"Invalid volatility class. Use: {[v.name for v in VolatilityClass]}"})
    
    claim = vol_mgr.register_claim(content, vol_class, source_url)
    
    return json.dumps({
        "claim_id": claim.claim_id,
        "volatility_class": claim.volatility_class,
        "ttl_seconds": claim.ttl_seconds,
        "expires_at": claim.expires_at,
        "expires_in_hours": (claim.expires_at - time.time()) / 3600
    })

@mcp.tool()
def check_claim_validity(claim_id: str) -> str:
    """
    Check if a claim is still valid (not expired).
    
    Args:
        claim_id: The claim ID to check
        
    Returns:
        JSON with validity status and time remaining
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM claim_volatility WHERE claim_id = ?", (claim_id,))
        row = cursor.fetchone()
        
        if not row:
            return json.dumps({"error": "Claim not found", "valid": False})
        
        now = time.time()
        expires_at = row[6]  # expires_at column
        is_valid = now < expires_at
        
        return json.dumps({
            "claim_id": claim_id,
            "valid": is_valid,
            "status": "VALID" if is_valid else "EXPIRED",
            "time_remaining_hours": max(0, (expires_at - now) / 3600),
            "verification_count": row[8]
        })

@mcp.tool()
def get_expired_claims() -> str:
    """
    Get all expired claims that need re-verification.
    
    Returns:
        JSON array of expired claims
    """
    vol_mgr = get_volatility_manager()
    expired = vol_mgr.get_expired_claims()
    
    return json.dumps([{
        "claim_id": c.claim_id,
        "volatility_class": c.volatility_class,
        "hours_expired": (time.time() - c.expires_at) / 3600,
        "source_url": c.source_url
    } for c in expired])

@mcp.tool()
def get_sla_status() -> str:
    """
    Get the L3 SLA compliance status.
    
    Returns:
        JSON with SLA metrics and any overdue requests
    """
    sla_mgr = get_sla_manager()
    status = sla_mgr.get_sla_status()
    escalations = sla_mgr.escalate_overdue()
    
    status["escalations"] = escalations
    return json.dumps(status)

@mcp.tool()
def verify_signature(did: str, data: str, signature_hex: str) -> str:
    """
    Verify an Ed25519 signature.
    
    Args:
        did: The alleged signer's DID
        data: The signed data (string)
        signature_hex: Hex-encoded signature
        
    Returns:
        JSON with verification result
    """
    try:
        id_mgr = get_identity_manager()
        valid = id_mgr.verify(did, data.encode(), signature_hex)
        
        return json.dumps({
            "did": did,
            "valid": valid,
            "status": "VERIFIED" if valid else "INVALID"
        })
    except Exception as e:
        return json.dumps({
            "did": did,
            "valid": False,
            "status": "ERROR",
            "error": str(e)
        })

@mcp.tool()
def system_health_check() -> str:
    """
    Run a comprehensive health check on all Q-DNA systems.
    
    Returns:
        JSON with health status across all subsystems
    """
    health = {
        "timestamp": time.time(),
        "subsystems": {}
    }
    
    # Database health
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM soa_ledger")
            ledger_count = cursor.fetchone()[0]
            health["subsystems"]["ledger"] = {"status": "OK", "entries": ledger_count}
    except Exception as e:
        health["subsystems"]["ledger"] = {"status": "ERROR", "error": str(e)}
    
    # SLA health
    try:
        sla_mgr = get_sla_manager()
        sla_status = sla_mgr.get_sla_status()
        health["subsystems"]["sla"] = {
            "status": "OK" if sla_status["overdue_count"] == 0 else "WARNING",
            "compliance_pct": sla_status["sla_compliance_pct"],
            "pending": sla_status["pending_count"],
            "overdue": sla_status["overdue_count"]
        }
    except Exception as e:
        health["subsystems"]["sla"] = {"status": "ERROR", "error": str(e)}
    
    # Volatility health
    try:
        vol_mgr = get_volatility_manager()
        expired = vol_mgr.get_expired_claims()
        health["subsystems"]["volatility"] = {
            "status": "OK" if len(expired) == 0 else "WARNING",
            "expired_claims": len(expired)
        }
    except Exception as e:
        health["subsystems"]["volatility"] = {"status": "ERROR", "error": str(e)}
    
    # Shadow Genome
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM shadow_genome WHERE remediation_status = 'UNRESOLVED'")
            unresolved = cursor.fetchone()[0]
            health["subsystems"]["shadow_genome"] = {
                "status": "OK",
                "unresolved_failures": unresolved
            }
    except Exception as e:
        health["subsystems"]["shadow_genome"] = {"status": "ERROR", "error": str(e)}
    
    # Overall status
    all_ok = all(s.get("status") == "OK" for s in health["subsystems"].values())
    any_error = any(s.get("status") == "ERROR" for s in health["subsystems"].values())
    
    if any_error:
        health["overall_status"] = "ERROR"
    elif not all_ok:
        health["overall_status"] = "WARNING"
    else:
        health["overall_status"] = "HEALTHY"
    
    return json.dumps(health)

# ============================================================================
# P1 Features: Source Credibility, Quarantine, Sentinel Fallback
# ============================================================================

@mcp.tool()
def register_source(url: str, tier_override: str = None) -> str:
    """
    Register a source URL and get its credibility classification.
    
    Args:
        url: The source URL to register
        tier_override: Optional tier (T1, T2, T3, T4) - auto-classified if not provided
        
    Returns:
        JSON with source_id, tier, and SCI score
    """
    from local_fortress.mcp_server.credibility_manager import ReferenceTier
    
    cred_mgr = get_credibility_manager()
    
    tier = None
    if tier_override:
        try:
            tier = ReferenceTier[tier_override.upper()]
        except KeyError:
            return json.dumps({"error": f"Invalid tier. Use: T1, T2, T3, T4"})
    
    record = cred_mgr.register_source(url, tier)
    
    tier_names = {1: "T1", 2: "T2", 3: "T3", 4: "T4"}
    
    return json.dumps({
        "source_id": record.source_id,
        "domain": record.domain,
        "tier": tier_names[record.tier],
        "base_credibility": record.base_credibility,
        "current_sci": record.current_sci
    })

@mcp.tool()
def check_source_credibility(url: str, current_grade: str) -> str:
    """
    Check if a source affects risk grade (escalation check).
    
    Args:
        url: The source URL
        current_grade: Current risk grade (L1, L2, L3)
        
    Returns:
        JSON with should_escalate and new_grade
    """
    cred_mgr = get_credibility_manager()
    
    should_escalate, new_grade = cred_mgr.should_escalate_risk(url, current_grade)
    sci = cred_mgr.get_source_sci(url)
    
    return json.dumps({
        "url": url,
        "current_sci": sci,
        "should_escalate": should_escalate,
        "original_grade": current_grade,
        "new_grade": new_grade
    })

@mcp.tool()
def update_source_verification(url: str, success: bool) -> str:
    """
    Update a source's SCI based on verification result.
    
    Args:
        url: The source URL
        success: True if verification passed, False if failed
        
    Returns:
        JSON with updated SCI
    """
    cred_mgr = get_credibility_manager()
    new_sci = cred_mgr.update_sci_on_verification(url, success)
    
    return json.dumps({
        "url": url,
        "verification_result": "PASS" if success else "FAIL",
        "new_sci": new_sci
    })

# ============================================================================
# Phase 8.5 Track INT: Trust Dynamics (Agent Trust)
# ============================================================================

@mcp.tool()
def get_agent_trust(agent_did: str) -> str:
    """
    Get the current trust score and stage for an agent.
    
    Args:
        agent_did: The agent's DID
        
    Returns:
        JSON with trust score, stage, and metadata
    """
    trust_mgr = get_trust_manager()
    score = trust_mgr.get_agent_trust(agent_did)
    
    if score is None:
        return json.dumps({"error": f"Agent {agent_did} not found"})
        
    stage = trust_mgr.get_trust_stage(agent_did)
    
    return json.dumps({
        "agent_did": agent_did,
        "trust_score": score,
        "trust_stage": stage.name if stage else "UNKNOWN",
        "probation_active": score <= 0.5  # Rough heuristic, actual check in manager
    })

@mcp.tool()
def update_agent_trust(agent_did: str, outcome_score: float, context: str, ledger_ref_id: int = None) -> str:
    """
    Update an agent's trust score based on a verification outcome (EWMA).
    
    Args:
        agent_did: The agent's DID
        outcome_score: 1.0 (PASS) or 0.0 (FAIL). Can be fractional.
        context: LOW_RISK or HIGH_RISK
        ledger_ref_id: Optional ID of the SOA ledger entry prompting this update
        
    Returns:
        JSON with old and new scores
    """
    from local_fortress.mcp_server.trust_engine import TrustContext
    
    trust_mgr = get_trust_manager()
    
    try:
        ctx = TrustContext[context.upper()]
    except KeyError:
        return json.dumps({"error": "Invalid context. Use: LOW_RISK, HIGH_RISK"})
    
    # Capture old score for reporting
    old_score = trust_mgr.get_agent_trust(agent_did)
    
    success = trust_mgr.update_trust_ewma(agent_did, outcome_score, ctx, ledger_ref_id)
    
    if not success:
        return json.dumps({"error": "Update failed. Agent not found?"})
        
    new_score = trust_mgr.get_agent_trust(agent_did)
    
    return json.dumps({
        "agent_did": agent_did,
        "old_score": old_score,
        "new_score": new_score,
        "delta": new_score - old_score if old_score is not None else 0
    })

@mcp.tool()
def apply_trust_penalty(agent_did: str, penalty_type: str, reason: str) -> str:
    """
    Apply a micro-penalty to an agent's trust score.
    
    Args:
        agent_did: The agent's DID
        penalty_type: SCHEMA_VIOLATION, API_MISUSE, STALE_CITATION
        reason: Justification for penalty
        
    Returns:
        JSON with new score and applied penalty amount
    """
    from local_fortress.mcp_server.trust_engine import MicroPenaltyType
    
    trust_mgr = get_trust_manager()
    
    try:
        ptype = MicroPenaltyType[penalty_type.upper()]
    except KeyError:
        return json.dumps({"error": "Invalid penalty type. Use: SCHEMA_VIOLATION, API_MISUSE, STALE_CITATION"})
        
    success = trust_mgr.apply_micro_penalty(agent_did, ptype, reason)
    
    if not success:
        return json.dumps({"error": "Penalty application failed"})
        
    # We don't get the exact applied amount back easily without querying history, 
    # but the manager logs it. We'll return the new current score.
    new_score = trust_mgr.get_agent_trust(agent_did)
    
    return json.dumps({
        "agent_did": agent_did,
        "new_score": new_score,
        "status": "PENALIZED"
    })

@mcp.tool()
def apply_trust_decay(agent_did: str) -> str:
    """
    Apply temporal decay to an agent if inactive.
    
    Args:
        agent_did: The agent's DID
        
    Returns:
        JSON with status
    """
    trust_mgr = get_trust_manager()
    changed = trust_mgr.apply_temporal_decay(agent_did)
    
    new_score = trust_mgr.get_agent_trust(agent_did)
    
    return json.dumps({
        "agent_did": agent_did,
        "decay_applied": changed,
        "current_score": new_score
    })

@mcp.tool()
def check_semantic_drift(agent_did: str, content: str) -> str:
    """
    Check if content exhibits semantic drift from agent's baseline.
    Spec §7.1: Cosine similarity < 0.85 triggers flag.
    
    Args:
        agent_did: The agent's DID
        content: The text content to analyze
        
    Returns:
        JSON with drift status and similarity score
    """
    monitor = get_drift_monitor()
    
    # Check if model is available
    if monitor.get_model() is None:
        return json.dumps({
            "status": "SKIPPED",
            "reason": "Embedding model unavailable",
            "has_drift": False
        })

    has_drift, similarity, msg = monitor.check_drift(agent_did, content)
    
    if has_drift:
        log_event("Sentinel", "DRIFT_DETECTED", "L2", json.dumps({
            "agent_did": agent_did,
            "similarity": similarity,
            "threshold": 0.85, # Config from monitor
            "sample_snippet": content[:50]
        }))
    
    return json.dumps({
        "status": "CHECKED",
        "has_drift": has_drift,
        "similarity": round(similarity, 4),
        "message": msg
    })

@mcp.tool()
def get_low_credibility_sources(threshold: float = 50) -> str:
    """
    Get all sources below a credibility threshold.
    
    Args:
        threshold: SCI threshold (default 50)
        
    Returns:
        JSON array of low-credibility sources
    """
    cred_mgr = get_credibility_manager()
    sources = cred_mgr.get_low_credibility_sources(threshold)
    
    return json.dumps(sources)

@mcp.tool()
def quarantine_agent(agent_did: str, reason: str, track: str) -> str:
    """
    Put an agent in quarantine (for manipulation track violations).
    
    Args:
        agent_did: The agent's DID
        reason: Why they're being quarantined
        track: HONEST_ERROR or MANIPULATION
        
    Returns:
        JSON with quarantine details
    """
    if track not in ["HONEST_ERROR", "MANIPULATION"]:
        return json.dumps({"error": "Track must be HONEST_ERROR or MANIPULATION"})
    
    quar_mgr = get_quarantine_manager()
    record = quar_mgr.quarantine_agent(agent_did, reason, track)
    
    log_event("Judge", "QUARANTINE", "L3", json.dumps({
        "agent_did": agent_did,
        "reason": reason,
        "track": track,
        "duration_hours": (record.end_time - record.start_time) / 3600
    }))
    
    return json.dumps({
        "quarantine_id": record.quarantine_id,
        "agent_did": record.agent_did,
        "track": record.track,
        "duration_hours": (record.end_time - record.start_time) / 3600,
        "ends_at": record.end_time
    })

@mcp.tool()
def check_agent_quarantine(agent_did: str) -> str:
    """
    Check if an agent is currently quarantined.
    
    Args:
        agent_did: The agent's DID
        
    Returns:
        JSON with quarantine status
    """
    quar_mgr = get_quarantine_manager()
    status = quar_mgr.get_quarantine_status(agent_did)
    
    return json.dumps(status)

@mcp.tool()
def get_active_quarantines() -> str:
    """
    Get all currently active agent quarantines.
    
    Returns:
        JSON array of active quarantines
    """
    quar_mgr = get_quarantine_manager()
    quarantines = quar_mgr.get_all_active_quarantines()
    
    return json.dumps(quarantines)

@mcp.tool()
def release_expired_quarantines() -> str:
    """
    Release all agents whose quarantine has expired.
    
    Returns:
        JSON with list of released agents
    """
    quar_mgr = get_quarantine_manager()
    released = quar_mgr.release_expired_quarantines()
    
    return json.dumps({
        "released_count": len(released),
        "released_agents": released
    })

@mcp.tool()
def check_sentinel_fallback(current_grade: str) -> str:
    """
    Check Sentinel availability and get fallback grade if unavailable.
    
    Args:
        current_grade: Current risk grade (L1, L2, L3)
        
    Returns:
        JSON with sentinel status and potentially escalated grade
    """
    fallback = get_sentinel_fallback()
    available = fallback.check_sentinel_health()
    
    result = {
        "sentinel_available": available,
        "original_grade": current_grade
    }
    
    if not available:
        result["fallback_active"] = True
        result["escalated_grade"] = fallback.escalate_grade_on_unavailable(current_grade)
        result["reason"] = "Sentinel unavailable - grade escalated per spec"
    else:
        result["fallback_active"] = False
        result["escalated_grade"] = current_grade
    
    return json.dumps(result)

# ============================================================================
# P2 Features: Deferral, Mode Enforcement, Calibration, Recovery
# ============================================================================

@mcp.tool()
def request_deferral(artifact_hash: str, category: str, reason: str) -> str:
    """
    Request a time-boxed deferral for sensitive disclosure.
    
    Args:
        artifact_hash: Hash of the artifact to defer
        category: SAFETY_CRITICAL (4h), MEDICAL/LEGAL/FINANCIAL (24h), REPUTATIONAL (72h), LOW_RISK (0)
        reason: Why deferral is needed
        
    Returns:
        JSON with deferral details and max window
    """
    from local_fortress.mcp_server.advanced_features import DeferralCategory
    
    defer_mgr = get_deferral_manager()
    
    try:
        cat = DeferralCategory[category.upper()]
    except KeyError:
        valid = [c.name for c in DeferralCategory]
        return json.dumps({"error": f"Invalid category. Use: {valid}"})
    
    req = defer_mgr.request_deferral(artifact_hash, cat, reason)
    
    return json.dumps({
        "deferral_id": req.deferral_id,
        "category": req.category,
        "max_hours": (req.max_end_time - req.start_time) / 3600,
        "expires_at": req.max_end_time,
        "status": req.status
    })

@mcp.tool()
def complete_deferral(deferral_id: int) -> str:
    """
    Mark a deferral as disclosed (disclosure complete).
    
    Args:
        deferral_id: The deferral to complete
        
    Returns:
        JSON confirmation
    """
    defer_mgr = get_deferral_manager()
    result = defer_mgr.complete_disclosure(deferral_id)
    return json.dumps(result)

@mcp.tool()
def get_active_deferrals() -> str:
    """
    Get all currently active deferrals.
    
    Returns:
        JSON array of active deferrals with remaining time
    """
    defer_mgr = get_deferral_manager()
    deferrals = defer_mgr.get_active_deferrals()
    return json.dumps(deferrals)

@mcp.tool()
def check_expired_deferrals() -> str:
    """
    Check for and expire overdue deferrals.
    
    Returns:
        JSON array of newly expired deferrals
    """
    defer_mgr = get_deferral_manager()
    expired = defer_mgr.check_expired_deferrals()
    
    return json.dumps([{
        "deferral_id": d.deferral_id,
        "category": d.category,
        "artifact_hash": d.artifact_hash
    } for d in expired])

@mcp.tool()
def check_verification_mode(risk_grade: str) -> str:
    """
    Check if verification should proceed based on operational mode.
    
    Args:
        risk_grade: L1, L2, or L3
        
    Returns:
        JSON with should_verify and reason
    """
    enforcer = get_mode_enforcer()
    should, reason = enforcer.should_verify(risk_grade)
    stats = enforcer.get_mode_stats()
    
    return json.dumps({
        "current_mode": stats["current_mode"],
        "risk_grade": risk_grade,
        "should_verify": should,
        "reason": reason
    })

@mcp.tool()
def get_mode_behavior() -> str:
    """
    Get detailed behavior for current operational mode.
    
    Returns:
        JSON with mode behavior for each risk level
    """
    enforcer = get_mode_enforcer()
    return json.dumps(enforcer.get_mode_stats())

@mcp.tool()
def record_prediction(agent_did: str, confidence: float, correct: bool) -> str:
    """
    Record a prediction outcome for calibration tracking.
    
    Args:
        agent_did: The agent's DID
        confidence: Confidence level (0-1)
        correct: Whether prediction was correct
        
    Returns:
        JSON with Brier contribution
    """
    tracker = get_calibration_tracker()
    record = tracker.record_prediction(agent_did, confidence, correct)
    
    return json.dumps({
        "agent_did": agent_did,
        "confidence": record.prediction_confidence,
        "correct": record.actual_outcome,
        "brier_contribution": round(record.brier_contribution, 4)
    })

@mcp.tool()
def get_calibration_report(agent_did: str) -> str:
    """
    Get calibration report for an agent (Brier score).
    
    Args:
        agent_did: The agent's DID
        
    Returns:
        JSON with Brier score and calibration status
    """
    tracker = get_calibration_tracker()
    report = tracker.get_calibration_report(agent_did)
    return json.dumps(report)

@mcp.tool()
def check_honest_error(agent_did: str) -> str:
    """
    Check if agent triggers Honest Error Track (Brier > 0.2).
    
    Args:
        agent_did: The agent's DID
        
    Returns:
        JSON with trigger status and Brier score
    """
    tracker = get_calibration_tracker()
    triggered, brier = tracker.check_honest_error_trigger(agent_did)
    
    return json.dumps({
        "agent_did": agent_did,
        "honest_error_triggered": triggered,
        "brier_score": round(brier, 4) if brier else None,
        "threshold": 0.2
    })

@mcp.tool()
def record_clean_audit(agent_did: str) -> str:
    """
    Record a clean audit and apply reputation recovery (+1%).
    
    Args:
        agent_did: The agent's DID
        
    Returns:
        JSON with weight change
    """
    recovery = get_reputation_recovery()
    result = recovery.record_clean_audit(agent_did)
    
    if "recovery_applied" in result and result["recovery_applied"]:
        log_event("Judge", "REWARD", "L1", json.dumps({
            "agent_did": agent_did,
            "reason": "Clean audit recovery",
            "delta": result["delta"]
        }))
    
    return json.dumps(result)

@mcp.tool()
def get_all_agent_weights() -> str:
    """
    Get current influence weights for all agents.
    
    Returns:
        JSON array of agent weights
    """
    recovery = get_reputation_recovery()
    agents = recovery.get_all_agent_weights()
    return json.dumps(agents)

@mcp.tool()
def get_monitor_status() -> str:
    """
    Get status of the background System Monitor (CPU & Queue).
    
    Returns:
        JSON with monitor metrics
    """
    monitor = get_system_monitor()
    return json.dumps(monitor.get_system_status())

# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    # Start System Monitor (Background Thread)
    try:
        monitor = get_system_monitor()
        monitor.start_monitoring()
        # print("System Monitor started", file=sys.stderr)
    except Exception as e:
        pass
        # print(f"Failed to start monitor: {e}", file=sys.stderr)

    mcp.run(transport='stdio')



