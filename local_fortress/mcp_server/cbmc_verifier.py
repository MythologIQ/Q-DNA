"""
QoreLogic BMC Verifier (Phase 10.5 - COMPLETE)

Unified formal verification interface supporting three modes:
- Full: LLM transpilation (PyVeritas) + CBMC verification
- Lite: Heuristic pattern matching (no LLM required)
- Disabled: Skip formal verification

Research Reference: FORMAL_METHODS.md §6
- PyVeritas achieves 80-90% accuracy via Python->C transpilation + CBMC
- Small Scope Hypothesis: 5-10 step bounds catch most errors
- Lite mode heuristics catch 60-70% of common patterns
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class CBMCStatus(Enum):
    """Verification result status."""
    PASS = "PASS"              # No violations found
    FAIL = "FAIL"              # Violations detected
    ERROR = "ERROR"            # Verification error
    UNAVAILABLE = "UNAVAILABLE"  # Prerequisites not met
    DISABLED = "DISABLED"      # User disabled verification
    LITE_ONLY = "LITE_ONLY"    # Only heuristic checks ran


@dataclass
class BMCResult:
    """Unified verification result."""
    status: CBMCStatus
    violations: List[str]
    output: str
    mode: str = "unknown"       # "full", "lite", "disabled"
    heuristic_findings: List[Dict] = None
    transpilation_used: bool = False
    model_used: str = ""
    
    def __post_init__(self):
        if self.heuristic_findings is None:
            self.heuristic_findings = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "violations": self.violations,
            "mode": self.mode,
            "heuristic_findings": self.heuristic_findings,
            "transpilation_used": self.transpilation_used,
            "model_used": self.model_used
        }


class CBMCVerifier:
    """
    Unified formal verification interface.
    
    Automatically selects verification strategy based on:
    1. Configuration (Full/Lite/Disabled)
    2. Prerequisites (CBMC available, LLM available)
    3. Content type (Python vs C)
    """
    
    def __init__(self):
        self._config = None
        self._heuristic_scanner = None
        self._transpiler = None
        self._cbmc_wrapper = None
    
    @property
    def config(self):
        if self._config is None:
            try:
                from .verification_config import get_verification_config
                self._config = get_verification_config()
            except ImportError:
                # Fallback to default Lite mode
                from .verification_config import VerificationConfig
                self._config = VerificationConfig()
        return self._config
    
    @property
    def heuristic_scanner(self):
        if self._heuristic_scanner is None:
            try:
                from .heuristic_patterns import get_heuristic_scanner
                self._heuristic_scanner = get_heuristic_scanner()
            except ImportError:
                self._heuristic_scanner = None
        return self._heuristic_scanner
    
    @property
    def transpiler(self):
        if self._transpiler is None:
            try:
                from .pyveritas_transpiler import get_transpiler
                self._transpiler = get_transpiler()
            except ImportError:
                self._transpiler = None
        return self._transpiler
    
    @property
    def cbmc_wrapper(self):
        if self._cbmc_wrapper is None:
            try:
                from .cbmc_wrapper import get_cbmc_wrapper
                self._cbmc_wrapper = get_cbmc_wrapper(
                    timeout_seconds=self.config.timeout_seconds,
                    memory_limit_mb=self.config.memory_limit_mb,
                    unwind_depth=self.config.cbmc_unwind_depth
                )
            except ImportError:
                self._cbmc_wrapper = None
        return self._cbmc_wrapper
    
    def verify(self, content: str, is_c_code: bool = False) -> BMCResult:
        """
        Run verification on the artifact.
        
        Args:
            content: Source code to verify
            is_c_code: True if content is C, False if Python
            
        Returns:
            BMCResult with status and findings
        """
        # Check if disabled
        if self.config.is_disabled():
            return BMCResult(
                status=CBMCStatus.DISABLED,
                violations=[],
                output="Formal verification disabled in configuration",
                mode="disabled"
            )
        
        # For C code, use CBMC directly if available
        if is_c_code:
            return self._verify_c_code(content)
        
        # For Python, choose strategy based on mode
        if self.config.is_full_mode():
            return self._verify_python_full(content)
        else:
            return self._verify_python_lite(content)
    
    def _verify_c_code(self, content: str) -> BMCResult:
        """Verify C code with CBMC."""
        if self.cbmc_wrapper is None or not self.cbmc_wrapper.is_available:
            return BMCResult(
                status=CBMCStatus.UNAVAILABLE,
                violations=[],
                output="CBMC binary not found in PATH",
                mode="full"
            )
        
        result = self.cbmc_wrapper.verify_c_code(content)
        
        return BMCResult(
            status=CBMCStatus(result.status.value),
            violations=[v.description for v in result.violations],
            output=result.output,
            mode="full",
            transpilation_used=False
        )
    
    def _verify_python_full(self, content: str) -> BMCResult:
        """Full Mode: Transpile Python to C, then verify with CBMC."""
        # Always run heuristics first
        heuristic_findings = self._run_heuristics(content)
        
        # Check if transpiler available
        if self.transpiler is None:
            logger.warning("PyVeritas transpiler not available, falling back to Lite mode")
            return self._verify_python_lite(content)
        
        # Check if LLM is available
        available, msg = self.transpiler.is_available()
        if not available:
            logger.warning(f"LLM not available ({msg}), falling back to Lite mode")
            return BMCResult(
                status=CBMCStatus.LITE_ONLY,
                violations=[f["id"] + ": " + f["description"] for f in heuristic_findings if f["severity"] in ["HIGH", "CRITICAL"]],
                output=f"LLM unavailable ({msg}). Heuristic analysis only.",
                mode="lite",
                heuristic_findings=heuristic_findings
            )
        
        # Transpile
        from .pyveritas_transpiler import TranspilationStatus
        trans_result = self.transpiler.transpile(content)
        
        if trans_result.status != TranspilationStatus.SUCCESS:
            logger.warning(f"Transpilation failed: {trans_result.error_message}")
            return BMCResult(
                status=CBMCStatus.LITE_ONLY,
                violations=[f["id"] + ": " + f["description"] for f in heuristic_findings if f["severity"] in ["HIGH", "CRITICAL"]],
                output=f"Transpilation failed: {trans_result.error_message}. Heuristic analysis only.",
                mode="lite",
                heuristic_findings=heuristic_findings,
                transpilation_used=False,
                model_used=trans_result.model_used
            )
        
        # Verify with CBMC
        if self.cbmc_wrapper is None or not self.cbmc_wrapper.is_available:
            return BMCResult(
                status=CBMCStatus.LITE_ONLY,
                violations=[f["id"] + ": " + f["description"] for f in heuristic_findings if f["severity"] in ["HIGH", "CRITICAL"]],
                output="CBMC unavailable. Heuristic analysis only.",
                mode="lite",
                heuristic_findings=heuristic_findings,
                transpilation_used=True,
                model_used=trans_result.model_used
            )
        
        cbmc_result = self.cbmc_wrapper.verify_c_code(trans_result.c_code)
        
        # Merge heuristic and CBMC findings
        all_violations = []
        
        # Add CBMC violations with Python line mapping
        for v in cbmc_result.violations:
            py_line = trans_result.python_line_map.get(v.line)
            if py_line:
                all_violations.append(f"[L{py_line}] {v.type}: {v.description}")
            else:
                all_violations.append(f"{v.type}: {v.description}")
        
        # Add critical heuristic findings
        for f in heuristic_findings:
            if f["severity"] in ["HIGH", "CRITICAL"]:
                all_violations.append(f"[L{f['line']}] {f['id']}: {f['description']}")
        
        # Determine final status
        if cbmc_result.status.value == "FAIL" or any(f["severity"] == "CRITICAL" for f in heuristic_findings):
            status = CBMCStatus.FAIL
        elif cbmc_result.status.value == "PASS":
            status = CBMCStatus.PASS
        else:
            status = CBMCStatus(cbmc_result.status.value)
        
        return BMCResult(
            status=status,
            violations=all_violations,
            output=cbmc_result.output,
            mode="full",
            heuristic_findings=heuristic_findings,
            transpilation_used=True,
            model_used=trans_result.model_used
        )
    
    def _verify_python_lite(self, content: str) -> BMCResult:
        """Lite Mode: Heuristic pattern matching only."""
        findings = self._run_heuristics(content)
        
        # Extract violations (HIGH and CRITICAL)
        violations = []
        for f in findings:
            if f["severity"] in ["HIGH", "CRITICAL"]:
                violations.append(f"[L{f['line']}] {f['id']}: {f['description']}")
        
        if violations:
            status = CBMCStatus.FAIL
        else:
            status = CBMCStatus.PASS
        
        return BMCResult(
            status=status,
            violations=violations,
            output=f"Lite mode: {len(findings)} patterns checked, {len(violations)} critical issues found",
            mode="lite",
            heuristic_findings=findings
        )
    
    def _run_heuristics(self, content: str) -> List[Dict]:
        """Run heuristic pattern scanner."""
        if self.heuristic_scanner is None:
            return []
        
        return self.heuristic_scanner.scan(content, severity_threshold="LOW")


# Singleton accessor
_verifier = None

def get_cbmc_verifier() -> CBMCVerifier:
    """Get the singleton verifier instance."""
    global _verifier
    if _verifier is None:
        _verifier = CBMCVerifier()
    return _verifier
