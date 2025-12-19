from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import json
import urllib.request
import urllib.error

class NetworkConnector(ABC):
    """
    Abstract base class for network interactions.
    """
    
    @abstractmethod
    def connect(self, host: str, port: int) -> bool:
        pass

    @abstractmethod
    def send(self, data: Dict[str, Any]) -> bool:
        pass

class SimpleHTTPConnector(NetworkConnector):
    """
    A basic HTTP connector using standard library.
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.base_url = ""

    def connect(self, host: str, port: int) -> bool:
        self.base_url = f"http://{host}:{port}"
        # Simulation of a connection check
        return True

    def send(self, data: Dict[str, Any], endpoint: str = "/") -> Dict[str, Any]:
        """
        Sends JSON data to the endpoint.
        """
        if not self.base_url:
            raise ConnectionError("Not connected to any host.")
            
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps(data).encode('utf-8')
        
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = response.read().decode('utf-8')
                return json.loads(result)
        except urllib.error.URLError as e:
            print(f"Network error: {e}")
            return {"error": str(e)}
