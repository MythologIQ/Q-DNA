"""
Semantic Drift Monitor (Phase 9)
Tracks concept embedding shifts to detect hallucination or personality drift.

Research: Semantic Drift Detection [ML-001]
Spec: §7.1

[L3] Requires embedding model inference.
"""
import numpy as np
import sqlite3
import json
import pickle
import logging
from typing import Optional, Tuple, List, Dict
from datetime import datetime

try:
    from sentence_transformers import SentenceTransformer
    MODEL_AVAILABLE = True
except ImportError:
    MODEL_AVAILABLE = False

# Configuration
DRIFT_THRESHOLD = 0.85  # Spec §7.1
BASELINE_ALPHA = 0.1    # Update rate for baseline (10% new, 90% history)
MODEL_NAME = 'all-MiniLM-L6-v2'

class SemanticDriftMonitor:
    """
    Monitors semantic drift using sentence embeddings.
    """
    
    _model = None
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)

    @classmethod
    def get_model(cls):
        """Lazy load the embedding model."""
        if not MODEL_AVAILABLE:
            return None
            
        if cls._model is None:
            # This might download the model on first run (~80MB)
            try:
                cls._model = SentenceTransformer(MODEL_NAME)
            except Exception as e:
                logging.error(f"Failed to load model {MODEL_NAME}: {e}")
                return None
        return cls._model

    def compute_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for text."""
        model = self.get_model()
        if model is None:
            return None
        
        try:
            # model.encode returns numpy array by default
            return model.encode(text)
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {e}")
            return None

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return np.dot(a, b) / (norm_a * norm_b)

    def get_baseline(self, agent_did: str) -> Optional[np.ndarray]:
        """Retrieve baseline embedding for an agent."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT baseline_embedding FROM semantic_baselines WHERE agent_did = ?",
                    (agent_did,)
                )
                row = cursor.fetchone()
                if row and row[0]:
                    return pickle.loads(row[0])
        except Exception as e:
            self.logger.error(f"Error reading baseline for {agent_did}: {e}")
        return None

    def update_baseline(self, agent_did: str, current_embedding: np.ndarray):
        """Update the baseline embedding using EWMA."""
        baseline = self.get_baseline(agent_did)
        
        if baseline is None:
            new_baseline = current_embedding
            sample_count = 1
        else:
            # EWMA update: B_new = (1-alpha) * B_old + alpha * Current
            # If we want to accept DRIFT over time (personality evolution), we do this.
            # If we want to detect deviation from a FIXED core, we wouldn't update often.
            # Spec §5.3.3 mentions EWMA for Trust, let's apply similar logic here for concept drift 
            # to allow "organic evolution" but flag "sudden jumps".
            new_baseline = (1 - BASELINE_ALPHA) * baseline + BASELINE_ALPHA * current_embedding
            
            # Need to re-normalize? Cosine similarity checks angle, magnitude doesn't matter much 
            # but usually embeddings are normalized.
            sample_count = 1 # Just increment (logic below)

        serialized = pickle.dumps(new_baseline)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO semantic_baselines (agent_did, baseline_embedding, sample_count, last_updated)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(agent_did) DO UPDATE SET
                        baseline_embedding = excluded.baseline_embedding,
                        sample_count = semantic_baselines.sample_count + 1,
                        last_updated = CURRENT_TIMESTAMP
                    """,
                    (agent_did, serialized)
                )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error updating baseline for {agent_did}: {e}")

    def check_drift(self, agent_did: str, content: str) -> Tuple[bool, float, str]:
        """
        Check if content drifts from agent's baseline.
        
        Returns:
            (has_drift, similarity_score, message)
        """
        if not MODEL_AVAILABLE:
            return False, 1.0, "Model unavailable"

        embedding = self.compute_embedding(content)
        if embedding is None:
            return False, 0.0, "Embedding failed"
            
        baseline = self.get_baseline(agent_did)
        
        if baseline is None:
            # First observation, set baseline
            self.update_baseline(agent_did, embedding)
            return False, 1.0, "Baseline initialized"
            
        similarity = self.cosine_similarity(baseline, embedding)
        
        has_drift = similarity < DRIFT_THRESHOLD
        
        # Update baseline only if NO drift (don't learn from bad data)??
        # Or update slowly?
        # Usually, if it's a hallucination (drift), we DON'T want to update baseline to include it.
        if not has_drift:
            self.update_baseline(agent_did, embedding)
            msg = f"Similarity {similarity:.3f} >= {DRIFT_THRESHOLD}"
        else:
            msg = f"DRIFT DETECTED: Similarity {similarity:.3f} < {DRIFT_THRESHOLD}"
            
        return has_drift, similarity, msg
