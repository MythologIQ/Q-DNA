"""
Q-DNA Sentinel Engine v2.0

Implements the full verification pipeline as specified in Q-DNA_SPECIFICATION.md:
- Static Safety Analysis (L1/L2)
- Cyclomatic Complexity Check (L2)
- Citation Depth Enforcement (L2)
- Quote Context Verification (L2)
- Bounded Model Checking Simulation (L3)
- Risk Grade Auto-Classification
- PII Redaction Filter
"""

import re
import ast
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

class RiskGrade(Enum):
    L1 = "L1"  # Low - Routine
    L2 = "L2"  # Medium - Functional
    L3 = "L3"  # High - Critical

class FailureMode(Enum):
    HARDCODED_SECRET = "HARDCODED_SECRET"
    UNSAFE_FUNCTION = "UNSAFE_FUNCTION"
    HIGH_COMPLEXITY = "HIGH_COMPLEXITY"
    CITATION_DEPTH = "CITATION_DEPTH"
    MISSING_CONTEXT = "MISSING_CONTEXT"
    PII_EXPOSURE = "PII_EXPOSURE"
    DIVISION_BY_ZERO = "DIVISION_BY_ZERO"
    INJECTION_RISK = "INJECTION_RISK"
    LOGICAL_CONTRADICTION = "LOGICAL_CONTRADICTION"

