"""
Traffic Control & Mode Transition System (Track C2 - Phase 8.5)
Implements Backpressure, Queue Management, and Autonomous Mode Switching.

Research: Google SRE Handbook [SRE-001] - Load Shedding and Backpressure
Spec: §2.5.1 (Backpressure), §12 (Operational Modes)

[L2] Implements:
- C2.1: CPU >70% for 5 min → LEAN mode
- C2.2: Queue depth >50 → SURGE mode
- C2.3: Security event → SAFE mode
"""
from threading import Lock, Thread, Event
import time
import psutil
import sqlite3
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from collections import deque
from enum import Enum

class BackpressureMonitor:
    """
    Monitors concurrent request load and enforces backpressure.
    Spec §2.5.1: Queue Bound 50, 80% Warning, Shed at 100%.
    """
    
    def __init__(self, capacity: int = 50):
        self.capacity = capacity
        # Use simple counter + lock for active requests
        # (Since we don't have a real queue object for sync calls, we count concurrency)
        self._active_requests = 0
        self._lock = Lock()
        
    @property
    def utilization(self) -> float:
        with self._lock:
            if self.capacity == 0: return 0.0
            return self._active_requests / self.capacity
            
    @contextmanager
    def request_access(self):
        """
        Context manager for checking backpressure.
        Raises RuntimeError (503) if overloaded.
        """
        with self._lock:
            if self._active_requests >= self.capacity:
                raise RuntimeError("503 Service Unavailable: Backpressure limit reached (Queue Full)")
            
            self._active_requests += 1
            
        try:
            yield
        finally:
            with self._lock:
                self._active_requests -= 1

    def get_status(self) -> dict:
        """Get current traffic status."""
        with self._lock:
            util = self._active_requests / self.capacity if self.capacity > 0 else 0
            
            status = "OK"
            if util >= 1.0:
                status = "OVERLOAD"
            elif util >= 0.8:
                status = "WARNING"
                
            return {
                "active_requests": self._active_requests,
                "capacity": self.capacity,
                "utilization": round(util, 2),
                "status": status
            }

# Singleton instance
_monitor = BackpressureMonitor()

def get_traffic_monitor():
    return _monitor


# ============================================================================
# Track C2: Mode Transition System
# ============================================================================

class OperationalMode(Enum):
    """Operational modes per Spec §12"""
    NORMAL = "NORMAL"   # Standard operation
    LEAN = "LEAN"       # CPU constrained - reduce verification sampling
    SURGE = "SURGE"     # High request volume - optimize throughput
    SAFE = "SAFE"       # Security incident - maximum verification


# Monitoring thresholds (Spec §12)
CPU_THRESHOLD = 70.0          # % CPU usage to trigger LEAN mode
CPU_SAMPLE_WINDOW = 5 * 60    # 5 minutes in seconds
QUEUE_SURGE_THRESHOLD = 50    # Queue depth to trigger SURGE mode
QUEUE_WARNING_THRESHOLD = 40  # 80% of max (50 * 0.8)


