import os
from typing import Optional

class Config:
    """
    Basic configuration loader.
    """
    
    @staticmethod
    def get(key: str, default: Optional[str] = None) -> Optional[str]:
        return os.environ.get(key, default)

    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        val = os.environ.get(key)
        if val is None:
            return default
        try:
            return int(val)
        except ValueError:
            return default

    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        val = os.environ.get(key)
        if val is None:
            return default
        return val.lower() in ('true', '1', 'yes', 'on')