@dataclass
class AuditResult:
    verdict: str  # PASS, FAIL, L3_REQUIRED
    risk_grade: str
    rationale: str
    failure_modes: List[str]
    latency_ms: float
    pii_redacted: bool = False
    requires_approval: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class SentinelEngine:
    """
    The Sentinel L-Module: Specialized Verification Agent.
    
    Design Philosophy:
    - Fast-fail on known bad patterns (negative constraints)
    - Escalate uncertainty to higher risk grades
    - Never approve L3 without explicit flag for Human review
    """
    
    # Configuration
    COMPLEXITY_THRESHOLD_L2 = 10  # McCabe cyclomatic complexity
    COMPLEXITY_THRESHOLD_L3 = 20
    
    # High-Risk File Patterns (Auto-L3)
    L3_FILE_PATTERNS = [
        r"auth", r"login", r"password", r"credential",
        r"payment", r"billing", r"finance",
        r"encrypt", r"decrypt", r"key", r"secret",
        r"migration", r"schema", r"database",
        r"admin", r"root", r"sudo"
    ]
    
    # Dangerous Patterns
    SECRET_PATTERNS = [
        r"sk_live_[0-9a-zA-Z]{20,}",
        r"sk_test_[0-9a-zA-Z]{20,}",
        r"AIza[0-9A-Za-z\-_]{35}",
        r"ghp_[0-9a-zA-Z]{36}",
        r"aws_access_key_id\s*=\s*['\"][A-Z0-9]{20}['\"]",
        r"password\s*=\s*['\"][^'\"]{4,}['\"]",
        r"api_key\s*=\s*['\"][^'\"]{8,}['\"]",
    ]
    
    UNSAFE_FUNCTIONS = [
        "eval(", "exec(", "compile(",
        "os.system(", "subprocess.call(", "subprocess.Popen(",
        "pickle.loads(", "__import__(",
        "open(", # Flag for review, not auto-fail
    ]
    
    PII_PATTERNS = [
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
        r"\b\d{16}\b",             # Credit Card
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
    ]
    
    def __init__(self, model_url: str = "http://localhost:11434/api/generate"):
        self.model_url = model_url
        self.start_time = 0
    
    def _start_timer(self):
        self.start_time = time.perf_counter()
    
    def _get_latency_ms(self) -> float:
        return (time.perf_counter() - self.start_time) * 1000
    
    def classify_risk_grade(self, file_path: str, content: str) -> RiskGrade:
        """
        Auto-classify risk based on file path and content patterns.
        Per Q-DNA Spec Section 4: Risk Grading.
        """
        file_lower = file_path.lower()
        
        # Check for L3 file patterns
        for pattern in self.L3_FILE_PATTERNS:
            if re.search(pattern, file_lower):
                return RiskGrade.L3
        
        # Check content for L3 indicators
        l3_content_patterns = [
            r"def\s+authenticate", r"def\s+authorize",
            r"CREATE\s+TABLE", r"ALTER\s+TABLE", r"DROP\s+TABLE",
            r"AES|RSA|SHA256|bcrypt|argon2"
        ]
        for pattern in l3_content_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return RiskGrade.L3
        
        # Default to L2 for any code changes
        if content.strip():
            return RiskGrade.L2
        
        return RiskGrade.L1
    
    def check_secrets(self, content: str) -> List[str]:
        """Detect hardcoded secrets and API keys."""
        findings = []
        for pattern in self.SECRET_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                findings.append(FailureMode.HARDCODED_SECRET.value)
                break  # One finding is enough to fail
        return findings
    
    def check_unsafe_functions(self, content: str) -> List[str]:
        """Detect unsafe function calls."""
        findings = []
        for func in self.UNSAFE_FUNCTIONS:
            if func in content:
                findings.append(f"{FailureMode.UNSAFE_FUNCTION.value}:{func}")
        return findings
    
    def check_cyclomatic_complexity(self, content: str) -> tuple[int, List[str]]:
        """
        Calculate cyclomatic complexity using AST.
        Returns (max_complexity, list of findings)
        """
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return 0, []  # Can't parse, skip this check
        
        max_complexity = 0
        findings = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = 1  # Base complexity
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                         ast.With, ast.Assert, ast.comprehension)):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1
                
                if complexity > max_complexity:
                    max_complexity = complexity
                
                if complexity > self.COMPLEXITY_THRESHOLD_L3:
                    findings.append(f"{FailureMode.HIGH_COMPLEXITY.value}:{node.name}={complexity}")
                elif complexity > self.COMPLEXITY_THRESHOLD_L2:
                    findings.append(f"WARN:COMPLEXITY:{node.name}={complexity}")
        
        return max_complexity, findings
    
    def check_pii_exposure(self, content: str) -> tuple[str, bool]:
        """
        Detect and redact PII patterns.
        Returns (redacted_content, had_pii)
        """
        had_pii = False
        redacted = content
        
        for pattern in self.PII_PATTERNS:
            if re.search(pattern, content):
                had_pii = True
                redacted = re.sub(pattern, "[REDACTED]", redacted)
        
        return redacted, had_pii
    
    def check_citation_depth(self, text: str) -> List[str]:
        """
        Enforce Transitive Cap (max 2 degrees).
        """
        findings = []
        
        # Heuristic: Count nested citations
        citation_patterns = [
            r'according to .+ who cited',
            r'as quoted in .+ from',
            r'""".+"""',  # Triple nested quotes
        ]
        
        depth_score = 0
        for pattern in citation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            depth_score += len(matches)
        
        if depth_score > 2:
            findings.append(FailureMode.CITATION_DEPTH.value)
        
        return findings
    
    def check_quote_context(self, text: str) -> List[str]:
        """
        Enforce Quote Context Rule (±2 sentences or 200 chars).
        """
        findings = []
        
        # Find quoted text
        quotes = re.findall(r'"([^"]{10,})"', text)
        
        for quote in quotes:
            # Check if quote has sufficient surrounding context
            quote_pos = text.find(f'"{quote}"')
            context_before = text[max(0, quote_pos-200):quote_pos]
            context_after = text[quote_pos+len(quote)+2:quote_pos+len(quote)+202]
            
            # Very short context is suspicious
            if len(context_before.strip()) < 50 and len(context_after.strip()) < 50:
                findings.append(FailureMode.MISSING_CONTEXT.value)
                break
        
        return findings
    
    def check_formal_contracts(self, content: str) -> List[str]:
        """
        Phase 9.1: Tier 3 Formal Verification.
        Extracts constraints from @deal decorators and validates them with Z3.
        """
        findings = []
        try:
            from local_fortress.mcp_server.contract_verifier import get_contract_verifier
            verifier = get_contract_verifier()
            
            if not verifier.z3_available:
                return ["WARN: Z3 solver unavailable for Tier 3 verification"]

            # Heuristic Constraint Extractor (Bootstrap Phase)
            # Looks for: @deal.pre(lambda ... 0 <= var <= 1)
            # This bridges the gap until full PyVeritas transpiler is ready.
            
            # Regex to find range constraints in deal decorators
            # Matches: 0<=x<=1 or -1.0 <= x <= 1.0
            range_pattern = r'([-]?\d+\.?\d*)\s*<=\s*([a-zA-Z_]\w*)\s*<=\s*([-]?\d+\.?\d*)'
            matches = re.finditer(range_pattern, content)
            
            constraints = {}
            for m in matches:
                min_val = float(m.group(1))
                var_name = m.group(2)
                max_val = float(m.group(3))
                constraints[var_name] = (min_val, max_val)

            if constraints:
                # Run Z3 Verification
                is_sat, msg = verifier.verify_with_z3(constraints)
                if not is_sat:
                    findings.append(f"{FailureMode.LOGICAL_CONTRADICTION.value}: {msg}")
                    
        except ImportError:
            findings.append("WARN: ContractVerifier module not found")
        except Exception as e:
            findings.append(f"WARN: Formal verification failed: {str(e)}")
            
        return findings

    def bounded_model_check(self, content: str) -> List[str]:
        """
        Simulate Bounded Model Checking (L3).
        In production, this would invoke CBMC/ESBMC via PyVeritas.
        """
        findings = []
        
        # 1. Division by zero check
        if re.search(r'/\s*0\b', content):
            findings.append(FailureMode.DIVISION_BY_ZERO.value)
        
        # 2. SQL Injection patterns
        sql_injection = [
            r'execute\(.+%s',
            r'cursor\.execute\(.+\+',
            r'f"SELECT.+{',
        ]
        for pattern in sql_injection:
            if re.search(pattern, content):
                findings.append(FailureMode.INJECTION_RISK.value)
                break
        
        # 3. Formal Contract Verification (Z3)
        findings.extend(self.check_formal_contracts(content))
        
        return findings
    
    def check_static_analysis(self, content: str) -> List[str]:
        """
        Tier 1: External Static Analysis (Pylint, MyPy).
        Spec §3.3.1: "Fast-fail < 5s".
        Runs strict error checking on the provided content.
        """
        findings = []
        import tempfile
        import subprocess
        import os

        # Only check Python content
        # Heuristic: verify basic python syntax with AST first (already implicit via other checks)
        # or just try/catch the tool execution.
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # 1. Pylint (Errors only for speed)
            # --disable=E0401: Ignore import errors (dependencies might be missing in isolation)
            result = subprocess.run(
                ['pylint', '-E', '--disable=E0401', '--msg-template={line}: {msg_id} {msg}', tmp_path], 
                capture_output=True, text=True
            )
            # Pylint exit codes: 1=fatal, 2=error, 4=warning, etc. Bitmask.
            # If errors found, stdout has them.
            if result.stdout:
                for line in result.stdout.splitlines():
                    if line.strip() and not line.startswith("*************"):
                        findings.append(f"PYLINT:{line.strip()}")

            # 2. MyPy
            result_mypy = subprocess.run(
                ['mypy', '--ignore-missing-imports', '--no-error-summary', tmp_path],
                capture_output=True, text=True
            )
            if result_mypy.returncode != 0 and result_mypy.stdout:
                for line in result_mypy.stdout.splitlines():
                    # Filter out "Success" messages if any
                    if "Success:" not in line:
                        clean_line = line.replace(tmp_path, "input.py")
                        findings.append(f"MYPY:{clean_line.strip()}")

        except FileNotFoundError:
            # Bootstrapping: degrade gracefully if tools missing
            findings.append("WARN: Static analysis tools (pylint/mypy) not found in environment.")
        except Exception as e:
            findings.append(f"WARN: Static analysis failed: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            
        return findings

    def audit(self, file_path: str, content: str) -> AuditResult:
        """
        Main entry point for the Sentinel.
        Executes the full verification pipeline.
        """
        self._start_timer()
        
        all_findings: List[str] = []
        requires_approval = False
        
        # 1. Classify Risk Grade
        risk_grade = self.classify_risk_grade(file_path, content)
        
        # 2. PII Redaction (Always)
        redacted_content, had_pii = self.check_pii_exposure(content)
        
        # 3. Static Safety Checks (All Grades)
        all_findings.extend(self.check_secrets(content))
        all_findings.extend(self.check_unsafe_functions(content))
        
        # 3.1 Tier 1: Static Analysis (New in v2.4, Phase 8.5)
        # Skip for empty content or non-python (heuristic: file extension or content)
        if file_path.endswith('.py') or 'def ' in content:
            all_findings.extend(self.check_static_analysis(content))
        
        # 4. L2+ Checks
        if risk_grade in [RiskGrade.L2, RiskGrade.L3]:
            complexity, complexity_findings = self.check_cyclomatic_complexity(content)
            all_findings.extend(complexity_findings)
            all_findings.extend(self.check_citation_depth(content))
            all_findings.extend(self.check_quote_context(content))
        
        # 5. L3 Checks
        if risk_grade == RiskGrade.L3:
            all_findings.extend(self.bounded_model_check(content))
            requires_approval = True  # L3 always requires Human sign-off
        
        # 6. Determine Verdict
        critical_failures = [f for f in all_findings if not f.startswith("WARN:")]
        
        if critical_failures:
            verdict = "FAIL"
            rationale = "; ".join(critical_failures)
        elif requires_approval:
            verdict = "L3_REQUIRED"
            rationale = "L3 artifact requires Overseer approval before commit."
        else:
            verdict = "PASS"
            rationale = f"All {risk_grade.value} checks passed."
        
        return AuditResult(
            verdict=verdict,
            risk_grade=risk_grade.value,
            rationale=rationale,
            failure_modes=all_findings,
            latency_ms=self._get_latency_ms(),
            pii_redacted=had_pii,
            requires_approval=requires_approval
        )
    
    def audit_claim(self, text: str) -> AuditResult:
        """Audit a text claim (non-code artifact)."""
        self._start_timer()
        
        findings = []
        findings.extend(self.check_citation_depth(text))
        findings.extend(self.check_quote_context(text))
        
        _, had_pii = self.check_pii_exposure(text)
        
        if findings:
            verdict = "FAIL"
            rationale = "; ".join(findings)
        else:
            verdict = "PASS"
            rationale = "Claim passes citation and context rules."
        
        return AuditResult(
            verdict=verdict,
            risk_grade="L2",
            rationale=rationale,
            failure_modes=findings,
            latency_ms=self._get_latency_ms(),
            pii_redacted=had_pii,
            requires_approval=False
        )
