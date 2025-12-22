"""
QoreLogic Evolutionary Bootstrapping System

Implements the "Fail Forward" multi-pass build model:
1. Generate multiple candidate solutions (variants)
2. Evaluate each variant against the Quality DNA
3. Select the best-scoring variant for use
4. Archive non-selected variants to Shadow Genome for potential recall
5. All variants contribute to system learning

Key Concepts:
- Generation: A batch of candidate solutions for a single task
- Variant: A single candidate solution within a generation
- Selection: The process of choosing the best variant
- Archive: Non-selected variants stored for future recall
- Recall: Retrieving archived variants when conditions change
"""

import json
import hashlib
import time
import sqlite3
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import contextmanager


# Import Sentinel for evaluation
import sys
import os

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

try:
    from .sentinel_engine import SentinelEngine, AuditResult
except ImportError:
    # Fallback for direct execution
    from sentinel_engine import SentinelEngine, AuditResult

DB_PATH = os.path.join(PROJECT_ROOT, "local_fortress", "ledger", "qorelogic_soa_ledger.db")



class VariantStatus(Enum):
    PENDING = "PENDING"      # Awaiting evaluation
    SELECTED = "SELECTED"    # Chosen as best for this generation
    ARCHIVED = "ARCHIVED"    # Stored in Shadow Genome for potential recall
    RECALLED = "RECALLED"    # Previously archived, now active
    REJECTED = "REJECTED"    # Critical failure, not suitable for recall


@dataclass
class Variant:
    """A single candidate solution."""
    variant_id: str
    generation_id: str
    content: str
    source: str  # "scrivener", "human", "recalled"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Evaluation results (populated after audit)
    audit_result: Optional[AuditResult] = None
    fitness_score: float = 0.0
    status: VariantStatus = VariantStatus.PENDING
    
    def compute_hash(self) -> str:
        """Compute content hash for deduplication."""
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]


@dataclass
class Generation:
    """A collection of variants for a single task."""
    generation_id: str
    task_description: str
    file_path: str
    created_at: float = field(default_factory=time.time)
    
    variants: List[Variant] = field(default_factory=list)
    selected_variant_id: Optional[str] = None
    
    # Aggregated metrics
    total_evaluated: int = 0
    pass_count: int = 0
    fail_count: int = 0
    
    def add_variant(self, content: str, source: str = "scrivener", metadata: Dict = None) -> Variant:
        """Add a new variant to this generation."""
        variant_id = f"{self.generation_id}_v{len(self.variants)}"
        variant = Variant(
            variant_id=variant_id,
            generation_id=self.generation_id,
            content=content,
            source=source,
            metadata=metadata or {}
        )
        self.variants.append(variant)
        return variant


