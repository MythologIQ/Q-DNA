"""
QoreLogic PyVeritas Transpiler

LLM-powered Python to C transpilation for formal verification.
Supports multiple models with automatic fallback.

Research Reference: FORMAL_METHODS.md §6
- PyVeritas achieves 80-90% accuracy via Qwen2.5-Coder
- Transpiled C code is verified via CBMC

Modes:
- Full: LLM transpilation + CBMC verification
- Lite: Heuristic patterns only (no LLM required)
- Disabled: Skip formal verification
"""

import os
import re
import json
import logging
import hashlib
import tempfile
import subprocess
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TranspilationStatus(Enum):
    """Status of transpilation attempt."""
    SUCCESS = "success"
    LLM_UNAVAILABLE = "llm_unavailable"
    COMPILATION_ERROR = "compilation_error"
    TIMEOUT = "timeout"
    INVALID_OUTPUT = "invalid_output"
    DISABLED = "disabled"


@dataclass
class TranspilationResult:
    """Result of Python to C transpilation."""
    status: TranspilationStatus
    c_code: str
    python_line_map: Dict[int, int]  # C line -> Python line
    model_used: str
    elapsed_ms: float
    error_message: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "c_code_length": len(self.c_code),
            "model_used": self.model_used,
            "elapsed_ms": self.elapsed_ms,
            "error": self.error_message
        }


# Transpilation prompt template
TRANSPILE_PROMPT = """You are a Python to C transpiler. Convert the following Python code to equivalent C code.

Rules:
1. Preserve the exact logic and control flow
2. Add necessary #include statements
3. Handle Python types as: int -> int, float -> double, str -> char*, list -> array
4. Add bounds checking assertions where appropriate
5. Mark each significant C line with a comment showing the original Python line number: // PY:N

Python code:
```python
{python_code}
```

Output ONLY valid C code, no explanations:
```c
"""


