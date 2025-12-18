"""
Trust Dynamics Engine (Phase 8.5)
Implements context-based trust decay, EWMA updates, and transitive trust logic.

Research: RiskMetrics [TRUST-004], EigenTrust [TRUST-001]
Spec: §5.3.3, §5.3.5

[L3] Design by Contract: All critical functions protected with formal contracts
Research: deal library documentation, Z3 solver integration
"""
import time
from enum import Enum, auto
from typing import List, Optional
import deal

# Lambda Decay Parameters (Spec §5.3.3)
LAMBDA_HIGH_RISK = 0.94  # Reactive: ~95% weight on last 60 observations
LAMBDA_LOW_RISK = 0.97   # Stable: Tolerates minor variance

# Transitive Trust Parameters (Spec §5.3.5)
DAMPING_FACTOR = 0.5
MAX_HOPS = 3

class TrustContext(Enum):
    """Context for risk-based decay parameters."""
    LOW_RISK = auto()   # L1/L2 Tasks (Docs, Routine Code)
    HIGH_RISK = auto()  # L3 Tasks (Security, Crypto, PII)

class TrustStage(Enum):
    """
    Lewicki-Bunker Trust Stages (Spec §5.3.6).
    Research: [TRUST-002]
    """
    CBT = auto() # Calculus-Based (0.0 - 0.5): Probationary
    KBT = auto() # Knowledge-Based (0.5 - 0.8): Standard
    IBT = auto() # Identification-Based (> 0.8): Trusted

class MicroPenaltyType(Enum):
    """
    Micro-Penalty definitions (Spec §9.1).
    Values are absolute deductions on 0.0-1.0 scale.
    """
    SCHEMA_VIOLATION = 0.005  # 0.5%
    API_MISUSE = 0.005        # 0.5%
    STALE_CITATION = 0.010    # 1.0%

# Constants
DAILY_PENALTY_CAP = 0.020 # Max 2% penalty per day
COOLING_OFF_HONEST = 24 * 3600
COOLING_OFF_MALICIOUS = 48 * 3600
PROBATION_VERIFICATIONS = 5
PROBATION_DURATION = 30 * 24 * 3600
PROBATION_FLOOR_SCI = 0.35 # Normalized 35/100