class FitnessEvaluator:
    """
    Calculates a fitness score for each variant based on multiple factors.
    
    Scoring Philosophy (per Research First Principles):
    - Passing audit is necessary but not sufficient
    - Lower complexity = higher fitness
    - Faster verification = higher fitness
    - Novel solutions (not duplicates) get bonus
    """
    
    # Fitness weights
    WEIGHT_AUDIT_PASS = 50.0      # Must pass to be viable
    WEIGHT_COMPLEXITY = 20.0      # Lower is better
    WEIGHT_LATENCY = 10.0         # Faster is better
    WEIGHT_NOVELTY = 10.0         # Unique solutions preferred
    WEIGHT_L3_CLEAN = 10.0        # L3 without issues is excellent
    
    def __init__(self, existing_hashes: set = None):
        self.existing_hashes = existing_hashes or set()
        self.sentinel = SentinelEngine()
    
    def evaluate(self, variant: Variant, file_path: str) -> float:
        """
        Evaluate a variant and return its fitness score.
        Updates the variant's audit_result and fitness_score.
        """
        # Run Sentinel audit
        result = self.sentinel.audit(file_path, variant.content)
        variant.audit_result = result
        
        score = 0.0
        
        # 1. Audit Pass/Fail (binary gate)
        if result.verdict == "PASS":
            score += self.WEIGHT_AUDIT_PASS
        elif result.verdict == "L3_REQUIRED":
            # L3 that passes checks gets partial credit
            if not result.failure_modes:
                score += self.WEIGHT_AUDIT_PASS * 0.8
            else:
                score += self.WEIGHT_AUDIT_PASS * 0.3
        else:
            # Failed audit - still evaluate for learning but low score
            score += self.WEIGHT_AUDIT_PASS * 0.1
        
        # 2. Complexity (inverse relationship)
        # Get complexity from findings if available
        complexity = 1
        for finding in result.failure_modes:
            if "COMPLEXITY" in finding:
                try:
                    complexity = int(finding.split("=")[-1])
                except:
                    pass
        complexity_score = max(0, self.WEIGHT_COMPLEXITY * (1 - complexity / 30))
        score += complexity_score
        
        # 3. Latency (faster is better)
        latency_score = self.WEIGHT_LATENCY * max(0, 1 - result.latency_ms / 100)
        score += latency_score
        
        # 4. Novelty bonus
        content_hash = variant.compute_hash()
        if content_hash not in self.existing_hashes:
            score += self.WEIGHT_NOVELTY
            self.existing_hashes.add(content_hash)
        
        # 5. L3 Clean bonus
        if result.risk_grade == "L3" and result.verdict == "PASS":
            score += self.WEIGHT_L3_CLEAN
        
        variant.fitness_score = round(score, 2)
        return variant.fitness_score


