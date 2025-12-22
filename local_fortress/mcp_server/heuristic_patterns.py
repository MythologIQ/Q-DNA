"""
QoreLogic Heuristic Pattern Library

Provides pattern-based vulnerability detection for Lite Mode.
These patterns catch common issues without requiring LLM/CBMC.

Research Reference: FORMAL_METHODS.md §3.3 (Small Scope Hypothesis)
"""

import re
from typing import List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum


class VulnerabilityCategory(Enum):
    """Categories of detected vulnerabilities."""
    MEMORY = "memory"           # Buffer overflow, null deref
    ARITHMETIC = "arithmetic"   # Division by zero, overflow
    INJECTION = "injection"     # SQL, command, code injection
    CRYPTO = "crypto"           # Weak crypto, hardcoded secrets
    RESOURCE = "resource"       # Resource leaks, deadlocks
    LOGIC = "logic"             # Logical contradictions


@dataclass
class HeuristicPattern:
    """A single vulnerability detection pattern."""
    id: str
    name: str
    category: VulnerabilityCategory
    pattern: str  # Regex pattern
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    cwe_id: str = ""  # Common Weakness Enumeration ID
    
    def matches(self, content: str) -> List[Tuple[int, str]]:
        """
        Find all matches in content.
        Returns list of (line_number, matched_text).
        """
        results = []
        for i, line in enumerate(content.splitlines(), 1):
            if re.search(self.pattern, line, re.IGNORECASE):
                results.append((i, line.strip()))
        return results


# =============================================================================
# Pattern Library
# =============================================================================

VULNERABILITY_PATTERNS: List[HeuristicPattern] = [
    # --- Arithmetic ---
    HeuristicPattern(
        id="ARITH-001",
        name="Division by Zero (Literal)",
        category=VulnerabilityCategory.ARITHMETIC,
        pattern=r'/\s*0\s*($|[;#,\)\]])',  # Matches end of line or terminators
        severity="HIGH",
        description="Potential division by literal zero",
        cwe_id="CWE-369"
    ),
    HeuristicPattern(
        id="ARITH-002",
        name="Division by Variable (Unchecked)",
        category=VulnerabilityCategory.ARITHMETIC,
        pattern=r'/\s*[a-zA-Z_]\w*\s*(?![!=<>])',
        severity="MEDIUM",
        description="Division by variable without zero-check guard",
        cwe_id="CWE-369"
    ),
    HeuristicPattern(
        id="ARITH-003",
        name="Integer Overflow Risk",
        category=VulnerabilityCategory.ARITHMETIC,
        pattern=r'\*\s*\d{10,}|\d{10,}\s*\*',
        severity="MEDIUM",
        description="Multiplication with very large literal",
        cwe_id="CWE-190"
    ),
    
    # --- Memory/Buffer ---
    HeuristicPattern(
        id="MEM-001",
        name="Unsafe Index Access",
        category=VulnerabilityCategory.MEMORY,
        pattern=r'\[\s*-\d+\s*\]',
        severity="MEDIUM",
        description="Negative index access (may be intentional in Python)",
        cwe_id="CWE-125"
    ),
    HeuristicPattern(
        id="MEM-002",
        name="Hardcoded Large Index",
        category=VulnerabilityCategory.MEMORY,
        pattern=r'\[\s*\d{4,}\s*\]',
        severity="LOW",
        description="Very large hardcoded index",
        cwe_id="CWE-129"
    ),
    
    # --- Injection ---
    HeuristicPattern(
        id="INJ-001",
        name="SQL Injection (f-string)",
        category=VulnerabilityCategory.INJECTION,
        pattern=r'execute\s*\(\s*f["\'].*\{',
        severity="CRITICAL",
        description="SQL query built with f-string interpolation",
        cwe_id="CWE-89"
    ),
    HeuristicPattern(
        id="INJ-002",
        name="SQL Injection (format)",
        category=VulnerabilityCategory.INJECTION,
        pattern=r'execute\s*\(.*\.format\s*\(',
        severity="CRITICAL",
        description="SQL query built with .format()",
        cwe_id="CWE-89"
    ),
    HeuristicPattern(
        id="INJ-003",
        name="SQL Injection (concat)",
        category=VulnerabilityCategory.INJECTION,
        pattern=r'execute\s*\([^)]*\+',
        severity="CRITICAL",
        description="SQL query built with string concatenation",
        cwe_id="CWE-89"
    ),
    HeuristicPattern(
        id="INJ-004",
        name="Command Injection (os.system)",
        category=VulnerabilityCategory.INJECTION,
        pattern=r'os\.system\s*\(\s*[^"\'][^)]*\+',
        severity="CRITICAL",
        description="shell command with dynamic input",
        cwe_id="CWE-78"
    ),
    HeuristicPattern(
        id="INJ-005",
        name="Command Injection (subprocess)",
        category=VulnerabilityCategory.INJECTION,
        pattern=r'subprocess\.(call|run|Popen)\s*\(\s*[^"\'][^)]*\+',
        severity="HIGH",
        description="subprocess with dynamic command string",
        cwe_id="CWE-78"
    ),
    HeuristicPattern(
        id="INJ-006",
        name="Code Injection (eval)",
        category=VulnerabilityCategory.INJECTION,
        pattern=r'\beval\s*\([^)]*[a-zA-Z_]\w*[^)]*\)',
        severity="CRITICAL",
        description="eval() with variable input",
        cwe_id="CWE-94"
    ),
    HeuristicPattern(
        id="INJ-007",
        name="Code Injection (exec)",
        category=VulnerabilityCategory.INJECTION,
        pattern=r'\bexec\s*\([^)]*[a-zA-Z_]\w*[^)]*\)',
        severity="CRITICAL",
        description="exec() with variable input",
        cwe_id="CWE-94"
    ),
    
    # --- Crypto/Secrets ---
    HeuristicPattern(
        id="CRYPTO-001",
        name="Hardcoded API Key (Stripe)",
        category=VulnerabilityCategory.CRYPTO,
        pattern=r'sk_(live|test)_[0-9a-zA-Z]{20,}',
        severity="CRITICAL",
        description="Stripe secret key in source code",
        cwe_id="CWE-798"
    ),
    HeuristicPattern(
        id="CRYPTO-002",
        name="Hardcoded API Key (AWS)",
        category=VulnerabilityCategory.CRYPTO,
        pattern=r'AKIA[0-9A-Z]{16}',
        severity="CRITICAL",
        description="AWS access key in source code",
        cwe_id="CWE-798"
    ),
    HeuristicPattern(
        id="CRYPTO-003",
        name="Hardcoded API Key (GitHub)",
        category=VulnerabilityCategory.CRYPTO,
        pattern=r'ghp_[0-9a-zA-Z]{36}',
        severity="CRITICAL",
        description="GitHub personal access token in source code",
        cwe_id="CWE-798"
    ),
    HeuristicPattern(
        id="CRYPTO-004",
        name="Hardcoded Password",
        category=VulnerabilityCategory.CRYPTO,
        pattern=r'password\s*=\s*["\'][^"\']{4,}["\']',
        severity="HIGH",
        description="Hardcoded password assignment",
        cwe_id="CWE-259"
    ),
    HeuristicPattern(
        id="CRYPTO-005",
        name="Weak Hash (MD5)",
        category=VulnerabilityCategory.CRYPTO,
        pattern=r'hashlib\.md5\s*\(',
        severity="MEDIUM",
        description="MD5 hash (cryptographically broken)",
        cwe_id="CWE-328"
    ),
    HeuristicPattern(
        id="CRYPTO-006",
        name="Weak Hash (SHA1)",
        category=VulnerabilityCategory.CRYPTO,
        pattern=r'hashlib\.sha1\s*\(',
        severity="LOW",
        description="SHA1 hash (weak for security purposes)",
        cwe_id="CWE-328"
    ),
    
    # --- Resource ---
    HeuristicPattern(
        id="RES-001",
        name="Unclosed File",
        category=VulnerabilityCategory.RESOURCE,
        pattern=r'open\s*\([^)]+\)\s*$',
        severity="LOW",
        description="File opened without context manager",
        cwe_id="CWE-404"
    ),
    
    # --- Logic ---
    HeuristicPattern(
        id="LOGIC-001",
        name="Impossible Condition",
        category=VulnerabilityCategory.LOGIC,
        pattern=r'if\s+False\s*:',
        severity="LOW",
        description="Condition that is always false",
        cwe_id="CWE-570"
    ),
    HeuristicPattern(
        id="LOGIC-002",
        name="Always True Condition",
        category=VulnerabilityCategory.LOGIC,
        pattern=r'if\s+True\s*:',
        severity="LOW",
        description="Condition that is always true",
        cwe_id="CWE-571"
    ),
    HeuristicPattern(
        id="LOGIC-003",
        name="Useless Comparison",
        category=VulnerabilityCategory.LOGIC,
        pattern=r'\bx\s*==\s*x\b|\bx\s*!=\s*x\b',
        severity="LOW",
        description="Variable compared to itself",
        cwe_id="CWE-697"
    ),
]


