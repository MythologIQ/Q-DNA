# QoreLogic Product Requirements Document (PRD)

**Version:** 9.0 (Z3 Integration Active)
**Status:** Production Ready
**Last Updated:** December 22, 2025
**Research Foundation:** See [Research Library](./research/INDEX.md)

---

## 1. Executive Summary

QoreLogic (Quality DNA Engine) is a **local-first governance layer** for high-assurance AI-assisted code development. It addresses the fundamental unreliability of Large Language Models by implementing a multi-tier verification pipeline grounded in formal methods and probabilistic trust engineering.

### Core Value Proposition

| Problem                    | QoreLogic Solution               | Research Basis            |
| :------------------------- | :------------------------------- | :------------------------ |
| LLM hallucination (18-50%) | Multi-tier verification pipeline | HaluEval, TruthfulQA      |
| Cloud dependency           | Sovereign local execution        | Data sovereignty          |
| Static trust assumptions   | Dynamic reputation with decay    | RiskMetrics, EigenTrust   |
| Binary security            | Probabilistic risk grading       | HILS deterrence theory    |
| Audit opacity              | Merkle-chained transparency      | GDPR Art. 22, NIST AI RMF |

---

## 2. Strategic Objectives

### 2.1 Defect Reduction

**Target:** ~78% reduction in logic errors for L3 code
**Basis:** Fintech case study (defects: 4.82% → 1.06%) [ACCA System]

### 2.2 Compute Efficiency

**Target:** 80% cost savings vs. cloud Chain-of-Thought
**Mechanism:** Local quantized models (Phi-3 Mini, Gemma 2B) at <2GB RAM
**Basis:** HRM benchmarks [Research Library]

### 2.3 Data Sovereignty

**Target:** 100% local audit trail, keys, and reputation data
**Compliance:** GDPR, NIST AI RMF, ISO 42001 alignment

### 2.4 Hallucination Mitigation

**Target:** ≤1% hallucination rate (post-verification)
**Mechanism:** RAG + CoT + Span Verification + Sentinel
**Basis:** HaluEval baseline (18% → <1% with pipeline)

---

## 3. Target Environment

### 3.1 Hardware Constraints (Sovereign Fortress)

| Component         | Specification  | Constraint                |
| :---------------- | :------------- | :------------------------ |
| **Primary**       | Desktop/Laptop | i5/i7 gen 4-6, 8GB RAM    |
| **Edge**          | Raspberry Pi 4 | 4GB RAM, ARM CPU          |
| **Model Budget**  | <2GB           | Leaves ~1.5GB for runtime |
| **CPU Threshold** | 70%            | LEAN mode trigger         |

### 3.2 Software Stack

| Layer       | Technology           | Purpose                    |
| :---------- | :------------------- | :------------------------- |
| Protocol    | JSON-RPC 2.0 (MCP)   | Agent communication        |
| Transport   | stdio/HTTP/WebSocket | Transport agnostic         |
| Persistence | SQLite 3             | Merkle-chained ledger      |
| Inference   | Ollama/llama.cpp     | Local model execution      |
| Signing     | Ed25519              | Identity & non-repudiation |

---

## 4. Core Functional Requirements

### 4.1 The Sovereign Fortress (Infrastructure)

**SOA-Gate (MCP Gateway):**

- Exclusive gateway for ledger writes
- Deny-by-default security (DID whitelist)
- JSON-RPC 2.0 protocol with Pydantic schemas
- Backpressure at 80% queue capacity

**Isolation:**

- Port 8001 dedicated
- SQLite file locking
- No shared memory with other systems (e.g., Hearthlink)

### 4.2 The Sentinel (Verification Engine)

**Multi-Tier Verification Pipeline:**

| Tier | Method                                 | Scope    | Latency |
| :--- | :------------------------------------- | :------- | :------ |
| 1    | Static Analysis (Pylint, Flake8, MyPy) | All code | <0.5s   |
| 2    | Design by Contract (`deal` library)    | All code | <1.0s   |
| 3    | Formal Verification (PyVeritas → CBMC) | L3 code  | <5.0s   |

**Model Options:**

- Phi-3 Mini (q4_k_m): ~1.7GB RAM
- Gemma 2B (q4_k_m): ~1.2GB RAM
- HRM latent (27M): ~50MB RAM (future)

**Latency Target:** <0.2s per snippet (Tier 1), <1s full audit

### 4.3 The Judge (Policy Enforcement)

**Identity & Signing:**

- Ed25519 key pairs per agent
- 30-day key rotation (NIST SP 800-57)
- DID-based identity

**Merkle-Chain Ledger:**

- `hash(n) = SHA256(timestamp + payload + hash(n-1))`
- `signature = Ed25519_Sign(private_key, hash(n))`

**Remediation (HILS Model):**

- Micro-penalties: 0.5-2% per minor infraction (100% detection)
- Honest Error: 5% + 24h cooling-off
- Manipulation: 25% + 48h quarantine