class EvolutionaryBootstrapper:
    """
    Orchestrates the multi-pass build process with variant selection and archival.
    """
    
    def __init__(self):
        self.sentinel = SentinelEngine()
        self.evaluator = FitnessEvaluator()
    
    @contextmanager
    def get_db(self):
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def create_generation(self, task: str, file_path: str) -> Generation:
        """Create a new generation for a task."""
        gen_id = f"gen_{int(time.time())}_{hashlib.md5(task.encode()).hexdigest()[:8]}"
        return Generation(
            generation_id=gen_id,
            task_description=task,
            file_path=file_path
        )
    
    def evaluate_generation(self, generation: Generation) -> Variant:
        """
        Evaluate all variants in a generation and select the best one.
        Archives non-selected variants to Shadow Genome.
        
        Returns the selected variant.
        """
        if not generation.variants:
            raise ValueError("Generation has no variants to evaluate")
        
        # Evaluate all variants
        for variant in generation.variants:
            self.evaluator.evaluate(variant, generation.file_path)
            generation.total_evaluated += 1
            
            if variant.audit_result.verdict == "PASS":
                generation.pass_count += 1
            else:
                generation.fail_count += 1
        
        # Sort by fitness (descending)
        sorted_variants = sorted(
            generation.variants, 
            key=lambda v: v.fitness_score, 
            reverse=True
        )
        
        # Select the best
        best = sorted_variants[0]
        best.status = VariantStatus.SELECTED
        generation.selected_variant_id = best.variant_id
        
        # Archive the rest
        for variant in sorted_variants[1:]:
            if variant.audit_result.verdict == "FAIL" and variant.fitness_score < 20:
                # Critical failure - not worth recalling
                variant.status = VariantStatus.REJECTED
            else:
                # Archive for potential recall
                variant.status = VariantStatus.ARCHIVED
                self._archive_to_shadow_genome(variant, generation)
        
        # Log the generation results
        self._log_generation(generation)
        
        return best
    
    def _archive_to_shadow_genome(self, variant: Variant, generation: Generation):
        """Archive a non-selected variant to the Shadow Genome."""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            context = {
                "generation_id": generation.generation_id,
                "task": generation.task_description,
                "file_path": generation.file_path,
                "fitness_score": variant.fitness_score,
                "source": variant.source,
                "variant_metadata": variant.metadata,
                "can_recall": variant.status == VariantStatus.ARCHIVED
            }
            
            failure_mode = "NON_OPTIMAL"
            if variant.audit_result and variant.audit_result.failure_modes:
                failure_mode = variant.audit_result.failure_modes[0].split(":")[0]
            
            causal = variant.audit_result.rationale if variant.audit_result else "Not evaluated"
            
            cursor.execute("""
                INSERT INTO shadow_genome 
                (input_vector, context, failure_mode, causal_vector, remediation_status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                variant.content[:2000],  # Truncate for storage
                json.dumps(context),
                failure_mode,
                causal,
                "UNRESOLVED" if variant.status == VariantStatus.ARCHIVED else "WONT_FIX"
            ))
            conn.commit()
    
    def _log_generation(self, generation: Generation):
        """Log generation results to the SOA Ledger."""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            # Get previous hash
            cursor.execute("SELECT entry_hash FROM soa_ledger ORDER BY entry_id DESC LIMIT 1")
            row = cursor.fetchone()
            prev_hash = row[0] if row else "0" * 64
            
            payload = {
                "generation_id": generation.generation_id,
                "task": generation.task_description,
                "file_path": generation.file_path,
                "total_variants": len(generation.variants),
                "pass_count": generation.pass_count,
                "fail_count": generation.fail_count,
                "selected_variant": generation.selected_variant_id,
                "best_fitness": max(v.fitness_score for v in generation.variants)
            }
            payload_str = json.dumps(payload, sort_keys=True)
            
            timestamp = str(time.time())
            did = "did:myth:judge:bootstrap"
            entry_data = f"{timestamp}{did}{payload_str}{prev_hash}"
            entry_hash = hashlib.sha256(entry_data.encode()).hexdigest()
            signature = f"sig_boot_{entry_hash[:8]}"
            
            cursor.execute("""
                INSERT INTO soa_ledger 
                (timestamp, agent_did, event_type, risk_grade, payload, entry_hash, prev_hash, signature, workspace_id)
                VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
            """, (did, "GENERATION_COMPLETE", "L2", payload_str, entry_hash, prev_hash, signature, "default"))
            conn.commit()
    
    def recall_variant(self, genome_id: int, reason: str) -> Optional[Dict]:
        """
        Recall a previously archived variant from the Shadow Genome.
        
        This is used when conditions change and a previously "non-optimal"
        solution becomes relevant.
        """
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            # Fetch the archived variant
            cursor.execute("""
                SELECT genome_id, input_vector, context, failure_mode, causal_vector
                FROM shadow_genome 
                WHERE genome_id = ? AND remediation_status != 'WONT_FIX'
            """, (genome_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            context = json.loads(row["context"])
            
            # Mark as recalled
            cursor.execute("""
                UPDATE shadow_genome 
                SET remediation_status = 'RESOLVED'
                WHERE genome_id = ?
            """, (genome_id,))
            
            # Log the recall
            prev_hash = "0" * 64
            cursor.execute("SELECT entry_hash FROM soa_ledger ORDER BY entry_id DESC LIMIT 1")
            prev_row = cursor.fetchone()
            if prev_row:
                prev_hash = prev_row[0]
            
            payload = {
                "genome_id": genome_id,
                "reason": reason,
                "original_failure": row["failure_mode"],
                "original_context": context
            }
            payload_str = json.dumps(payload, sort_keys=True)
            timestamp = str(time.time())
            did = "did:myth:judge:recall"
            entry_data = f"{timestamp}{did}{payload_str}{prev_hash}"
            entry_hash = hashlib.sha256(entry_data.encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO soa_ledger 
                (timestamp, agent_did, event_type, risk_grade, payload, entry_hash, prev_hash, signature, workspace_id)
                VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
            """, (did, "SHADOW_RECALL", "L2", payload_str, entry_hash, prev_hash, f"sig_recall_{entry_hash[:8]}", "default"))
            
            conn.commit()
            
            return {
                "genome_id": genome_id,
                "content": row["input_vector"],
                "original_context": context,
                "recall_reason": reason
            }
    
    def query_shadow_genome(self, failure_mode: str = None, min_fitness: float = 0) -> List[Dict]:
        """
        Query the Shadow Genome for archived variants.
        
        Use this to find solutions that might be relevant when:
        - A new context matches a previously failed context
        - Requirements change making old solutions viable
        - Learning from past "failures" for new tasks
        """
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT genome_id, input_vector, context, failure_mode, causal_vector, timestamp
                FROM shadow_genome 
                WHERE remediation_status = 'UNRESOLVED'
            """
            params = []
            
            if failure_mode:
                query += " AND failure_mode = ?"
                params.append(failure_mode)
            
            query += " ORDER BY timestamp DESC LIMIT 50"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                context = json.loads(row["context"])
                if context.get("fitness_score", 0) >= min_fitness:
                    results.append({
                        "genome_id": row["genome_id"],
                        "content_preview": row["input_vector"][:200] + "...",
                        "failure_mode": row["failure_mode"],
                        "fitness_score": context.get("fitness_score", 0),
                        "task": context.get("task", "Unknown"),
                        "timestamp": row["timestamp"]
                    })
            
            return results


def run_bootstrap_demo():
    """Demonstrate the evolutionary bootstrapping system."""
    print("\n" + "="*70)
    print("QoreLogic EVOLUTIONARY BOOTSTRAPPING DEMO")
    print("="*70)
    
    bootstrapper = EvolutionaryBootstrapper()
    
    # Create a generation with multiple variant solutions
    task = "Implement a user authentication function"
    file_path = "auth/login.py"
    
    generation = bootstrapper.create_generation(task, file_path)
    
    # Variant 1: Basic but has hardcoded secret (bad)
    generation.add_variant(
        content='''
def authenticate(username, password):
    secret_key = "sk_live_12345abcdef67890"
    # Bad: hardcoded secret
    return check_credentials(username, password, secret_key)
''',
        source="scrivener",
        metadata={"attempt": 1}
    )
    
    # Variant 2: Uses env var but has SQL injection (medium)
    generation.add_variant(
        content='''
def authenticate(username, password):
    key = os.getenv("AUTH_KEY")
    user = db.execute(f"SELECT * FROM users WHERE name = {username}")
    return verify(user, password)
''',
        source="scrivener",
        metadata={"attempt": 2}
    )
    
    # Variant 3: Clean implementation (good)
    generation.add_variant(
        content='''
def authenticate(username: str, password: str) -> bool:
    """Authenticate a user with secure practices."""
    key = os.getenv("AUTH_KEY")
    user = db.execute("SELECT * FROM users WHERE name = ?", (username,))
    if not user:
        return False
    return bcrypt.checkpw(password.encode(), user.password_hash)
''',
        source="scrivener",
        metadata={"attempt": 3}
    )
    
    print(f"\n📋 Task: {task}")
    print(f"📁 File: {file_path}")
    print(f"🧬 Variants submitted: {len(generation.variants)}")
    
    # Evaluate and select
    print("\n🔬 Evaluating variants...")
    best = bootstrapper.evaluate_generation(generation)
    
    # Display results
    print("\n" + "-"*70)
    print("EVALUATION RESULTS")
    print("-"*70)
    
    for variant in generation.variants:
        status_icon = {
            VariantStatus.SELECTED: "✅",
            VariantStatus.ARCHIVED: "📦",
            VariantStatus.REJECTED: "❌"
        }.get(variant.status, "❓")
        
        print(f"\n{status_icon} {variant.variant_id}")
        print(f"   Fitness: {variant.fitness_score}")
        print(f"   Verdict: {variant.audit_result.verdict}")
        print(f"   Status: {variant.status.value}")
        if variant.audit_result.failure_modes:
            print(f"   Issues: {variant.audit_result.failure_modes}")
    
    print("\n" + "-"*70)
    print(f"🏆 SELECTED: {best.variant_id} (Fitness: {best.fitness_score})")
    print("-"*70)
    
    # Query Shadow Genome
    print("\n📦 Shadow Genome Contents:")
    archived = bootstrapper.query_shadow_genome()
    for item in archived[:3]:
        print(f"   - {item['genome_id']}: {item['failure_mode']} (fitness: {item['fitness_score']})")
    
    print("\n✨ Bootstrapping cycle complete. Non-optimal variants archived for potential recall.")


if __name__ == "__main__":
    run_bootstrap_demo()
