"""
Traffic Control System (Phase 8.5)
Implements Backpressure and Queue Management per Spec §2.5.1.
"""
from threading import Lock
import time
from typing import Optional
from contextlib import contextmanager

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
