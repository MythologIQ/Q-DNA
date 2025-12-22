# PyVeritas Integration Plan

**Version:** 1.0
**Created:** December 21, 2025
**Status:** ✅ IMPLEMENTED
**Blocking:** None - Ready for Testing

---

## Executive Summary

PyVeritas provides Python→C transpilation for CBMC-based formal verification. Given performance constraints on low-end machines, this implementation must support:

1. **Full Mode** - LLM-powered transpilation (requires GPU/high RAM)
2. **Lite Mode** - Pattern-based heuristics (CPU-only)
3. **Disabled Mode** - Skip formal verification entirely

---

## Parallel Development Tracks

### Track A: Configuration System (Est: 1 hour)

**Owner:** Can start immediately
**Dependencies:** None

| Task | Description                                               | File                 |
| ---- | --------------------------------------------------------- | -------------------- |
| A1   | Add `verification_config.py` with settings dataclass      | NEW                  |
| A2   | Add `formal_verification` section to `agents.json` schema | Schema update        |
| A3   | Wire config loading into SentinelEngine                   | `sentinel_engine.py` |

**Deliverable:** Configuration toggle: `{mode: "full"|"lite"|"disabled"}`

---

### Track B: Heuristic Fallback Engine (Est: 2 hours)

**Owner:** Can start immediately
**Dependencies:** None

| Task | Description                                              | File                          |
| ---- | -------------------------------------------------------- | ----------------------------- |
| B1   | Enhance `cbmc_verifier.py` with comprehensive heuristics | `cbmc_verifier.py`            |
| B2   | Add pattern library for common vulnerabilities           | `heuristic_patterns.py` (NEW) |
| B3   | Implement local AST-based bounds checking                | `ast_verifier.py` (NEW)       |

**Deliverable:** Functional Lite Mode that catches 60-70% of issues without LLM

---

### Track C: LLM Transpiler Service (Est: 4 hours)

**Owner:** Requires Ollama/LLM availability
**Dependencies:** Track A (config)

| Task | Description                                              | File                  |
| ---- | -------------------------------------------------------- | --------------------- |
| C1   | Create `pyveritas_transpiler.py` module                  | NEW                   |
| C2   | Implement Python→C transpilation prompts                 | Prompt engineering    |
| C3   | Add model selection (Qwen2.5-Coder preferred, fallbacks) | Config                |
| C4   | Implement output validation (compilable C check)         | GCC/Clang integration |
| C5   | Add MaxSAT fault localization (line mapping)             | Advanced              |

**Deliverable:** Full Mode transpilation with configurable LLM backend

---

### Track D: CBMC Container Integration (Est: 2 hours)

**Owner:** Docker/DevOps
**Dependencies:** None (parallel)

| Task | Description                                 | File              |
| ---- | ------------------------------------------- | ----------------- |
| D1   | Add CBMC binary to Docker image             | `Dockerfile.dist` |
| D2   | Create CBMC wrapper with timeout protection | `cbmc_wrapper.py` |
| D3   | Add resource limits (memory, CPU time)      | Docker/cgroups    |

**Deliverable:** Containerized CBMC with safety limits

---

### Track E: UI Settings Panel (Est: 1 hour)

**Owner:** Frontend
**Dependencies:** Track A (config schema)

| Task | Description                                          | File             |
| ---- | ---------------------------------------------------- | ---------------- |
| E1   | Add "Verification Settings" section to AgentsView    | `AgentsView.jsx` |
| E2   | Toggle for Full/Lite/Disabled modes                  | UI component     |
| E3   | Performance indicators (estimated verification time) | UX               |

**Deliverable:** User-controllable verification settings in Dashboard

---

## Dependency Graph

```
     Track A (Config)
        │
   ┌────┴────┐
   │         │
Track B   Track C ──── Track D
(Heuristic) (LLM)      (CBMC)
   │         │            │
   └────┬────┴────────────┘
        │
     Track E (UI)
        │
     ✅ Integration Complete
```

---

## Mode Specifications

### Full Mode (GPU/High RAM)

- **Requirements:** 8GB+ RAM, GPU recommended, Ollama running
- **LLM:** Qwen2.5-Coder (7B) preferred, fallback to smaller models
- **Process:** Python → LLM → C code → CBMC → Violations → Line mapping
- **Accuracy:** ~80-90% (per FORMAL_METHODS.md research)

### Lite Mode (CPU-Only)

- **Requirements:** 4GB RAM, no GPU
- **Process:** Python → AST analysis → Pattern matching → Heuristic violations
- **Accuracy:** ~60-70% (common patterns only)
- **Patterns:**
  - Division by zero (literal `/0` or variable-based)
  - Buffer overflows (list index beyond bounds)
  - Null pointer dereference (`None.method()`)
  - Integer overflow (explicit large values)
  - SQL injection patterns
  - Command injection patterns

### Disabled Mode

- **Requirements:** None
- **Process:** Skip formal verification, log warning
- **Accuracy:** 0% (user accepts risk)
- **Use Case:** CI/CD speed optimization, known-safe code

---

## Configuration Schema

```json
{
  "formal_verification": {
    "mode": "lite",
    "llm_endpoint": "http://localhost:11434/api/generate",
    "llm_model": "qwen2.5-coder:7b",
    "fallback_models": ["codellama:7b", "deepseek-coder:6.7b"],
    "timeout_seconds": 30,
    "cbmc_unwind_depth": 10,
    "enable_maxsat_localization": false
  }
}
```

---

## Implementation Order

**Phase 1 (Immediate - Parallel Start):**

- Track A: Configuration System
- Track B: Heuristic Fallback Engine
- Track D: CBMC Container Integration

**Phase 2 (After Phase 1):**

- Track C: LLM Transpiler Service

**Phase 3 (After All):**

- Track E: UI Settings Panel
- Integration Testing

---

## Success Criteria

| Criteria                                    | Metric             |
| ------------------------------------------- | ------------------ |
| Lite Mode catches division by zero          | Pass/Fail          |
| Lite Mode catches SQL injection             | Pass/Fail          |
| Full Mode transpiles simple Python function | Valid C output     |
| Full Mode + CBMC finds seeded bug           | Violation reported |
| User can toggle modes in Dashboard          | UI functional      |
| Low-perf machine runs without crash         | 4GB RAM test       |

---

## Risk Mitigation

| Risk                       | Mitigation                                    |
| -------------------------- | --------------------------------------------- |
| LLM produces invalid C     | Validate with `gcc -fsyntax-only` before CBMC |
| CBMC hangs on complex code | Timeout + kill after 30s                      |
| Out of memory              | Resource limits in Docker                     |
| User disables verification | Log warning, require explicit acknowledgment  |

---

## Files to Create

1. `local_fortress/mcp_server/verification_config.py` (Track A)
2. `local_fortress/mcp_server/heuristic_patterns.py` (Track B)
3. `local_fortress/mcp_server/ast_verifier.py` (Track B)
4. `local_fortress/mcp_server/pyveritas_transpiler.py` (Track C)
5. `local_fortress/mcp_server/cbmc_wrapper.py` (Track D)
6. Update: `dashboard/frontend/src/AgentsView.jsx` (Track E)

---

## Estimated Total Effort

| Track     | Effort       | Parallelizable            |
| --------- | ------------ | ------------------------- |
| A         | 1 hour       | Yes                       |
| B         | 2 hours      | Yes                       |
| C         | 4 hours      | After A                   |
| D         | 2 hours      | Yes                       |
| E         | 1 hour       | After A                   |
| **Total** | **10 hours** | **5 hours critical path** |

---

**Ready to proceed with Track A, B, D in parallel?**