class TrustEngine:
    @deal.post(lambda result: 0.0 < result <= 1.0)
    @deal.post(lambda result: result in [LAMBDA_HIGH_RISK, LAMBDA_LOW_RISK])
    def get_lambda(self, context: TrustContext) -> float:
        """
        Returns decay factor λ based on context risk.
        Research: RiskMetrics [TRUST-004] - λ=0.94 applies to high volatility contexts.

        Contracts:
        - POST: Result must be between 0.0 and 1.0 (exclusive lower, inclusive upper)
        - POST: Result must be one of the defined lambda values
        """
        if context == TrustContext.HIGH_RISK:
            return LAMBDA_HIGH_RISK
        return LAMBDA_LOW_RISK

    @deal.pre(lambda _self, current_score, **kwargs: 0.0 <= current_score <= 1.0)
    @deal.pre(lambda _self, outcome_score, **kwargs: 0.0 <= outcome_score <= 1.0)
    @deal.post(lambda result: 0.0 <= result <= 1.0)
    def calculate_ewma_update(self, current_score: float, outcome_score: float, context: TrustContext) -> float:
        """
        Calculates new trust score using EWMA (Exponentially Weighted Moving Average).
        Formula: T(t) = λ * T(t-1) + (1-λ) * Outcome

        Contracts:
        - PRE: current_score must be in [0.0, 1.0]
        - PRE: outcome_score must be in [0.0, 1.0]
        - POST: Result must be in [0.0, 1.0]

        Args:
            current_score: Current trust metric (float)
            outcome_score: Score of the new event (float)
                           e.g., PASS=1.0, FAIL=0.0
            context: Risk context for selecting lambda

        Returns:
            Updated trust score (float)
        """
        lam = self.get_lambda(context)
        # EWMA Formula: New = Old * Lambda + New * (1 - Lambda)
        new_score = (lam * current_score) + ((1 - lam) * outcome_score)
        return new_score

    @deal.pre(lambda _self, current_score, **kwargs: 0.0 <= current_score <= 1.0)
    @deal.pre(lambda _self, last_update_ts, **kwargs: last_update_ts >= 0)
    @deal.pre(lambda _self, baseline=0.4, **kwargs: 0.0 <= baseline <= 1.0)
    @deal.post(lambda result: 0.0 <= result <= 1.0)
    def calculate_temporal_decay(self, current_score: float, last_update_ts: float, baseline: float = 0.4) -> float:
        """
        Applies temporal decay for inactivity.
        Spec §5.3.4: Drift toward baseline by 1 unit per 30 days (normalized).

        Contracts:
        - PRE: current_score must be in [0.0, 1.0]
        - PRE: last_update_ts must be non-negative
        - PRE: baseline must be in [0.0, 1.0]
        - POST: Result must be in [0.0, 1.0]

        Args:
            current_score: Current trust score
            last_update_ts: Unix timestamp of last update
            baseline: Target baseline score (default 0.4 for T4/Neutral)

        Returns:
            Decayed score
        """
        now = time.time()
        if last_update_ts > now:
            return current_score # Guard against future timestamps

        days_inactive = (now - last_update_ts) / (24 * 3600)

        if days_inactive <= 0:
            return current_score

        # Rate: 1% drift per 30 days (assuming 0-1 scale) ??
        # Spec says "1 point per 30 days" (on 0-100 scale).
        # On 0.0-1.0 scale, this is 0.01 per 30 days.
        decay_amount = (days_inactive / 30.0) * 0.01

        if current_score > baseline:
            return max(baseline, current_score - decay_amount)
        elif current_score < baseline:
            return min(baseline, current_score + decay_amount)

        return current_score

    
    # --- A3: Lewicki-Bunker Stages (Spec §5.3.6) ---
    
    def get_trust_stage(self, score: float) -> TrustStage:
        """
        Maps numerical trust score to behavioral stage.
        Spec §5.3.6: CBT(0-0.5), KBT(0.5-0.8), IBT(>0.8).
        """
        if score > 0.8:
            return TrustStage.IBT
        elif score > 0.5:
            return TrustStage.KBT
        return TrustStage.CBT

    def calculate_violation_penalty(self, current_score: float) -> float:
        """
        Calculates new score after a violation, enforcing strict stage demotion.
        Spec §5.3.6: "Any trust violation demotes by at least one stage."
        
        Logic:
        - IBT -> Drop to KBT range (max 0.8)
        - KBT -> Drop to CBT range (max 0.5)
        - CBT -> Standard penalty (or severe drop if needed)
        """
        current_stage = self.get_trust_stage(current_score)
        target_score = current_score
        
        # Determine ceiling of the NEXT LOWER stage
        if current_stage == TrustStage.IBT:
            # Demote to KBT: Ceiling is 0.8.
            target_score = 0.8
        elif current_stage == TrustStage.KBT:
            # Demote to CBT: Ceiling is 0.5.
            target_score = 0.5
        elif current_stage == TrustStage.CBT:
            # Already at bottom stage. Apply massive penalty to reset probation?
            # Or just let normal EWMA handle it (which will be a drop).
            # Spec implies demotion, but you can't demote below bottom.
            pass
            
        # Ensure the score is definitely lowered from current if it was at boundary
        if target_score >= current_score:
            # This happens if we were exactly 0.8 or 0.5 or in CBT.
            # Apply a fallback drop (e.g. -0.1) to ensure penalty is felt.
            target_score = max(0.0, current_score - 0.1)
            
        return target_score



    # --- A4: Micro-Penalties (Spec §9.1) ---

    @deal.pre(lambda _self, current_score, **kwargs: 0.0 <= current_score <= 1.0)
    @deal.pre(lambda _self, daily_penalty_sum, **kwargs: 0.0 <= daily_penalty_sum <= DAILY_PENALTY_CAP)
    @deal.post(lambda result: 0.0 <= result[0] <= 1.0)  # new_score
    @deal.post(lambda result: 0.0 <= result[1] <= DAILY_PENALTY_CAP)  # applied_penalty
    def calculate_micro_penalty(self, current_score: float, penalty_type: MicroPenaltyType, daily_penalty_sum: float) -> tuple[float, float]:
        """
        Applies micro-penalty with daily cap.

        Contracts:
        - PRE: current_score must be in [0.0, 1.0]
        - PRE: daily_penalty_sum must be in [0.0, DAILY_PENALTY_CAP]
        - POST: new_score must be in [0.0, 1.0]
        - POST: applied_penalty must be in [0.0, DAILY_PENALTY_CAP]

        Returns (new_score, applied_penalty).
        """
        base_penalty = penalty_type.value

        # Check remaining cap
        remaining_cap = max(0.0, DAILY_PENALTY_CAP - daily_penalty_sum)
        applied_penalty = min(base_penalty, remaining_cap)

        # Apply to score
        new_score = max(0.0, current_score - applied_penalty)
        return new_score, applied_penalty

    # --- A5: Cooling-Off Periods (Spec §9.2) ---

    def get_cooling_off_duration(self, is_malicious: bool) -> float:
        """Returns cooling-off duration in seconds."""
        return COOLING_OFF_MALICIOUS if is_malicious else COOLING_OFF_HONEST

    # --- A6: Probation Logic (Spec §5.3.2) ---

    def is_in_probation(self, created_at: float, verification_count: int) -> bool:
        """
        Checks if entity is in probation.
        Spec §5.3.2: Probation expires after 5 verifications OR 30 days.
        """
        now = time.time()
        age = now - created_at
        
        # If EITHER condition is met, probation ends.
        if verification_count >= PROBATION_VERIFICATIONS:
            return False
        if age >= PROBATION_DURATION:
            return False
            
        return True

    def get_probation_floor(self) -> float:
        return PROBATION_FLOOR_SCI

    # --- A2: Transitive Trust Stubs (for Phase 8.5 Track A integration) ---
    
    @deal.pre(lambda _self, trust_path: all(0.0 <= score <= 1.0 for score in trust_path))
    @deal.pre(lambda _self, trust_path: len(trust_path) <= MAX_HOPS)
    @deal.post(lambda result: 0.0 <= result <= 1.0)
    def calculate_transitive_trust(self, trust_path: List[float]) -> float:
        """
        Calculates transitive trust through a chain of intermediaries.
        Spec §5.3.5: Trust(A->C) = Trust(A->B) * Trust(B->C) * δ

        Contracts:
        - PRE: All trust scores in path must be in [0.0, 1.0]
        - PRE: Path length must not exceed MAX_HOPS (3)
        - POST: Result must be in [0.0, 1.0]

        Args:
            trust_path: List of trust scores (0.0-1.0) along the path.
                        e.g., [Trust(A->B), Trust(B->C)]

        Returns:
            Derived trust score (0.0-1.0)
        """
        if not trust_path:
            return 0.0

        if len(trust_path) > MAX_HOPS:
            return 0.0  # Trust evaporates beyond max hops

        # Start with the first link
        trust = trust_path[0]

        # Multiply by subsequent links and damping factor
        for next_link in trust_path[1:]:
            trust = trust * next_link * DAMPING_FACTOR

        return trust
