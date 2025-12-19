"""
Trust Management Integration (Track INT - Phase 8.5)
Bridges TrustEngine calculations with AgentRegistry persistence.

Research: Trust Dynamics [TRUST-001], RiskMetrics [TRUST-004]
Spec: §5.3 (Trust Dynamics)

[L3] Critical security component - manages agent trust scores and history
"""
import sqlite3
import time
from typing import Optional, Dict, Any, List
from datetime import date
import logging

from .trust_engine import (
    TrustEngine,
    TrustContext,
    TrustStage,
    MicroPenaltyType
)


class TrustManager:
    """
    Manages trust score persistence and updates for agents.
    Integrates TrustEngine calculations with the agent_registry database.
    """

    def __init__(self, db_path: str):
        """
        Initialize trust manager.

        Args:
            db_path: Path to SOA ledger database
        """
        self.db_path = db_path
        self.engine = TrustEngine()
        self.logger = logging.getLogger(__name__)

    def get_agent_trust(self, agent_did: str) -> Optional[float]:
        """
        Get current trust score for an agent.

        Args:
            agent_did: Agent DID

        Returns:
            Trust score (0.0-1.0) or None if agent not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT trust_score FROM agent_registry WHERE did = ?",
                    (agent_did,)
                )
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            self.logger.error(f"Error reading trust score for {agent_did}: {e}")
            return None

    def update_trust_ewma(
        self,
        agent_did: str,
        outcome_score: float,
        context: TrustContext,
        ledger_ref_id: Optional[int] = None
    ) -> bool:
        """
        Update agent trust score using EWMA formula.

        Args:
            agent_did: Agent DID
            outcome_score: Score of the verification event (0.0=FAIL, 1.0=PASS)
            context: Risk context (LOW_RISK or HIGH_RISK)
            ledger_ref_id: Reference to triggering SOA ledger entry

        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get current trust score
                cursor = conn.execute(
                    """
                    SELECT trust_score, verification_count, created_at
                    FROM agent_registry
                    WHERE did = ?
                    """,
                    (agent_did,)
                )
                row = cursor.fetchone()
                if not row:
                    self.logger.error(f"Agent {agent_did} not found")
                    return False

                current_score, verification_count, created_at = row
                created_timestamp = self._parse_timestamp(created_at)

                # Check if in probation
                in_probation = self.engine.is_in_probation(created_timestamp, verification_count)

                # Calculate new score using EWMA
                new_score = self.engine.calculate_ewma_update(
                    current_score,
                    outcome_score,
                    context
                )

                # Apply probation floor if needed
                if in_probation:
                    probation_floor = self.engine.get_probation_floor()
                    new_score = max(new_score, probation_floor)

                # Update agent_registry
                new_stage = self.engine.get_trust_stage(new_score).name
                conn.execute(
                    """
                    UPDATE agent_registry
                    SET trust_score = ?,
                        trust_stage = ?,
                        last_trust_update = CURRENT_TIMESTAMP,
                        verification_count = verification_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE did = ?
                    """,
                    (new_score, new_stage, agent_did)
                )

                # Record in trust_updates history
                conn.execute(
                    """
                    INSERT INTO trust_updates (
                        agent_did, old_score, new_score, delta,
                        update_type, context, ledger_ref_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        agent_did,
                        current_score,
                        new_score,
                        new_score - current_score,
                        'EWMA_UPDATE',
                        f"{context.name} (outcome={outcome_score})",
                        ledger_ref_id
                    )
                )

                conn.commit()

                self.logger.info(
                    f"Trust updated for {agent_did}: {current_score:.3f} → {new_score:.3f} "
                    f"(Δ={new_score - current_score:+.3f}, context={context.name})"
                )

                return True

        except Exception as e:
            self.logger.error(f"Error updating trust for {agent_did}: {e}", exc_info=True)
            return False

    def apply_micro_penalty(
        self,
        agent_did: str,
        penalty_type: MicroPenaltyType,
        reason: str,
        ledger_ref_id: Optional[int] = None
    ) -> bool:
        """
        Apply micro-penalty to agent trust score.

        Args:
            agent_did: Agent DID
            penalty_type: Type of micro-penalty
            reason: Reason for penalty
            ledger_ref_id: Reference to triggering SOA ledger entry

        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get current state
                cursor = conn.execute(
                    """
                    SELECT trust_score, daily_penalty_sum, penalty_reset_date
                    FROM agent_registry
                    WHERE did = ?
                    """,
                    (agent_did,)
                )
                row = cursor.fetchone()
                if not row:
                    self.logger.error(f"Agent {agent_did} not found")
                    return False

                current_score, daily_penalty_sum, penalty_reset_date = row

                # Reset daily penalty sum if new day
                today = date.today()
                reset_date = date.fromisoformat(penalty_reset_date) if penalty_reset_date else today

                if reset_date < today:
                    daily_penalty_sum = 0.0

                # Calculate penalty
                new_score, applied_penalty = self.engine.calculate_micro_penalty(
                    current_score,
                    penalty_type,
                    daily_penalty_sum
                )

                # Update agent_registry
                new_stage = self.engine.get_trust_stage(new_score).name
                conn.execute(
                    """
                    UPDATE agent_registry
                    SET trust_score = ?,
                        trust_stage = ?,
                        daily_penalty_sum = ?,
                        penalty_reset_date = ?,
                        last_trust_update = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE did = ?
                    """,
                    (
                        new_score,
                        new_stage,
                        daily_penalty_sum + applied_penalty,
                        today.isoformat(),
                        agent_did
                    )
                )

                # Record in trust_updates history
                conn.execute(
                    """
                    INSERT INTO trust_updates (
                        agent_did, old_score, new_score, delta,
                        update_type, context, ledger_ref_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        agent_did,
                        current_score,
                        new_score,
                        new_score - current_score,
                        'MICRO_PENALTY',
                        f"{penalty_type.name}: {reason}",
                        ledger_ref_id
                    )
                )

                conn.commit()

                self.logger.warning(
                    f"Micro-penalty applied to {agent_did}: {current_score:.3f} → {new_score:.3f} "
                    f"(-{applied_penalty:.3f}, type={penalty_type.name}, daily_sum={daily_penalty_sum + applied_penalty:.3f})"
                )

                return True

        except Exception as e:
            self.logger.error(f"Error applying micro-penalty to {agent_did}: {e}", exc_info=True)
            return False

    def apply_temporal_decay(self, agent_did: str, baseline: float = 0.4) -> bool:
        """
        Apply temporal decay for inactivity.

        Args:
            agent_did: Agent DID
            baseline: Target baseline score (default 0.4 for T4/Neutral)

        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT trust_score, last_trust_update
                    FROM agent_registry
                    WHERE did = ?
                    """,
                    (agent_did,)
                )
                row = cursor.fetchone()
                if not row:
                    return False

                current_score, last_update = row
                last_update_ts = self._parse_timestamp(last_update)

                # Calculate decayed score
                new_score = self.engine.calculate_temporal_decay(
                    current_score,
                    last_update_ts,
                    baseline
                )

                # Only update if score changed
                if abs(new_score - current_score) < 0.0001:
                    return True

                # Update agent_registry
                new_stage = self.engine.get_trust_stage(new_score).name
                conn.execute(
                    """
                    UPDATE agent_registry
                    SET trust_score = ?,
                        trust_stage = ?,
                        last_trust_update = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE did = ?
                    """,
                    (new_score, new_stage, agent_did)
                )

                # Record in trust_updates history
                conn.execute(
                    """
                    INSERT INTO trust_updates (
                        agent_did, old_score, new_score, delta,
                        update_type, context, ledger_ref_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        agent_did,
                        current_score,
                        new_score,
                        new_score - current_score,
                        'TEMPORAL_DECAY',
                        f"Inactivity drift toward baseline ({baseline})",
                        None
                    )
                )

                conn.commit()

                return True

        except Exception as e:
            self.logger.error(f"Error applying temporal decay to {agent_did}: {e}", exc_info=True)
            return False

    def get_trust_stage(self, agent_did: str) -> Optional[TrustStage]:
        """
        Get Lewicki-Bunker trust stage for an agent.

        Args:
            agent_did: Agent DID

        Returns:
            TrustStage or None if agent not found
        """
        score = self.get_agent_trust(agent_did)
        if score is None:
            return None
        return self.engine.get_trust_stage(score)

    def get_trust_history(
        self,
        agent_did: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get trust update history for an agent.

        Args:
            agent_did: Agent DID
            limit: Maximum number of records to return

        Returns:
            List of trust update records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT *
                    FROM trust_updates
                    WHERE agent_did = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (agent_did, limit)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error reading trust history for {agent_did}: {e}")
            return []

    def apply_violation_penalty(
        self,
        agent_did: str,
        reason: str,
        is_malicious: bool = False,
        ledger_ref_id: Optional[int] = None
    ) -> bool:
        """
        Apply major violation penalty and stage demotion.
        
        Args:
            agent_did: Agent DID
            reason: Violation reason
            is_malicious: True if violation implies potential intent (triggers longer cooling off)
            ledger_ref_id: SOA ledger reference
            
        Returns:
            True if successful
        """
        from datetime import datetime, timedelta
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get current state
                cursor = conn.execute(
                    "SELECT trust_score FROM agent_registry WHERE did = ?",
                    (agent_did,)
                )
                row = cursor.fetchone()
                if not row:
                    self.logger.error(f"Agent {agent_did} not found")
                    return False
                
                current_score = row[0]
                
                # Calculate new score via TrustEngine (handles stage demotion)
                new_score = self.engine.calculate_violation_penalty(current_score)
                
                # Determine cooling off
                cooling_off_seconds = self.engine.get_cooling_off_duration(is_malicious)
                now = datetime.now()
                end_time = now + timedelta(seconds=cooling_off_seconds)
                
                # Update trust_score and set status to QUARANTINED
                new_stage = self.engine.get_trust_stage(new_score).name
                conn.execute(
                    """
                    UPDATE agent_registry
                    SET trust_score = ?,
                        trust_stage = ?,
                        status = 'QUARANTINED',
                        last_trust_update = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE did = ?
                    """,
                    (new_score, new_stage, agent_did)
                )
                
                # Insert into agent_quarantine
                conn.execute(
                    """
                    INSERT INTO agent_quarantine 
                    (agent_did, start_time, end_time, reason, active)
                    VALUES (?, CURRENT_TIMESTAMP, ?, ?, 1)
                    """,
                    (agent_did, end_time, reason)
                )
                
                # Log VIOLATION_PENALTY
                conn.execute(
                    """
                    INSERT INTO trust_updates (
                        agent_did, old_score, new_score, delta,
                        update_type, context, ledger_ref_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        agent_did, current_score, new_score, new_score - current_score,
                        'VIOLATION_PENALTY', reason, ledger_ref_id
                    )
                )
                
                # Log COOLING_OFF_START
                conn.execute(
                    """
                    INSERT INTO trust_updates (
                        agent_did, old_score, new_score, delta,
                        update_type, context, ledger_ref_id
                    ) VALUES (?, ?, ?, ?, 'COOLING_OFF_START', ?, ?)
                    """,
                    (
                        agent_did, new_score, new_score, 0.0,
                        f"Duration: {cooling_off_seconds}s (Malicious={is_malicious})",
                        ledger_ref_id
                    )
                )
                
                conn.commit()
                self.logger.warning(
                    f"VIOLATION penalty applied to {agent_did}: {current_score:.3f} -> {new_score:.3f}. "
                    f"Quarantined until {end_time}."
                )
                return True
                
        except Exception as e:
            self.logger.error(f"Error applying violation penalty to {agent_did}: {e}", exc_info=True)
            return False

    def update_influence_weights(self) -> bool:
        """
        Recalculate and update influence weights for all agents based on L1-normalized trust scores.
        This ensures system-wide conservation of influence.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Fetch all active agents and their trust scores
                cursor = conn.execute(
                    "SELECT did, trust_score FROM agent_registry WHERE status = 'ACTIVE'"
                )
                agents = cursor.fetchall()  # List of (did, score)
                
                if not agents:
                    return True
                
                dids = [a[0] for a in agents]
                scores = [a[1] for a in agents]
                
                # Normalize current trust scores (eigenvector approximation)
                normalized_scores = self.engine.normalize_trust_vector(scores)
                
                # --- Phase 10.5: Anchor Damping (Sybil Resistance) ---
                # Create pre-trusted vector based on roles
                cursor = conn.execute(
                    "SELECT did, role FROM agent_registry WHERE status = 'ACTIVE'"
                )
                role_map = {row[0]: row[1] for row in cursor.fetchall()}
                
                anchor_scores = []
                for did in dids:
                    role = role_map.get(did, "")
                    # Anchors: Judge, Overseer, Sentinel (Genesis Agents)
                    if role in ["Judge", "Overseer", "Sentinel"]:
                        anchor_scores.append(1.0)
                    else:
                        anchor_scores.append(0.0) # Scriveners/others trust anchors
                
                # Normalize anchor vector
                normalized_anchors = self.engine.normalize_trust_vector(anchor_scores)
                
                # Apply damping (Teleportation)
                if normalized_anchors: # Only if we have anchors
                    final_weights = self.engine.apply_anchor_damping(
                        normalized_scores, 
                        normalized_anchors,
                        damping_factor=0.85 
                    )
                else:
                    final_weights = normalized_scores
                
                # Update influence_weight for each agent
                for did, weight in zip(dids, final_weights):
                    conn.execute(
                        "UPDATE agent_registry SET influence_weight = ?, updated_at = CURRENT_TIMESTAMP WHERE did = ?",
                        (weight, did)
                    )
                
                conn.commit()
                self.logger.info(f"Updated influence weights for {len(agents)} agents (L1 Norm + Anchor Damping).")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating influence weights: {e}", exc_info=True)
            return False

    def _parse_timestamp(self, ts_str: str) -> float:
        """
        Parse SQLite timestamp to Unix timestamp.

        Args:
            ts_str: Timestamp string from SQLite

        Returns:
            Unix timestamp (float)
        """
        from datetime import datetime

        try:
            # SQLite CURRENT_TIMESTAMP format: "YYYY-MM-DD HH:MM:SS"
            dt = datetime.fromisoformat(ts_str.replace(' ', 'T'))
            return dt.timestamp()
        except Exception:
            # Fallback to current time if parsing fails
            return time.time()


# Global trust manager instance
_trust_manager: Optional[TrustManager] = None


def get_trust_manager(db_path: str) -> TrustManager:
    """Get or create the global trust manager instance."""
    global _trust_manager
    if _trust_manager is None:
        _trust_manager = TrustManager(db_path)
    return _trust_manager
