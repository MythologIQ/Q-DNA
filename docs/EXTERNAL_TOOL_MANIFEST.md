# Q-DNA External Tool Manifest

This manifest enumerates all external binaries, tools, and system dependencies required for the Q-DNA engine to operate in full sovereign mode.

## 1. Core Runtime

| Component  | Minimum Version | Criticality  | Usage                                                 |
| :--------- | :-------------- | :----------- | :---------------------------------------------------- |
| **Python** | 3.10+           | **Required** | Host runtime for MCP server and Sentinel engine.      |
| **Git**    | 2.30+           | **Required** | Version control integration for Diff/Commit tracking. |
| **SQLite** | 3.35+           | **Required** | Embedded SOA Ledger (usually bundled with Python).    |

## 2. Static Analysis Code (Tier 1)

These tools are invoked via `subprocess` by `sentinel_engine.py`.
| Tool | Package Source | Usage |
| :--- | :--- | :--- |
| **pylint** | `pip install pylint` | Fast static analysis for Python code. |
| **mypy** | `pip install mypy` | Static type checking for Python code. |

## 3. Formal Verification (Tier 3)

Required for L3 "High Risk" artifact verification (Phase 9).
| Tool | Installation | Usage |
| :--- | :--- | :--- |
| **Z3 Theorem Prover** | `pip install z3-solver` | Satisfiability Modulo Theories (SMT) solver for contract verification. |
| **CBMC** | [CBMC GitHub](https://github.com/diffblue/cbmc) | Bounded Model Checker for C/C++ (used via PyVeritas transpilation). |
| **PyVeritas** | _Internal/Proposed_ | Python-to-C transpiler for CBMC integration. |

## 4. Isolation & Environment

| Tool                  | Requirement          | Usage                                                       |
| :-------------------- | :------------------- | :---------------------------------------------------------- |
| **Docker** (Optional) | Docker Engine 20.10+ | Recommended for strict "Agent-as-a-Tool" sandbox isolation. |

## 5. Machine Learning (Phase 9)

| Model                | Size  | Usage                                              |
| :------------------- | :---- | :------------------------------------------------- |
| **all-MiniLM-L6-v2** | ~80MB | Sentence Embeddings for Semantic Drift Monitoring. |

## 6. Development Tools

| Tool        | Usage                                 |
| :---------- | :------------------------------------ |
| **fd**      | Fast file finding (Agent capability). |
| **ripgrep** | Fast text search (Agent capability).  |
