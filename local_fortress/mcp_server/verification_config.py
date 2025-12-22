"""
QoreLogic Verification Configuration

Provides unified configuration for formal verification features.
Supports three modes: Full (LLM), Lite (Heuristic), Disabled.

Research Reference: FORMAL_METHODS.md §6
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class VerificationMode(Enum):
    """Verification intensity levels."""
    FULL = "full"       # LLM transpilation + CBMC
    LITE = "lite"       # Heuristic pattern matching only
    DISABLED = "disabled"  # Skip formal verification


@dataclass
class VerificationConfig:
    """
    Configuration for formal verification features.
    
    Attributes:
        mode: Verification intensity (full/lite/disabled)
        llm_endpoint: Ollama API endpoint for transpilation
        llm_model: Primary model for Python→C transpilation
        fallback_models: Backup models if primary unavailable
        timeout_seconds: Max time for verification per artifact
        cbmc_unwind_depth: Loop unrolling depth (Small Scope Hypothesis: 5-10)
        enable_maxsat_localization: Map CBMC errors to Python lines
        memory_limit_mb: Max memory for CBMC process
    """
    mode: VerificationMode = VerificationMode.LITE
    llm_endpoint: str = "http://localhost:11434/api/generate"
    llm_model: str = "qwen2.5-coder:7b"
    fallback_models: List[str] = field(default_factory=lambda: [
        "codellama:7b",
        "deepseek-coder:6.7b",
        "starcoder2:3b"
    ])
    timeout_seconds: int = 30
    cbmc_unwind_depth: int = 10
    enable_maxsat_localization: bool = False
    memory_limit_mb: int = 512
    
    def is_full_mode(self) -> bool:
        return self.mode == VerificationMode.FULL
    
    def is_lite_mode(self) -> bool:
        return self.mode == VerificationMode.LITE
    
    def is_disabled(self) -> bool:
        return self.mode == VerificationMode.DISABLED
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["mode"] = self.mode.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VerificationConfig':
        if "mode" in data:
            data["mode"] = VerificationMode(data["mode"])
        return cls(**data)


# Configuration paths (in order of priority)
CONFIG_PATHS = [
    # 1. Docker container mount point
    "/config/verification.json",
    # 2. Alongside agents.json
    os.path.expanduser("~/.qorelogic/config/verification.json"),
    # 3. Environment variable override
    os.environ.get("QORELOGIC_VERIFICATION_CONFIG", ""),
]


class VerificationConfigLoader:
    """
    Singleton loader for verification configuration.
    """
    _instance: Optional['VerificationConfigLoader'] = None
    _config: Optional[VerificationConfig] = None
    _config_path: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load(self, force_reload: bool = False) -> VerificationConfig:
        """Load configuration from file or return defaults."""
        if self._config and not force_reload:
            return self._config
        
        # Try each config path
        for path in CONFIG_PATHS:
            if path and os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Look for nested formal_verification key or root-level
                    if "formal_verification" in data:
                        data = data["formal_verification"]
                    
                    self._config = VerificationConfig.from_dict(data)
                    self._config_path = path
                    logger.info(f"Loaded verification config from {path}: mode={self._config.mode.value}")
                    return self._config
                    
                except (json.JSONDecodeError, IOError, TypeError) as e:
                    logger.warning(f"Failed to load verification config from {path}: {e}")
                    continue
        
        # Also check agents.json for embedded config
        agents_paths = [
            "/config/agents.json",
            os.path.expanduser("~/.qorelogic/config/agents.json"),
        ]
        
        for path in agents_paths:
            if path and os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if "formal_verification" in data:
                        self._config = VerificationConfig.from_dict(data["formal_verification"])
                        self._config_path = path
                        logger.info(f"Loaded verification config from agents.json: mode={self._config.mode.value}")
                        return self._config
                except Exception:
                    continue
        
        # Return defaults
        logger.info("Using default verification config: mode=lite")
        self._config = VerificationConfig()
        return self._config
    
    def get_config(self) -> VerificationConfig:
        """Get current configuration."""
        if self._config is None:
            return self.load()
        return self._config
    
    def reload(self) -> VerificationConfig:
        """Force reload from disk."""
        return self.load(force_reload=True)
    
    def save_config(self, config: VerificationConfig, path: str = None) -> bool:
        """Save configuration to file."""
        if path is None:
            path = os.path.expanduser("~/.qorelogic/config/verification.json")
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2)
            
            self._config = config
            self._config_path = path
            logger.info(f"Saved verification config to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save verification config: {e}")
            return False


# Singleton accessors
def get_verification_config() -> VerificationConfig:
    """Get the current verification configuration."""
    return VerificationConfigLoader().get_config()


def set_verification_mode(mode: VerificationMode) -> bool:
    """Quick setter for verification mode."""
    loader = VerificationConfigLoader()
    config = loader.get_config()
    config.mode = mode
    return loader.save_config(config)


def is_full_verification_available() -> bool:
    """Check if Full mode prerequisites are met."""
    import shutil
    
    # Check for CBMC
    has_cbmc = shutil.which("cbmc") is not None
    
    # Check for Ollama (basic connectivity test)
    has_ollama = False
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        has_ollama = response.status_code == 200
    except Exception:
        pass
    
    return has_cbmc and has_ollama
