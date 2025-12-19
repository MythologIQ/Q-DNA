"""
QoreLogic Telemetry Manager
Provides centralized SLI/SLO tracking and user feedback persistence.
"""

import time
import sqlite3
import psutil
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from contextlib import contextmanager

@dataclass
class FeedbackEntry:
    event_id: str
    rating: int  # 1-5
    comments: str
    agent_did: str
    timestamp: float

class TelemetryManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        
        # In-memory metrics (Transient)
        self.metrics = {
            "audit_latency_ms": [],  # Histogram samples
            "cpu_usage_pct": 0.0,    # Gauge
            "memory_usage_mb": 0.0,  # Gauge
            "trust_updates": 0,      # Counter
            "audit_count_total": 0,  # Counter
            "audit_count_fail": 0,   # Counter
        }
        self.last_cpu_check = 0

    @contextmanager
    def _get_db(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize feedback storage table."""
        with self._get_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    event_id TEXT,
                    rating INTEGER,
                    comments TEXT,
                    agent_did TEXT,
                    context TEXT
                )
            """)
            conn.commit()

    def record_latency(self, latency_ms: float):
        """Record an audit latency sample (SLI)."""
        self.metrics["audit_latency_ms"].append(latency_ms)
        # Keep only last 1000 samples to prevent memory leak
        if len(self.metrics["audit_latency_ms"]) > 1000:
            self.metrics["audit_latency_ms"].pop(0)

    def update_system_gauges(self):
        """Update system resource gauges (CPU/Mem)."""
        now = time.time()
        # Rate limit psutil calls to 1s
        if now - self.last_cpu_check > 1.0:
            self.metrics["cpu_usage_pct"] = psutil.cpu_percent(interval=None)
            self.metrics["memory_usage_mb"] = psutil.Process().memory_info().rss / (1024 * 1024)
            self.last_cpu_check = now

    def increment_counter(self, metric_name: str):
        """Increment a standard counter."""
        if metric_name in self.metrics:
            self.metrics[metric_name] += 1

    def submit_feedback(self, event_id: str, rating: int, comments: str, agent_did: str = "did:myth:user:human") -> int:
        """Persist user feedback for a specific event (e.g. audit result)."""
        with self._get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO feedback_log (timestamp, event_id, rating, comments, agent_did)
                VALUES (?, ?, ?, ?, ?)
            """, (time.time(), event_id, rating, comments, agent_did))
            conn.commit()
            return cursor.lastrowid

    def get_metrics_snapshot(self) -> Dict:
        """Get current SLIs for dashboarding."""
        self.update_system_gauges()
        
        latencies = self.metrics["audit_latency_ms"]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
        
        return {
            "status": "HEALTHY" if self.metrics["cpu_usage_pct"] < 70 else "SATURATED",
            "gauges": {
                "cpu_pct": self.metrics["cpu_usage_pct"],
                "memory_mb": self.metrics["memory_usage_mb"]
            },
            "sli": {
                "latency_avg_ms": round(avg_latency, 2),
                "latency_p95_ms": round(p95_latency, 2),
                "error_rate_pct": round((self.metrics["audit_count_fail"] / max(1, self.metrics["audit_count_total"])) * 100, 2)
            },
            "counters": {
                "audits": self.metrics["audit_count_total"],
                "trust_events": self.metrics["trust_updates"]
            }
        }