class SystemMonitor:
    """
    Monitors system resources and triggers mode transitions.

    Implements the monitoring logic for Track C2:
    - C2.1: CPU >70% for 5 min → LEAN mode
    - C2.2: Queue depth >50 → SURGE mode
    - C2.3: Security event → SAFE mode
    """

    def __init__(self, db_path: str, poll_interval: float = 10.0):
        """
        Initialize system monitor.

        Args:
            db_path: Path to SOA ledger database
            poll_interval: How often to check system resources (seconds)
        """
        self.db_path = db_path
        self.poll_interval = poll_interval
        self.logger = logging.getLogger(__name__)

        # CPU monitoring state
        self.cpu_samples = deque(maxlen=int(CPU_SAMPLE_WINDOW / poll_interval))
        self.last_cpu_check = time.time()

        # Queue monitoring state
        self.current_queue_depth = 0

        # Control flags
        self.stop_event = Event()
        self.monitor_thread: Optional[Thread] = None

    def start_monitoring(self):
        """Start the monitoring thread."""
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.logger.warning("Monitor already running")
            return

        self.stop_event.clear()
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("System monitor started")

    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        self.logger.info("System monitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while not self.stop_event.is_set():
            try:
                # Check CPU
                self._check_cpu()

                # Check queue depth
                self._check_queue_depth()

                # Sleep until next poll
                time.sleep(self.poll_interval)

            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}", exc_info=True)

    def _check_cpu(self):
        """
        Monitor CPU usage and trigger LEAN mode if sustained high usage.
        Spec §12: CPU >70% for 5 minutes → LEAN mode
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1.0)
            self.cpu_samples.append(cpu_percent)

            # Need full window of samples
            if len(self.cpu_samples) < self.cpu_samples.maxlen:
                return

            # Calculate average over window
            avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples)

            current_mode = self._get_current_mode()

            if avg_cpu > CPU_THRESHOLD and current_mode != OperationalMode.LEAN:
                self.logger.warning(
                    f"Sustained high CPU usage: {avg_cpu:.1f}% over {CPU_SAMPLE_WINDOW}s"
                )
                self._trigger_mode_transition(
                    OperationalMode.LEAN,
                    f"CPU usage {avg_cpu:.1f}% > {CPU_THRESHOLD}% for {CPU_SAMPLE_WINDOW}s"
                )

            elif avg_cpu <= CPU_THRESHOLD and current_mode == OperationalMode.LEAN:
                # Return to NORMAL when CPU subsides
                self.logger.info(f"CPU usage normalized: {avg_cpu:.1f}%")
                self._trigger_mode_transition(
                    OperationalMode.NORMAL,
                    f"CPU usage returned to normal: {avg_cpu:.1f}%"
                )

        except Exception as e:
            self.logger.error(f"Error checking CPU: {e}", exc_info=True)

    def _check_queue_depth(self):
        """
        Monitor queue depth and trigger SURGE mode if needed.
        Spec §12: Queue depth >50 → SURGE mode
        """
        try:
            # Get current queue depth from database
            queue_depth = self._get_queue_depth()
            self.current_queue_depth = queue_depth

            current_mode = self._get_current_mode()

            if queue_depth >= QUEUE_SURGE_THRESHOLD and current_mode != OperationalMode.SURGE:
                self.logger.warning(f"High queue depth: {queue_depth} requests pending")
                self._trigger_mode_transition(
                    OperationalMode.SURGE,
                    f"Queue depth {queue_depth} >= {QUEUE_SURGE_THRESHOLD}"
                )

            elif queue_depth < QUEUE_WARNING_THRESHOLD and current_mode == OperationalMode.SURGE:
                # Return to NORMAL when queue drains
                self.logger.info(f"Queue depth normalized: {queue_depth} requests")
                self._trigger_mode_transition(
                    OperationalMode.NORMAL,
                    f"Queue depth returned to normal: {queue_depth}"
                )

        except Exception as e:
            self.logger.error(f"Error checking queue depth: {e}", exc_info=True)

    def trigger_safe_mode(self, reason: str):
        """
        Manually trigger SAFE mode due to security event.
        Spec §12: Security event → SAFE mode

        Args:
            reason: Description of the security event
        """
        self.logger.critical(f"SAFE mode triggered: {reason}")
        self._trigger_mode_transition(OperationalMode.SAFE, reason)

    def _get_current_mode(self) -> OperationalMode:
        """Query current operational mode from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT current_mode FROM system_state WHERE state_id = 1")
                row = cursor.fetchone()
                if row:
                    return OperationalMode(row[0])
                return OperationalMode.NORMAL
        except Exception as e:
            self.logger.error(f"Error reading current mode: {e}")
            return OperationalMode.NORMAL

    def _trigger_mode_transition(self, new_mode: OperationalMode, reason: str):
        """
        Trigger a mode transition.

        Args:
            new_mode: Target operational mode
            reason: Reason for the transition
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Update system_state table
                conn.execute(
                    """
                    UPDATE system_state
                    SET current_mode = ?,
                        mode_changed_at = CURRENT_TIMESTAMP,
                        mode_reason = ?
                    WHERE state_id = 1
                    """,
                    (new_mode.value, reason)
                )
                conn.commit()

            self.logger.info(f"Mode transition: → {new_mode.value} ({reason})")

        except Exception as e:
            self.logger.error(f"Error during mode transition: {e}", exc_info=True)

    def _get_queue_depth(self) -> int:
        """
        Get current queue depth from L3 approval queue.

        Returns:
            Number of pending requests
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM l3_approval_queue WHERE status = 'PENDING'"
                )
                row = cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            self.logger.error(f"Error reading queue depth: {e}")
            return 0

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system monitoring status.

        Returns:
            Dictionary with current metrics
        """
        avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0.0

        return {
            "current_mode": self._get_current_mode().value,
            "cpu_percent_avg": round(avg_cpu, 1),
            "cpu_samples_count": len(self.cpu_samples),
            "queue_depth": self.current_queue_depth,
            "cpu_threshold": CPU_THRESHOLD,
            "queue_threshold": QUEUE_SURGE_THRESHOLD,
            "monitoring_active": self.monitor_thread and self.monitor_thread.is_alive()
        }


# Global system monitor instance
_system_monitor: Optional[SystemMonitor] = None

def get_system_monitor(db_path: str) -> SystemMonitor:
    """Get or create the global system monitor instance."""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor(db_path)
    return _system_monitor
