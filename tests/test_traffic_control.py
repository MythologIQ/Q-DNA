import unittest
from local_fortress.mcp_server.traffic_control import BackpressureMonitor

class TestBackpressure(unittest.TestCase):
    def test_limit_enforcement(self):
        # Create monitor with capacity 1
        monitor = BackpressureMonitor(capacity=1)
        
        # 1. First request succeeds
        with monitor.request_access():
            # Check utilisation
            self.assertEqual(monitor.utilization, 1.0)
            self.assertEqual(monitor.get_status()["status"], "OVERLOAD")
            
            # 2. Second request fails (Backpressure)
            try:
                with monitor.request_access():
                    self.fail("Should have raised RuntimeError (503)")
            except RuntimeError as e:
                self.assertIn("503", str(e))
                self.assertIn("Backpressure limit reached", str(e))
                
        # 3. After exit, queue is free
        self.assertEqual(monitor.utilization, 0.0)
        
        # 4. Should succeed again
        with monitor.request_access():
            pass

    def test_status_flags(self):
        monitor = BackpressureMonitor(capacity=10)
        self.assertEqual(monitor.get_status()["status"], "OK")
        
        # Simulate 80% load
        monitor._active_requests = 8
        self.assertEqual(monitor.get_status()["status"], "WARNING")
        
        monitor._active_requests = 10
        self.assertEqual(monitor.get_status()["status"], "OVERLOAD")

if __name__ == '__main__':
    unittest.main()