### 4.4 Trust Dynamics Engine

**Source Credibility Index (SCI):**

- Range: 0-100
- Thresholds: ≥90 (Gold), 60-89 (Verify), 40-59 (Escalate), <35 (Block)
- Probationary period for new sources (5 verifications)

**Dynamic Decay (EWMA):**

- High-risk: λ = 0.94 (reactive)
- Low-risk: λ = 0.97 (stable)

**Transitive Trust:**

- Damping: δ = 0.5 per hop
- Max hops: 3

**Trust Stages (Lewicki-Bunker):**

- CBT (0.0-0.5): Probationary, 100% verification
- KBT (0.5-0.8): Standard, sampling verification
- IBT (>0.8): Trusted, expedited verification

---

## 5. Risk Grading System

### 5.1 Risk Levels

| Grade  | Definition               | Verification          | SLA         |
| :----- | :----------------------- | :-------------------- | :---------- |
| **L1** | Routine (typos, docs)    | Tier 1 + 10% sampling | Best effort |
| **L2** | Functional (API, UI)     | Tier 1 + Tier 2       | <5 minutes  |
| **L3** | Critical (auth, finance) | All tiers + Human     | <24 hours   |

### 5.2 Auto-Classification Rules

| Pattern                           | Force Level |
| :-------------------------------- | :---------- |
| `eval()`, `exec()`, `os.system()` | L3          |
| SQL without parameterization      | L3          |
| File I/O, network operations      | L2          |
| Documentation, formatting         | L1          |

---

## 6. Operational Modes

| Mode       | Trigger          | L1        | L2        | L3         |
| :--------- | :--------------- | :-------- | :-------- | :--------- |
| **NORMAL** | Default          | 100%      | 100%      | 100%       |
| **LEAN**   | CPU >70% (5 min) | 10%       | 100%      | 100%       |
| **SURGE**  | Queue >50        | Deferred  | 100%      | 100%       |
| **SAFE**   | Security event   | Suspended | Suspended | Human only |

---

## 7. Compliance Requirements

### 7.1 Regulatory Alignment

| Regulation       | Requirement             | Implementation       |
| :--------------- | :---------------------- | :------------------- |
| **GDPR Art. 22** | Right to human decision | L3 Human-in-the-Loop |
| **NIST AI RMF**  | Risk management         | SOA Ledger + modes   |
| **ISO 42001**    | AI management           | Audit log schema     |
| **CERT/CC**      | Disclosure timing       | 90-day policy        |

### 7.2 Audit Trail

Every action logged with:

- `event_id`, `timestamp`, `actor` (DID, model, trust score)
- `action`, `verification`, `governance` fields

---

## 8. Acceptance Criteria

| Metric              | Target    | Required Components           |
| :------------------ | :-------- | :---------------------------- |
| Hallucination Rate  | ≤1%       | RAG + CoT + Span + Sentinel   |
| Catch Rate          | ≥95%      | Sentinel verification         |
| False Positive Rate | ≤5%       | Enterprise SAST               |
| L3 SLA              | 100% <24h | Queue management              |
| L3 First Response   | <2 min    | Immediate ack                 |
| PII Leakage         | 0%        | Mandatory redaction           |
| Merkle Integrity    | 100%      | Hash verification             |
| Determinism         | Semantic  | Seed logging + drift tracking |

---

## 9. Shadow Genome (Failure Learning)

**Purpose:** Convert failures into training data for continuous improvement.

**Schema:**

```sql
shadow_genome (
    id, timestamp,
    input_context, generated_code,
    failure_mode, failure_detail,
    constraint_extracted
)
```

**Process:**

1. Failed verification → archive to Shadow Genome
2. Extract "Negative Constraint"
3. Feed constraint to future Sentinel training

---

## 10. Success Metrics

| Phase         | Metric                     | Target |
| :------------ | :------------------------- | :----- |
| Bootstrapping | Spec compliance            | ≥95%   |
| Pilot         | Catch rate on trap dataset | ≥8/10  |
| Production    | Defect reduction           | ≥50%   |
| Maturity      | Hallucination rate         | ≤1%    |

---

## 11. Research Foundation

This PRD is grounded in empirical research:

- **[LLM-002]** HaluEval hallucination benchmarks
- **[TRUST-001]** EigenTrust algorithm
- **[TRUST-004]** RiskMetrics decay factors
- **[BEHAV-001]** HILS deterrence research
- **[COMP-001]** GDPR Article 22
- **[MAC-002]** Model Context Protocol

See [Research Library](./research/INDEX.md) for full citations.

---

## Changelog

| Version | Date           | Changes                                                           |
| :------ | :------------- | :---------------------------------------------------------------- |
| 1.0     | 2025-12        | Initial draft                                                     |
| 1.2     | 2025-12        | Research standard                                                 |
| **2.0** | **2025-12-17** | **Empirically validated; full research integration**              |
| **9.0** | **2025-12-22** | **Version alignment with specification, Z3 integration complete** |
