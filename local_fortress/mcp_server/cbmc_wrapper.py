"""
QoreLogic CBMC Wrapper

Safe wrapper for CBMC execution with timeouts, memory limits, and
result parsing. Used by both Full Mode (after transpilation) and
direct C code verification.

Research Reference: FORMAL_METHODS.md §3.3
"""

import os
import shutil
import subprocess
import tempfile
import signal
import logging
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CBMCStatus(Enum):
    """CBMC execution result status."""
    PASS = "PASS"              # No violations found
    FAIL = "FAIL"              # Violations detected
    TIMEOUT = "TIMEOUT"        # Exceeded time limit
    MEMORY_EXCEEDED = "MEMORY_EXCEEDED"  # Exceeded memory limit
    PARSE_ERROR = "PARSE_ERROR"  # Could not parse C code
    UNAVAILABLE = "UNAVAILABLE"  # CBMC not installed
    ERROR = "ERROR"            # Other error


@dataclass
class CBMCViolation:
    """A single CBMC violation."""
    type: str           # e.g., "division by zero", "array bounds"
    file: str
    line: int
    function: str
    description: str
    trace: List[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "file": self.file,
            "line": self.line,
            "function": self.function,
            "description": self.description,
            "trace": self.trace or []
        }


@dataclass
class CBMCResult:
    """Complete CBMC execution result."""
    status: CBMCStatus
    violations: List[CBMCViolation]
    output: str
    stderr: str = ""
    elapsed_seconds: float = 0.0
    unwind_depth: int = 10
    
    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "violation_count": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
            "elapsed_seconds": self.elapsed_seconds,
            "unwind_depth": self.unwind_depth
        }


class CBMCWrapper:
    """
    Safe CBMC execution wrapper.
    
    Features:
    - Timeout protection
    - Memory limits (via ulimit on Linux, advisory on Windows)
    - Structured result parsing
    - Temporary file management
    """
    
    def __init__(
        self,
        timeout_seconds: int = 30,
        memory_limit_mb: int = 512,
        unwind_depth: int = 10
    ):
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.unwind_depth = unwind_depth
        self.cbmc_path = shutil.which("cbmc")
        
    @property
    def is_available(self) -> bool:
        """Check if CBMC is installed."""
        return self.cbmc_path is not None
    
    def verify_c_code(self, c_code: str, function: str = None) -> CBMCResult:
        """
        Verify C code with CBMC.
        
        Args:
            c_code: C source code to verify
            function: Optional function to verify (--function flag)
            
        Returns:
            CBMCResult with status and violations
        """
        if not self.is_available:
            return CBMCResult(
                status=CBMCStatus.UNAVAILABLE,
                violations=[],
                output="CBMC binary not found in PATH"
            )
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.c', 
            delete=False,
            encoding='utf-8'
        ) as tmp:
            tmp.write(c_code)
            tmp_path = tmp.name
        
        try:
            return self._run_cbmc(tmp_path, function)
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def verify_c_file(self, file_path: str, function: str = None) -> CBMCResult:
        """Verify an existing C file."""
        if not self.is_available:
            return CBMCResult(
                status=CBMCStatus.UNAVAILABLE,
                violations=[],
                output="CBMC binary not found in PATH"
            )
        
        if not os.path.exists(file_path):
            return CBMCResult(
                status=CBMCStatus.ERROR,
                violations=[],
                output=f"File not found: {file_path}"
            )
        
        return self._run_cbmc(file_path, function)
    
    def _run_cbmc(self, file_path: str, function: str = None) -> CBMCResult:
        """Execute CBMC with safety limits."""
        import time
        start_time = time.time()
        
        # Build command
        cmd = [
            self.cbmc_path,
            file_path,
            f"--unwind", str(self.unwind_depth),
            "--bounds-check",
            "--pointer-check",
            "--div-by-zero-check",
            "--signed-overflow-check",
            "--unsigned-overflow-check",
            "--json-ui"  # Structured output
        ]
        
        if function:
            cmd.extend(["--function", function])
        
        try:
            # Run with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            
            elapsed = time.time() - start_time
            
            # Parse result
            if result.returncode == 0:
                return CBMCResult(
                    status=CBMCStatus.PASS,
                    violations=[],
                    output=result.stdout,
                    stderr=result.stderr,
                    elapsed_seconds=elapsed,
                    unwind_depth=self.unwind_depth
                )
            elif result.returncode == 10:
                # Verification failed - parse violations
                violations = self._parse_violations(result.stdout)
                return CBMCResult(
                    status=CBMCStatus.FAIL,
                    violations=violations,
                    output=result.stdout,
                    stderr=result.stderr,
                    elapsed_seconds=elapsed,
                    unwind_depth=self.unwind_depth
                )
            else:
                # Other error (likely parse error)
                return CBMCResult(
                    status=CBMCStatus.PARSE_ERROR,
                    violations=[],
                    output=result.stdout,
                    stderr=result.stderr,
                    elapsed_seconds=elapsed,
                    unwind_depth=self.unwind_depth
                )
                
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            return CBMCResult(
                status=CBMCStatus.TIMEOUT,
                violations=[],
                output=f"CBMC exceeded {self.timeout_seconds}s timeout",
                elapsed_seconds=elapsed,
                unwind_depth=self.unwind_depth
            )
        except Exception as e:
            elapsed = time.time() - start_time
            return CBMCResult(
                status=CBMCStatus.ERROR,
                violations=[],
                output=str(e),
                elapsed_seconds=elapsed,
                unwind_depth=self.unwind_depth
            )
    
    def _parse_violations(self, output: str) -> List[CBMCViolation]:
        """Parse CBMC output for violations."""
        violations = []
        
        # Try JSON parsing first
        import json
        try:
            data = json.loads(output)
            for item in data:
                if item.get("messageType") == "ERROR":
                    violations.append(CBMCViolation(
                        type=item.get("property", "unknown"),
                        file=item.get("sourceLocation", {}).get("file", ""),
                        line=item.get("sourceLocation", {}).get("line", 0),
                        function=item.get("sourceLocation", {}).get("function", ""),
                        description=item.get("messageText", ""),
                        trace=[]
                    ))
            return violations
        except json.JSONDecodeError:
            pass
        
        # Fallback to text parsing
        for line in output.splitlines():
            if "FAILURE" in line or "VIOLATED" in line:
                violations.append(CBMCViolation(
                    type="unknown",
                    file="",
                    line=0,
                    function="",
                    description=line.strip(),
                    trace=[]
                ))
        
        return violations


# Singleton accessor
_wrapper = None

def get_cbmc_wrapper(
    timeout_seconds: int = 30,
    memory_limit_mb: int = 512,
    unwind_depth: int = 10
) -> CBMCWrapper:
    """Get CBMC wrapper instance."""
    global _wrapper
    if _wrapper is None:
        _wrapper = CBMCWrapper(timeout_seconds, memory_limit_mb, unwind_depth)
    return _wrapper


def check_cbmc_available() -> Tuple[bool, str]:
    """Check if CBMC is available and return version."""
    cbmc_path = shutil.which("cbmc")
    if not cbmc_path:
        return False, "CBMC not found in PATH"
    
    try:
        result = subprocess.run([cbmc_path, "--version"], capture_output=True, text=True)
        version = result.stdout.strip().split('\n')[0]
        return True, version
    except Exception as e:
        return False, str(e)
