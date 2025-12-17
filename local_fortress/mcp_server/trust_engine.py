"""
Trust Dynamics Engine (Phase 8.5)
Implements context-based trust decay, EWMA updates, and transitive trust logic.

Research: RiskMetrics [TRUST-004], EigenTrust [TRUST-001]
Spec: §5.3.3, §5.3.5
"""
import time
from enum import Enum, auto
from typing import List, Optional

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

class TrustEngine:
    def get_lambda(self, context: TrustContext) -> float:
        """
        Returns decay factor λ based on context risk.
        Research: RiskMetrics [TRUST-004] - λ=0.94 applies to high volatility contexts.
        """
        if context == TrustContext.HIGH_RISK:
            return LAMBDA_HIGH_RISK
        return LAMBDA_LOW_RISK

    def calculate_ewma_update(self, current_score: float, outcome_score: float, context: TrustContext) -> float:
        """
        Calculates new trust score using EWMA (Exponentially Weighted Moving Average).
        Formula: T(t) = λ * T(t-1) + (1-λ) * Outcome
        
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

    def calculate_temporal_decay(self, current_score: float, last_update_ts: float, baseline: float = 0.4) -> float:
        """
        Applies temporal decay for inactivity.
        Spec §5.3.4: Drift toward baseline by 1 unit per 30 days (normalized).
        
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
    
    # --- A2: Transitive Trust Stubs (for Phase 8.5 Track A integration) ---
    
    def calculate_transitive_trust(self, trust_path: List[float]) -> float:
        """
        Calculates transitive trust through a chain of intermediaries.
        Spec §5.3.5: Trust(A->C) = Trust(A->B) * Trust(B->C) * δ
        
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
