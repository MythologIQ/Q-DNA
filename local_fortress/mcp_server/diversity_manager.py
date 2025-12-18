"""
Q-DNA Diversity Quorum Manager (Phase 9 - Track P3)
Implements Multi-Model Consensus logic for L3 artifacts.

Research: Diversity Quorum [ML-002]
Spec: §7.2 (Debate and Diversity)

[L3] Logic only - assumes external model providers are connected.
"""
import json
import logging
from typing import Dict, List, Optional
from enum import Enum
import hashlib

class ModelFamily(Enum):
    """Supported model families for diversity."""
    GPT = "GPT"        # OpenAI
    CLAUDE = "CLAUDE"  # Anthropic
    GEMINI = "GEMINI"  # Google
    LLAMA = "LLAMA"    # Meta (Open Weights)
    MISTRAL = "MISTRAL" # Mistral AI

class Verdict(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ABSTAIN = "ABSTAIN"

class DiversityManager:
    """
    Manages consensus gathering from diverse model families.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # In-memory storage for active debates (would be DB in prod)
        self.active_debates: Dict[str, Dict] = {} 

    def start_debate(self, artifact_hash: str, content: str) -> str:
        """Initialize a debate for an L3 artifact."""
        if artifact_hash in self.active_debates:
            return artifact_hash
            
        self.active_debates[artifact_hash] = {
            "content": content,
            "votes": {},  # family -> {verdict, reason, confidence}
            "status": "OPEN",
            "rounds": 0
        }
        return artifact_hash

    def cast_vote(self, artifact_hash: str, family: ModelFamily, verdict: Verdict, reason: str, confidence: float):
        """Record a vote from a specific model family."""
        if artifact_hash not in self.active_debates:
            raise ValueError(f"Debate {artifact_hash} not found")
            
        debate = self.active_debates[artifact_hash]
        
        # One vote per family per round (simplification)
        debate["votes"][family.value] = {
            "verdict": verdict.value,
            "reason": reason,
            "confidence": confidence
        }
        
    def check_quorum(self, artifact_hash: str) -> Dict:
        """
        Check if diversity quorum is met.
        Spec §7.2: L3 requires agreement from >= 2 model families.
        """
        if artifact_hash not in self.active_debates:
            return {"status": "UNKNOWN"}
            
        debate = self.active_debates[artifact_hash]
        votes = debate["votes"]
        
        family_count = len(votes)
        pass_count = sum(1 for v in votes.values() if v["verdict"] == "PASS")
        fail_count = sum(1 for v in votes.values() if v["verdict"] == "FAIL")
        
        # Quorum Rules
        # 1. Minimum 2 families participating
        if family_count < 2:
            return {
                "status": "PENDING",
                "message": f"Insufficient diversity (families={family_count}/2)"
            }
            
        # 2. Consensus Logic (Supermajority > 66% or Unanimous if only 2)
        consensus_threshold = 0.66
        pass_ratio = pass_count / family_count
        
        if pass_ratio > consensus_threshold:
            debate["status"] = "PASSED"
            return {
                "status": "PASSED",
                "ratio": pass_ratio,
                "votes": votes
            }
        elif (fail_count / family_count) > consensus_threshold:
            debate["status"] = "FAILED"
            return {
                "status": "FAILED",
                "ratio": pass_ratio,
                "votes": votes
            }
        else:
            debate["status"] = "DEADLOCK"
            return {
                "status": "DEADLOCK",
                "ratio": pass_ratio,
                "votes": votes,
                "message": "Debate requires tie-breaker or more votes"
            }

    def get_debate_summary(self, artifact_hash: str) -> Dict:
        """Get full summary of a debate."""
        return self.active_debates.get(artifact_hash, {})

# Singleton
_diversity_manager = DiversityManager()

def get_diversity_manager() -> DiversityManager:
    return _diversity_manager