class HeuristicScanner:
    """
    Scans code for vulnerabilities using pattern matching.
    This is the Lite Mode engine.
    """
    
    def __init__(self, patterns: List[HeuristicPattern] = None):
        self.patterns = patterns or VULNERABILITY_PATTERNS
    
    def scan(self, content: str, severity_threshold: str = "LOW") -> List[Dict]:
        """
        Scan content for vulnerabilities.
        
        Args:
            content: Source code to scan
            severity_threshold: Minimum severity to report (LOW, MEDIUM, HIGH, CRITICAL)
            
        Returns:
            List of finding dictionaries
        """
        severity_levels = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        threshold = severity_levels.get(severity_threshold, 1)
        
        findings = []
        
        for pattern in self.patterns:
            if severity_levels.get(pattern.severity, 0) < threshold:
                continue
                
            matches = pattern.matches(content)
            for line_num, line_text in matches:
                findings.append({
                    "id": pattern.id,
                    "name": pattern.name,
                    "category": pattern.category.value,
                    "severity": pattern.severity,
                    "line": line_num,
                    "code": line_text[:100],  # Truncate
                    "description": pattern.description,
                    "cwe": pattern.cwe_id
                })
        
        return findings
    
    def get_pattern_count(self) -> int:
        """Return number of loaded patterns."""
        return len(self.patterns)
    
    def get_patterns_by_category(self, category: VulnerabilityCategory) -> List[HeuristicPattern]:
        """Get patterns in a specific category."""
        return [p for p in self.patterns if p.category == category]


# Singleton accessor
_scanner = None

def get_heuristic_scanner() -> HeuristicScanner:
    """Get the singleton heuristic scanner."""
    global _scanner
    if _scanner is None:
        _scanner = HeuristicScanner()
    return _scanner