class PyVeritasTranspiler:
    """
    LLM-powered Python to C transpiler.
    
    Features:
    - Multiple model fallback
    - Output validation (compilable C check)
    - Line mapping for fault localization
    - Caching for repeated code
    """
    
    def __init__(
        self,
        endpoint: str = "http://localhost:11434/api/generate",
        primary_model: str = "qwen2.5-coder:7b",
        fallback_models: List[str] = None,
        timeout_seconds: int = 30
    ):
        self.endpoint = endpoint
        self.primary_model = primary_model
        self.fallback_models = fallback_models or [
            "codellama:7b",
            "deepseek-coder:6.7b",
            "starcoder2:3b"
        ]
        self.timeout_seconds = timeout_seconds
        self._cache: Dict[str, TranspilationResult] = {}
    
    def is_available(self) -> Tuple[bool, str]:
        """Check if LLM endpoint is available."""
        import requests
        try:
            response = requests.get(
                self.endpoint.replace("/api/generate", "/api/tags"),
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                return True, f"Available models: {model_names[:5]}"
            return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    def transpile(self, python_code: str) -> TranspilationResult:
        """
        Transpile Python code to C.
        
        Args:
            python_code: Python source code
            
        Returns:
            TranspilationResult with C code or error
        """
        import time
        start_time = time.time()
        
        # Check cache
        code_hash = hashlib.md5(python_code.encode()).hexdigest()
        if code_hash in self._cache:
            logger.debug(f"Cache hit for {code_hash[:8]}")
            return self._cache[code_hash]
        
        # Try primary model, then fallbacks
        models_to_try = [self.primary_model] + self.fallback_models
        
        for model in models_to_try:
            result = self._try_model(model, python_code, start_time)
            if result.status == TranspilationStatus.SUCCESS:
                self._cache[code_hash] = result
                return result
            elif result.status == TranspilationStatus.LLM_UNAVAILABLE:
                # No point trying other models if endpoint is down
                return result
        
        # All models failed
        elapsed = (time.time() - start_time) * 1000
        return TranspilationResult(
            status=TranspilationStatus.INVALID_OUTPUT,
            c_code="",
            python_line_map={},
            model_used="none",
            elapsed_ms=elapsed,
            error_message="All models failed to produce valid C code"
        )
    
    def _try_model(
        self, 
        model: str, 
        python_code: str, 
        start_time: float
    ) -> TranspilationResult:
        """Attempt transpilation with a specific model."""
        import time
        import requests
        
        prompt = TRANSPILE_PROMPT.format(python_code=python_code)
        
        try:
            response = requests.post(
                self.endpoint,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temp for determinism
                        "num_predict": 2000
                    }
                },
                timeout=self.timeout_seconds
            )
            
            if response.status_code != 200:
                return TranspilationResult(
                    status=TranspilationStatus.LLM_UNAVAILABLE,
                    c_code="",
                    python_line_map={},
                    model_used=model,
                    elapsed_ms=(time.time() - start_time) * 1000,
                    error_message=f"HTTP {response.status_code}"
                )
            
            data = response.json()
            raw_output = data.get("response", "")
            
            # Extract C code from output
            c_code = self._extract_c_code(raw_output)
            
            if not c_code:
                return TranspilationResult(
                    status=TranspilationStatus.INVALID_OUTPUT,
                    c_code="",
                    python_line_map={},
                    model_used=model,
                    elapsed_ms=(time.time() - start_time) * 1000,
                    error_message="No valid C code in LLM output"
                )
            
            # Validate C code compiles
            is_valid, compile_error = self._validate_c_syntax(c_code)
            
            if not is_valid:
                return TranspilationResult(
                    status=TranspilationStatus.COMPILATION_ERROR,
                    c_code=c_code,
                    python_line_map={},
                    model_used=model,
                    elapsed_ms=(time.time() - start_time) * 1000,
                    error_message=compile_error
                )
            
            # Extract line mapping
            line_map = self._extract_line_map(c_code)
            
            elapsed = (time.time() - start_time) * 1000
            return TranspilationResult(
                status=TranspilationStatus.SUCCESS,
                c_code=c_code,
                python_line_map=line_map,
                model_used=model,
                elapsed_ms=elapsed
            )
            
        except requests.exceptions.Timeout:
            return TranspilationResult(
                status=TranspilationStatus.TIMEOUT,
                c_code="",
                python_line_map={},
                model_used=model,
                elapsed_ms=(time.time() - start_time) * 1000,
                error_message=f"Timeout after {self.timeout_seconds}s"
            )
        except Exception as e:
            return TranspilationResult(
                status=TranspilationStatus.LLM_UNAVAILABLE,
                c_code="",
                python_line_map={},
                model_used=model,
                elapsed_ms=(time.time() - start_time) * 1000,
                error_message=str(e)
            )
    
    def _extract_c_code(self, raw_output: str) -> str:
        """Extract C code from LLM output."""
        # Look for code block
        code_match = re.search(r'```c?\n(.*?)```', raw_output, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # If no code block, try to find C-like content
        lines = raw_output.strip().split('\n')
        c_lines = []
        in_code = False
        
        for line in lines:
            # Heuristic: looks like C code
            if re.match(r'^(#include|int |void |char |double |float |struct |if |for |while |return )', line):
                in_code = True
            if in_code:
                c_lines.append(line)
        
        return '\n'.join(c_lines).strip()
    
    def _validate_c_syntax(self, c_code: str) -> Tuple[bool, str]:
        """Validate C code compiles (syntax check only)."""
        # Try GCC first, then Clang
        compilers = ["gcc", "clang"]
        
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.c', 
            delete=False,
            encoding='utf-8'
        ) as tmp:
            tmp.write(c_code)
            tmp_path = tmp.name
        
        try:
            for compiler in compilers:
                import shutil
                if shutil.which(compiler) is None:
                    continue
                
                result = subprocess.run(
                    [compiler, "-fsyntax-only", "-x", "c", tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    return True, ""
                else:
                    return False, result.stderr[:500]
            
            # No compiler available - assume valid
            logger.warning("No C compiler available for syntax validation")
            return True, ""
            
        except Exception as e:
            return False, str(e)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def _extract_line_map(self, c_code: str) -> Dict[int, int]:
        """Extract C line -> Python line mapping from comments."""
        line_map = {}
        
        for c_line_num, line in enumerate(c_code.splitlines(), 1):
            # Look for // PY:N pattern
            match = re.search(r'//\s*PY:(\d+)', line)
            if match:
                py_line = int(match.group(1))
                line_map[c_line_num] = py_line
        
        return line_map


# Singleton accessor
_transpiler = None

def get_transpiler() -> PyVeritasTranspiler:
    """Get the singleton transpiler instance."""
    global _transpiler
    if _transpiler is None:
        try:
            from .verification_config import get_verification_config
            config = get_verification_config()
            _transpiler = PyVeritasTranspiler(
                endpoint=config.llm_endpoint,
                primary_model=config.llm_model,
                fallback_models=config.fallback_models,
                timeout_seconds=config.timeout_seconds
            )
        except ImportError:
            _transpiler = PyVeritasTranspiler()
    return _transpiler


def transpile_and_verify(python_code: str) -> Dict:
    """
    Complete PyVeritas pipeline: Transpile Python to C, then verify with CBMC.
    
    Returns dict with transpilation and verification results.
    """
    from .cbmc_wrapper import get_cbmc_wrapper
    from .verification_config import get_verification_config, VerificationMode
    
    config = get_verification_config()
    
    if config.is_disabled():
        return {
            "status": "disabled",
            "message": "Formal verification disabled in configuration"
        }
    
    # Transpile
    transpiler = get_transpiler()
    trans_result = transpiler.transpile(python_code)
    
    result = {
        "transpilation": trans_result.to_dict()
    }
    
    if trans_result.status != TranspilationStatus.SUCCESS:
        result["status"] = "transpilation_failed"
        result["message"] = trans_result.error_message
        return result
    
    # Verify with CBMC
    wrapper = get_cbmc_wrapper(
        timeout_seconds=config.timeout_seconds,
        memory_limit_mb=config.memory_limit_mb,
        unwind_depth=config.cbmc_unwind_depth
    )
    
    verify_result = wrapper.verify_c_code(trans_result.c_code)
    result["verification"] = verify_result.to_dict()
    
    # Map violations back to Python lines
    if verify_result.violations:
        mapped_violations = []
        for v in verify_result.violations:
            py_line = trans_result.python_line_map.get(v.line, None)
            mapped_violations.append({
                **v.to_dict(),
                "python_line": py_line
            })
        result["mapped_violations"] = mapped_violations
    
    result["status"] = verify_result.status.value.lower()
    return result
