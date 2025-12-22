# QoreLogic: The Code DNA Engine Specification

**Version:** 9.0 (Formal Verification Active)
**Status:** Phase 9.0 Complete - Z3 Integration Active
**Last Updated:** December 22, 2025
**Audit Status:** Phase 8.5 Fully Verified; Phase 9.1 Z3 Operational
**Research Foundation:** See [Research Library](./research/INDEX.md) | [Design Validation](./research/synthesis/RESEARCH_VALIDATION.md)

---

## 1. Executive Summary

| Section            | Description                                                                                                                                                                              |
| :----------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Product Name**   | **QoreLogic: The Code DNA Engine** (Antigravity Extension)                                                                                                                               |
| **Project Type**   | **Research Initiative** (Not Commercial MVP)                                                                                                                                             |
| **Problem Solved** | Current agentic platforms prioritize velocity over correctness. We seek to establish **definitive results** through rigorous governance.                                                 |
| **Solution**       | QoreLogic implements the **Agent Accountability Contract (AAC)** using a **Hierarchical Reason Model (HRM)**. It bootstraps quality by identifying failure modes first ("Fail Forward"). |
| **Core Value**     | Establishes a **Verifiable System of Record** for autonomous development, with progressive formalization from heuristic to proof.                                                        |

---

## 2. Architectural Specification: The Sovereign Fortress

The QoreLogic extension operates as a **Verification Pipeline** that injects policy at critical stages of the Antigravity workflow. All verification and enforcement occurs on **local, sovereign hardware**.

### 2.1. The Sovereign Fortress Principle

Use high-power cloud models for creative "drafting" (Scrivener) while performing all critical verification and enforcement on local, private hardware (Sentinel & Judge). This ensures:

- **Data Sovereignty:** No private audit trails or IP leave local storage
- **Cost Efficiency:** Up to 80% reduction via local latent reasoning (per HRM vs. CoT benchmarks¹)
- **Resilience:** System operates even if cloud is unavailable

> ¹ _HRM efficiency benchmarks derived from comparative analysis of 27M-parameter recurrent models vs. 70B+ Transformer CoT on logic tasks (ARC-AGI, Sudoku). See Appendix C for citations._

### 2.2. The Hierarchical Reason Model (HRM)

The HRM uses two coupled recurrent modules for efficient reasoning:

| Module                    | Function                   | Characteristics                            |
| :------------------------ | :------------------------- | :----------------------------------------- |
| **H-Module** (High-Level) | Slow, abstract planning    | Orchestrates strategy, defines audit scope |
| **L-Module** (Low-Level)  | Fast, detailed computation | Executes checks, iterates on latent state  |

The logic is distributed across four specialized agent roles:

| Role          | Function                                                           | Model Type                                   | Location  |
| :------------ | :----------------------------------------------------------------- | :------------------------------------------- | :-------- |
| **Scrivener** | Generates code, proposes risk grades, attaches verification labels | Large LLM (Cloud)                            | Remote    |
| **Sentinel**  | Low-latency Formal Verification, citation checks, safety scans     | Micro-HRM (27M params, ~1K training samples) | **Local** |
| **Judge**     | Manages SOA Ledger, applies penalties, enforces quarantine         | MCP Controller/Middleware                    | **Local** |
| **Overseer**  | Final approval on L3/Divergence cases                              | Human                                        | **Local** |

### 2.3. Agent-as-a-Tool Pattern

To prevent context contamination between co-located systems:

- **Encapsulation:** Sentinel runs as an isolated `AgentTool` in its own environment (Docker/process)
- **Interface:** Returns only `PASS/FAIL` verdict + rationale to the Scrivener
- **Isolation:** Prevents formal logic from leaking into other memory stores

### 2.4. Policy Files

| File                                   | Purpose                                           |
| :------------------------------------- | :------------------------------------------------ |
| `config/rules/core_governance.md`      | AAC Core: Divergence Doctrine, Remediation Tracks |
| `config/rules/risk_grading.md`         | L1/L2/L3 classification matrix                    |
| `config/rules/citation_policy.md`      | Transitive Cap, Quote Context, Reference Tiers    |
| `config/workflows/verify_qorelogic.md` | MCP tool invocation workflow                      |

### 2.5. Communication Protocol

Per Multi-Agent Coordination research [MAC-002], QoreLogic uses **JSON-RPC 2.0** as the native protocol:

| Property  | Specification                  | Rationale                             |
| :-------- | :----------------------------- | :------------------------------------ |
| Protocol  | JSON-RPC 2.0 (MCP-compatible)  | Transport-agnostic, low overhead      |
| Transport | stdio / HTTP / WebSocket       | Flexible deployment                   |
| Schema    | Pydantic models                | Type safety, validation               |
| Semantics | `method` field as performative | `agent.request`, `agent.inform`, etc. |

> _JSON-RPC provides 40%+ overhead reduction vs. FIPA-ACL while maintaining semantic richness through strict schemas._

#### 2.5.1. Backpressure Mechanism

To prevent queue overload (per SRE research [SRE-001]):

| Threshold                | Value         | Action              |
| :----------------------- | :------------ | :------------------ |
| Queue bound              | 50 requests   | Maximum pending     |
| Warning                  | 80% capacity  | Backpressure signal |
| Load shedding            | 100% capacity | Reject new requests |
| Queue type (interactive) | LIFO          | Process most recent |
| Queue type (batch)       | FIFO          | Process in order    |

### 2.6. Edge Deployment Constraints

For edge deployment (Raspberry Pi 4):

| Resource     | Limit              | Rationale                |
| :----------- | :----------------- | :----------------------- |
| Total RAM    | 4GB                | Hardware constraint      |
| Model budget | <2GB               | Leaves ~1.5GB runtime    |
| CPU          | ARM (no GPU)       | Local CPU inference      |
| Framework    | uAgents (Fetch.ai) | Minimal memory footprint |

**Recommended Models:**

- Phi-3 Mini (q4_k_m): ~1.7GB
- Gemma 2B (q4_k_m): ~1.2GB

---

## 3. The Verification Lifecycle

Transforming a speculative Code Diff into a Verified Asset:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  PROPOSAL   │───▶│  CHALLENGE  │───▶│  CONSENSUS  │───▶│   COMMIT    │
│ (Scrivener) │    │  (Sentinel) │    │   (Judge)   │    │  (Ledger)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                  │                  │                  │
      ▼                  ▼                  ▼                  ▼
   Conditional        PASS/FAIL         Sign/Reject        Verified
   + Risk Grade       + Rationale       + Penalty          or Quarantined
```

### 3.1. Stages

1. **Proposal:** Scrivener submits Code Diff + Risk Grade Rationale. Status: `CONDITIONAL`.
2. **Challenge:** Sentinel executes all applicable checks. Returns `PASS`, `FAIL`, or `L3_REQUIRED`.
3. **Defense:** If `FAIL`, Scrivener revises. Failure archived to Shadow Genome.
4. **Consensus:** Judge validates Sentinel verdict. Signs artifact if `PASS`.
5. **Final Status:** Written to SOA Ledger with one of: `VERIFIED`, `VERIFIED_FALSE`, `CONDITIONAL`, `UNKNOWN`, or `QUARANTINED`.

### 3.1.1. Verification Status Definitions

| Status           | Description                                      |
| :--------------- | :----------------------------------------------- |
| `VERIFIED`       | Passed all checks, claim is true                 |
| `VERIFIED_FALSE` | Passed checks, claim is provably false           |
| `CONDITIONAL`    | Pending required checks or evidence              |
| `UNKNOWN`        | Cannot determine truth value with available data |
| `QUARANTINED`    | Blocked due to policy violation or manipulation  |

### 3.2. Sentinel Check Matrix

| Check                     | L1  | L2  | L3  | Implementation                                   |
| :------------------------ | :-: | :-: | :-: | :----------------------------------------------- |
| Secret Detection          |  ✓  |  ✓  |  ✓  | Regex patterns for API keys, passwords           |
| Unsafe Function Detection |  ✓  |  ✓  |  ✓  | `eval`, `exec`, `os.system`, etc.                |
| PII Detection & Redaction |  ✓  |  ✓  |  ✓  | SSN, email, credit card patterns                 |
| Cyclomatic Complexity     |  -  |  ✓  |  ✓  | AST-based McCabe analysis (C ≤ 10)               |
| Transitive Citation Cap   |  -  |  ✓  |  ✓  | Max depth 2                                      |
| Quote Context Rule        |  -  |  ✓  |  ✓  | ±2 sentences or 200 chars                        |
| SQL Injection Detection   |  -  |  -  |  ✓  | f-string/concat in queries                       |
| Bounded Model Checking    |  -  |  -  |  ✓  | Symbolic execution (CBMC/ESBMC, 5-10 step bound) |
| Volatility TTL Check      |  -  |  ✓  |  ✓  | Re-verify stale claims                           |
| Concurrency Safety        |  -  |  -  |  ✓  | Deadlock/Race condition detection (FV)           |
| False Positive Triage     |  -  |  ✓  |  ✓  | LLM-based context filter (cuts FP by 90%)²       |

> ² _Datadog engineering reports LLM-based SAST triage reduces false positives by ~90% while maintaining detection rates._

### 3.3. Multi-Tier Verification Pipeline

Per LLM Reliability research [LLM-001], verification uses a **defense-in-depth** approach with three tiers:

| Tier  | Method              | Tools                                | Latency | Scope    |
| :---- | :------------------ | :----------------------------------- | :------ | :------- |
| **1** | Static Analysis     | Pylint, Flake8, MyPy                 | <0.5s   | All code |
| **2** | Design by Contract  | `deal` library (pre/post conditions) | <1.0s   | All code |
| **3** | Formal Verification | PyVeritas → CBMC, CrossHair          | <5.0s   | L3 only  |

#### 3.3.1. Tier-by-Risk-Grade

| Risk   |         Tier 1         | Tier 2 | Tier 3 |
| :----- | :--------------------: | :----: | :----: |
| **L1** | ✓ (10% sample in LEAN) |   -    |   -    |
| **L2** |           ✓            |   ✓    |   -    |
| **L3** |           ✓            |   ✓    |   ✓    |

#### 3.3.2. Tier 2: Design by Contract

The `deal` library enforces formal contracts on Python functions:

```python
import deal

@deal.pre(lambda x: x > 0)
@deal.post(lambda res: res > x)
def heavy_compute(x):
    ...
```

- **Pre-conditions:** Input requirements
- **Post-conditions:** Output guarantees
- **Invariants:** Class-level constraints
- **Integration:** Connects to Z3 for formal verification

#### 3.3.3. Tier 3: Formal Verification

For L3 code, mathematical proof is required:

| Tool          | Method                            | Accuracy |
| :------------ | :-------------------------------- | :------- |
| **PyVeritas** | Python → C transpilation + CBMC   | ~80-90%  |
| **CrossHair** | Symbolic execution on Python (Z3) | Backup   |
| **CBMC**      | Bounded Model Checking            | External |

> _PyVeritas achieves 80-90% accuracy on formal verification by transpiling Python to C and running CBMC._

---

## 4. Risk Grading and Classification

| Grade  | Description                | Trigger Examples               | Verification Strategy         | SLA     |
| :----- | :------------------------- | :----------------------------- | :---------------------------- | :------ |
| **L1** | Low impact, routine        | Typos, variable renames, docs  | Lean Mode (sampling)          | <1 min  |
| **L2** | Medium impact, uncertainty | API integration, UI refactor   | Balanced (full Sentinel pass) | <5 min  |
| **L3** | High impact, critical      | Auth, DB migration, encryption | High Assurance (BMC + Human)  | <24 hrs |

### 4.1. Auto-Classification Rules

- File path contains `auth`, `login`, `password`, `payment`, `encrypt`, `migration` → **L3**
- Content contains `CREATE TABLE`, `def authenticate`, `AES`, `bcrypt` → **L3**
- Any **functional code** change (logic, control flow, data transformation) → Minimum **L2**
- **Non-code changes only** (documentation, comments, whitespace, typos) → **L1**

### 4.2. Fallback Rules

- If Sentinel unavailable → Judge raises grade by one level
- If L3 and Overseer unavailable → Block until approval

---

## 5. Evidence and Citation Policy

### 5.1. Reference Tier Hierarchy

| Tier   | Description                    | Credibility | Examples                         |
| :----- | :----------------------------- | :---------: | :------------------------------- |
| **T1** | Formal Proofs, Primary Records |    100%     | RFCs, IEEE specs, signed commits |
| **T2** | Reviewed Standards             |     90%     | OWASP, MISRA, textbooks          |
| **T3** | Reputable Reporting            |     70%     | Major tech publications          |
| **T4** | Community/Generative           |     40%     | Stack Overflow, LLM output       |

### 5.2. Integrity Rules (Zero-Assumption Protocol)

- **Transitive Cap:** Citation depth ≤ 2 from primary source
- **Quote Context:** ±2 sentences or 200 chars minimum
- **Paywall Policy:** Checksummed excerpt required if paywalled
- **AI Content:** Cite the verified source, not the AI
- **Tool Parity:** Down-weight votes from agents lacking verification tools

### 5.3. Source Credibility Index (SCI)

Judge maintains SCI scores (0-100) per source domain. Trust is non-linear; the "Trust Plateau" collapses rapidly below specific thresholds⁹.

#### 5.3.1. SCI Thresholds

| Threshold                 | SCI Level | Action State         | Rationale                                                  |
| :------------------------ | :-------- | :------------------- | :--------------------------------------------------------- |
| **Gold Standard**         | ≥ 90      | Auto-Accept          | T1/T2 equivalent; error probability lower than human noise |
| **Verification Required** | 60 – 89   | Sentinel Audit       | "Probabilistic Zone" – metadata cross-referencing required |
| **Human-in-the-Loop**     | 40 – 59   | Escalate to Overseer | Below 60%, humans perceive sources as "unreliable"         |
| **Hard Rejection**        | < 35      | Block Claim          | T4 floor; high risk of hallucination or data injection     |

> _Note: Hard Rejection threshold lowered from 40 to 35 to prevent immediate blocking of new sources after a single failure. (See RESEARCH_VALIDATION.md §3.1.2)_

#### 5.3.2. Initialization Scheme (Burden of Proof)

New sources use **Tier-Based Anchoring with Probationary Period**:

| Source Type                | Initial SCI          | Probation             | Rationale                               |
| :------------------------- | :------------------- | :-------------------- | :-------------------------------------- |
| Uncategorized Domain       | **45** (T4 + buffer) | First 5 verifications | Buffer prevents single-failure blocking |
| Identified T3 (journalism) | **60** (T3 floor)    | First 3 verifications | Anchored at tier floor                  |
| Identified T2 (standards)  | **75** (T3 ceiling)  | First 3 verifications | Earned promotion to 90 after validation |

**Probationary Rules:**

- During probation, SCI cannot drop below 35 (Hard Rejection threshold)
- After probation ends, full adjustment formula applies
- Probation expires after N verifications OR 30 days of activity

> _Adapts the Wikipedia "autoconfirmed" model: time-based + activity-based gates filter >90% of impulsive bad actors. (See RESEARCH_VALIDATION.md §6.3)_

#### 5.3.3. Adjustment Formula

Credibility is **hard to earn, easy to lose** via Asymmetric Weighting (EMA with penalty):

```
SCI_new = α × SCI_old + (1 - α) × (Verification × ω)
```

| Parameter    | Value   | Description                                              |
| :----------- | :------ | :------------------------------------------------------- |
| α (memory)   | **0.8** | Retains historical performance while adapting to recent  |
| ω (positive) | **1.0** | Standard weight for validated claims                     |
| ω (negative) | **1.5** | "Trust Penalty" – failures hurt more than successes help |

**Temporal Decay:** SCI drifts toward Tier baseline by 1 point per 30 days of inactivity (reflects domain ownership volatility).

**Context-Based Decay (per RiskMetrics [TRUST-004]):**

For agent trust scores (distinct from SCI), decay factor λ varies by context:

| Context           | λ (decay) | Behavior                           |
| :---------------- | :-------- | :--------------------------------- |
| High-risk tasks   | **0.94**  | Reactive; recent failures dominate |
| Advisory/low-risk | **0.97**  | Stable; tolerates minor variance   |

> _λ=0.94 places ~95% weight on the last 60 observations, ensuring rapid response to performance changes._

#### 5.3.4. Domain-Specific Modifiers

| Claim Type                  | Modifier                | Rationale                                  |
| :-------------------------- | :---------------------- | :----------------------------------------- |
| Syntax/Documentation        | Standard SCI            | High tolerance for functional claims       |
| Security/Cryptographic (L3) | SCI × 0.75              | 80 treated as 60; requires T1 verification |
| Performance Benchmarks      | Requires 2× T3 stacking | Empirical claims need corroboration        |

> ⁹ _Sources: Lazer et al. (2018) "The science of fake news"; Gupta et al. (2014) "TweetCred"; Metzger (2007) "Making sense of credibility on the Web". Industry: NewsGuard (60 = unreliable), Wikipedia RS (Reliable/Semi-reliable/Deprecated = 90/60/40), NIST SP 800-161._

#### 5.3.5. Transitive Trust

When Agent A hasn't directly interacted with Agent C, trust propagates through intermediaries with damping (per EigenTrust [TRUST-001]):

```
Trust_{A→C} = Trust_{A→B} × Trust_{B→C} × δ
```

| Parameter          | Value   | Rationale                                         |
| :----------------- | :------ | :------------------------------------------------ |
| δ (damping factor) | **0.5** | Trust halves at each hop                          |
| Max hops           | **3**   | Dunbar research; trust evaporates beyond 3-4 hops |

**Implementation Note:** QoreLogic implements a "Hybrid Trust Model" that combines EigenTrust global influence with Local Trust path products for transaction validation. This provides Sybil resistance while maintaining practical performance characteristics.

**Sybil Resistance:**

- Transitive damping prevents reputation inflation
- Hop limit prevents distant collusion networks
- Trust anchors (Overseer) provide ground truth

#### 5.3.6. Lewicki-Bunker Trust Stages

Agent trust scores map to behavioral stages (per trust dynamics research [TRUST-002]):

| Stage | Name                             | Score Range | QoreLogic Behavior              |
| :---- | :------------------------------- | :---------- | :------------------------------ |
| **1** | Calculus-Based Trust (CBT)       | 0.0 – 0.5   | Probationary; 100% verification |
| **2** | Knowledge-Based Trust (KBT)      | 0.5 – 0.8   | Standard; sampling verification |
| **3** | Identification-Based Trust (IBT) | > 0.8       | Trusted; expedited verification |

**Stage Transitions:**

- CBT → KBT: Sustained positive interactions demonstrating predictability
- KBT → IBT: Alignment of goals and values (rare for agents)
- **Violation Impact:** Any trust violation demotes by at least one stage

### 5.4. Volatility Time-To-Live (TTL)

Claims are subject to automatic expiration based on domain volatility:

| Data Type                 | TTL Duration | Action on Expiry           |
| :------------------------ | :----------- | :------------------------- |
| Leadership/Financial Data | 24 Hours     | Immediate Refresh Trigger  |
| Pricing/Market Data       | 72 Hours     | Stale-While-Revalidate     |
| General Code/Technical    | 30 Days      | Background Re-verification |

---

## 6. Evolutionary Bootstrapping (Fail Forward)

### 6.1. Philosophy

We do not build a perfect system from scratch. We build a system designed to **detect its own imperfections**.

- **Failure is Data:** A failed verification is as valuable as a pass.
- **Negative Reinforcement:** Sentinel learns from archived failures, not infinite "good" examples.
- **Recursive Constraint:** Each failure adds a new rule to prevent recurrence.

#### 6.1.1. Fail Forward as Discovery Mechanism

Structured failure analysis is not pessimism — it is a **generative process**.

The methodology:

1. **Surface-level reasoning** produces an initial solution (Plan A).
2. **Adversarial review** exposes first-order failure modes.
3. **Contingency planning** exposes second-order failures (problems created by solutions).
4. **Deep tracing** of those failures surfaces **superior architectures** invisible from the naive starting position.

> _The path **through** anticipated failure yields better solutions than the path **around** it._

This principle applies to all QoreLogic development:

| Phase        | Action                                     | Outcome                       |
| :----------- | :----------------------------------------- | :---------------------------- |
| Proposal     | Present initial architecture               | Candidate solution            |
| Adversarial  | "What could fail?"                         | First-order risks             |
| Contingency  | "How do we handle those failures?"         | Mitigations                   |
| Second-Order | "What problems do mitigations create?"     | Hidden costs revealed         |
| Synthesis    | "What architecture avoids these entirely?" | **Superior solution emerges** |

**Key Insight:** The superior solution (discovered after multi-depth analysis) often differs structurally from the initial proposal. This is not failure of the initial proposal — it is **proof that the process works**.

> _Exhaustive failure analysis creates the cognitive pressure that surfaces emergent architectures._

#### 6.1.2. Depth Calibration

Failure analysis depth should scale proportionally with decision complexity. Over-analysis of routine tasks wastes resources; under-analysis of architectural decisions invites costly rework.

| Task Type               | Recommended Depth | Rationale                                                    |
| :---------------------- | :---------------- | :----------------------------------------------------------- |
| Architectural decisions | 3+ levels         | High structural impact; cost of error is weeks/months        |
| New feature design      | 2 levels          | Moderate impact; standard contingencies + second-order check |
| Routine implementation  | 1 level           | Known patterns; test coverage provides feedback              |
| Bug fixes / refactors   | Minimal           | Localized scope; regression tests catch errors               |

> _Principle: Fail Forward depth ∝ decision complexity_

### 6.2. Multi-Pass Generation

For any task, the system generates **multiple candidate variants**:

1. **Generate:** Scrivener produces N variants (N ≥ 2)
2. **Evaluate:** Sentinel scores each variant on fitness metrics
3. **Select:** Best-scoring variant proceeds
4. **Archive:** Non-optimal variants stored in Shadow Genome
5. **Recall:** Archived variants can be retrieved if conditions change

### 6.3. Fitness Scoring

| Factor     | Weight | Measurement                      |
| :--------- | :----: | :------------------------------- |
| Audit Pass |   50   | Binary: Pass/Fail                |
| Complexity |   20   | Inverse of cyclomatic complexity |
| Latency    |   10   | Faster = better                  |
| Novelty    |   10   | Unique content hash              |
| L3 Clean   |   10   | L3 without failures              |

### 6.4. Shadow Genome Schema

```sql
CREATE TABLE shadow_genome (
    genome_id INTEGER PRIMARY KEY,
    input_vector TEXT,        -- The code/claim that failed
    context JSON,             -- Environment, task, fitness
    failure_mode TEXT,        -- INJECTION, HARDCODED_SECRET, etc.
    causal_vector TEXT,       -- Why it failed
    remediation_status TEXT,  -- UNRESOLVED, RESOLVED, WONT_FIX
    timestamp TIMESTAMP
);
```

---

## 7. Bias, Drift, and Manipulation Controls

### 7.1. Continuous Detection

| Monitor                    | Purpose                        | Trigger                  |
| :------------------------- | :----------------------------- | :----------------------- |
| **Semantic Drift**         | Track concept embedding shifts | Cosine similarity < 0.85 |
| **Echo/Paraphrase**        | Detect source exhaustion       | N-gram overlap > 60%     |
| **Confidence Calibration** | Brier Score monitoring         | Error > 0.2              |
| **Early Cross Check**      | Extraction mismatch detection  | Before full debate stage |

> _Thresholds (0.85, 60%, 0.2) are configurable defaults based on standard ML calibration practices._

### 7.2. Debate and Diversity

- **Diversity Quorum:** L3 requires agreement from ≥2 model families
- **Minority Rescue:** +30% weight boost for minority claims citing T1/T2 sources
- **Adversarial Review:** Devil's advocate pass on L3 proposals

### 7.3. Behavioral Guards

- **Decision Lock:** Judge cannot reverse without T1 override evidence
- **Incentive Guard:** Penalizes speed > accuracy (latency bonus capped)
- **Context Decay:** Old context weighted less than recent
- **Debate Saturation:** Quarantine after N rounds of unproductive debate
  - _N is system-calculated based on variance reduction per round_
  - _User has transparency into N value and manual override capability_
  - _Default: N = 3 if no variance signal available_

---

## 8. Divergence and Disclosure Protocol

### 8.1. The Divergence Doctrine

When **Objective Truth** conflicts with **User Protection**, or when technically valid data raises ethical concerns:

1. **Trigger:** Truthful disclosure risks physical/financial/emotional harm, OR data is valid but ethically problematic (e.g., protected class data in decision logic)
2. **Classify:** Auto-escalate to L3
3. **Log:** Record verified facts to SOA Ledger BEFORE any framing
4. **Disclose:** Default to truth with safety caveats

> _Ethical review at the micro level is relevant: a step may pull technically valid, verifiably sourced data, but the quality and viability of said data being pristine does not preclude ethical blockers to flawed logic._

### 8.2. Deferral Windows

| Risk Type               | Max Deferral    |
| :---------------------- | :-------------- |
| Safety Critical         | 4 hours         |
| Medical/Legal/Financial | 24 hours        |
| Reputational            | 72 hours        |
| Low Risk                | 0 (no deferral) |

### 8.3. Staged Disclosure

1. **Phase 1 (<2 min):** Safe guidance, no speculation
2. **Phase 2 ("Comfort Layer"):** Full truth after risk mitigation

### 8.4. Comfort Layer Definition

The **Comfort Layer** is supportive framing provided _only after_ verified facts are recorded in the SOA Ledger:

- **Permitted:** Empathetic context, coping resources, next-step guidance
- **Prohibited:** Falsehood, suppression, minimization of verified facts
- **Timing:** Never before truth; always as a supplement

### 8.5. Vulnerability Disclosure Policy

Per AI Governance research [COMP-004], QoreLogic adopts the **Google Project Zero standard**:

| Phase          | Timeline  | Action                                    |
| :------------- | :-------- | :---------------------------------------- |
| Acknowledgment | 24 hours  | Confirm receipt of report                 |
| Triage         | 7 days    | Assess severity and scope                 |
| Remediation    | 0-83 days | Develop and test fix                      |
| Disclosure     | Day 90    | Public disclosure (or earlier if patched) |

> _The 90-day timeline provides sufficient time for complex AI vulnerabilities requiring model retraining or architectural changes._

### 8.6. Regulatory Compliance

QoreLogic aligns with major AI governance frameworks (per [COMP-001], [COMP-002], [COMP-003]):

| Regulation       | Requirement                      | QoreLogic Implementation         |
| :--------------- | :------------------------------- | :------------------------------- |
| **GDPR Art. 22** | Right to non-automated decisions | L3 Human-in-the-Loop mandatory   |
| **GDPR Art. 33** | 72-hour breach notification      | Immediate escalation workflow    |
| **NIST AI RMF**  | Govern, Map, Measure, Manage     | SOA Ledger + operational modes   |
| **ISO 42001**    | AI Management Systems            | Audit log schema + documentation |
| **CERT/CC**      | Disclosure timing                | 90-day policy (see 8.5)          |

**GDPR Art. 22 Detection:**

- System auto-detects "Legal Effect" decisions (employment, credit, health)
- Triggers mandatory L3 escalation
- Logged in audit trail with `gdpr_art22_trigger` flag

---

## 9. Remediation Tracks

> _Design Principle: **HILS (High Inspection/Low Severity)** is superior to LIHS. Frequent, small, automated penalties create tighter feedback loops than infrequent severe actions. (See RESEARCH_VALIDATION.md §3.2)_

### 9.1. Micro-Penalty Layer (Automated)

| Infraction              | Detection      | Penalty     | Frequency       |
| :---------------------- | :------------- | :---------- | :-------------- |
| Schema violation        | 100% automated | 0.5% weight | Per occurrence  |
| API misuse              | 100% automated | 0.5% weight | Per occurrence  |
| Stale citation          | 100% automated | 1% weight   | Per occurrence  |
| Minor calibration drift | Continuous     | 2% weight   | Daily aggregate |

> _Rationale: 100% detection of minor infractions prevents "Gambler's Fallacy" risk-seeking behavior._

### 9.2. Honest Error Track

- **Trigger:** Calibration error > 0.2, logic gaps, repeated micro-penalties
- **Penalty:** 5% influence weight reduction
- **Action:** Context flush, retraining on failure examples
- **Cooling-Off:** 24-hour reduced activity period

### 9.3. Manipulation Track

- **Trigger:** Hash chain tampering, citation fabrication, gaming
- **Penalty:** 25% influence weight reduction
- **Action:** 48-hour quarantine, full re-audit of recent work
- **Cooling-Off:** Mandatory 24-hour period before trust repair begins

> _Per Lewicki-Bunker model: Cooling-off periods reduce retaliation and enable rational re-engagement._

### 9.4. Reputation Recovery

Recovery follows asymmetric dynamics (hard to earn, easy to lose):

| State               | Recovery Rate         | Conditions                                        |
| :------------------ | :-------------------- | :------------------------------------------------ |
| After Micro-Penalty | +0.5% per clean audit | Automatic                                         |
| After Honest Error  | +1% per clean audit   | After 24h cooling-off                             |
| After Manipulation  | +0.5% per clean audit | After 48h quarantine + 3 consecutive clean audits |

- **Starting Weight:** All agents begin at `1.0` influence weight
- **Maximum Weight:** 2.0x (earned through consistent integrity)
- **Minimum Weight:** 0.1x (not 0.0x; allows recovery path)
- **Probationary Floor:** New agents in probation cannot exceed 1.2x

---

## 10. Privacy and Data Protection

### 10.1. Core Rules

| Rule                 | Implementation                                     |
| :------------------- | :------------------------------------------------- |
| PII Redaction        | Mandatory before logging. Patterns: SSN, CC, Email |
| Data Minimization    | Store hashes/references, not raw content           |
| Differential Privacy | ε budget ledger for sensitive joins (see 10.3)     |
| Privacy Join Risk    | Block joins that exceed ε budget                   |
| Content Truncation   | Max 2000 chars stored per variant                  |

### 10.2. Identity and Signing

| Requirement         | Implementation                   |
| :------------------ | :------------------------------- |
| Agent DIDs          | `did:myth:{role}:{nonce}` format |
| Signature Algorithm | Ed25519                          |
| Key Storage         | Local encrypted keyfile          |
| Key Rotation        | Required every 30 days           |

### 10.3. Differential Privacy (ε Budget)

The ε (epsilon) parameter represents "privacy loss." Smaller ε provides stronger privacy but introduces more noise, potentially degrading verification accuracy.

#### Initial Budget

| Parameter  | Value                                | Justification                                          |
| :--------- | :----------------------------------- | :----------------------------------------------------- |
| Starting ε | **2.0** per 24-hour window per agent | Balances privacy (e²≈7.38 bound) with utility          |
| Scope      | Per-agent, capped by global odometer | Prevents single compromised agent from draining system |

> _Industry Benchmarks: Apple (ε=2-16), US Census 2020 (ε≈19.1), Google RAPPOR (ε=1-9)⁸_

#### ε Consumption Model

Consumption scales with operation sensitivity (Δf) and risk grade:

| Operation Type               | Sensitivity | ε Cost | Justification                              |
| :--------------------------- | :---------- | :----- | :----------------------------------------- |
| L1: Ledger Summary           | Low         | 0.05   | Simple COUNT/AVG of non-sensitive metadata |
| L2: Reputation Aggregation   | Medium      | 0.20   | Cross-referencing multiple agent actions   |
| L3: Code Pattern Match       | High        | 0.80   | Risk of leaking proprietary logic or PII   |
| Full-Text Search (Unindexed) | Critical    | 1.50+  | Heavy Laplacian noise required             |

#### Threshold and Blocking

| ε Remaining         | State            | Action                                                                           |
| :------------------ | :--------------- | :------------------------------------------------------------------------------- |
| ε ≥ 0.5             | Normal           | Standard operation                                                               |
| 0.2 ≤ ε < 0.5       | **Soft Warning** | Privacy Throttling flag; noise injection doubled                                 |
| ε < 0.1             | **Hard Block**   | Non-critical queries rejected (`PRIVACY_EXHAUSTED`)                              |
| ε = 0 + L3 Critical | **Emergency**    | Judge authorizes "Privacy Debt" (logged to SOA Ledger, triggers immediate audit) |

#### Refresh Mechanism (Reset & Decay)

| Policy           | Value                      | Rationale                                                 |
| :--------------- | :------------------------- | :-------------------------------------------------------- |
| Reset Period     | Daily (00:00 UTC)          | Simplifies tracking on resource-constrained hardware      |
| Rollover         | None                       | Prevents "super-budget" accumulation enabling mass scrape |
| Privacy Odometer | Monotonic lifetime counter | Identifies consistently "privacy-hungry" agents           |

#### Local Implementation

```sql
-- Privacy Budget Tracking (SQLite)
CREATE TABLE privacy_ledger (
    entry_id INTEGER PRIMARY KEY,
    agent_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    epsilon_spent REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Budget Check Query
SELECT SUM(epsilon_spent) FROM privacy_ledger
WHERE agent_id = ? AND timestamp > date('now');
```

> _Overhead: <1% CPU. Libraries: Google `differential-privacy` or IBM `diffprivlib`._
>
> ⁸ _Sources: Dwork (2006) "Differential Privacy"; Apple DP Team (2017) "Learning with Privacy at Scale"; Abowd (2018) "US Census Bureau Adopts Differential Privacy"_

---

## 11. Persistence Layer (SOA Ledger)

### 11.1. Merkle Chain Integrity

Every ledger entry contains:

- `entry_hash = SHA256(timestamp + did + payload + prev_hash)`
- `signature = Ed25519_Sign(private_key, entry_hash)`

### 11.2. Schema

```sql
-- Agent Identity Registry
CREATE TABLE agent_registry (
    did TEXT PRIMARY KEY,
    public_key TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('Scrivener', 'Sentinel', 'Judge', 'Overseer')),
    influence_weight REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SOA Ledger (Append-Only)
-- NOTE: agent_did may be NULL only for GENESIS_AXIOM (root event without agent)
CREATE TABLE soa_ledger (
    entry_id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent_did TEXT,  -- NULL permitted only for GENESIS_AXIOM
    model_version TEXT,         -- Model used for this action (v2.3+)
    trust_score REAL,           -- Agent trust score at time of action (v2.3+)
    event_type TEXT NOT NULL,
    risk_grade TEXT CHECK(risk_grade IN ('L1', 'L2', 'L3')),
    payload JSON NOT NULL,
    verification_method TEXT,   -- Tier 1/2/3 or NULL (v2.3+)
    verification_result TEXT,   -- PASS/FAIL or NULL (v2.3+)
    gdpr_art22_trigger BOOLEAN DEFAULT FALSE,  -- Legal effect detection (v2.3+)
    human_approver TEXT,        -- DID of human approver if escalated (v2.3+)
    entry_hash TEXT UNIQUE NOT NULL,
    prev_hash TEXT NOT NULL,
    signature TEXT NOT NULL,
    FOREIGN KEY (agent_did) REFERENCES agent_registry(did)
);

-- Reputation History
CREATE TABLE reputation_log (
    log_id INTEGER PRIMARY KEY,
    agent_did TEXT,
    adjustment REAL NOT NULL,
    reason TEXT NOT NULL,
    ledger_ref_id INTEGER,
    FOREIGN KEY (agent_did) REFERENCES agent_registry(did),
    FOREIGN KEY (ledger_ref_id) REFERENCES soa_ledger(entry_id)
);
```

### 11.3. Event Types

| Event                     | Description                        |
| :------------------------ | :--------------------------------- |
| GENESIS_AXIOM             | Root of the chain                  |
| PROPOSAL                  | Scrivener submits code             |
| AUDIT_PASS / AUDIT_FAIL   | Sentinel verdict                   |
| L3_APPROVAL_REQUEST       | Waiting for Overseer               |
| L3_APPROVED / L3_REJECTED | Overseer decision                  |
| PENALTY / REWARD          | Weight adjustment                  |
| COMMIT                    | Final verification                 |
| QUARANTINE                | Blocked artifact                   |
| GENERATION_COMPLETE       | Bootstrapping cycle                |
| SHADOW_RECALL             | Archived variant retrieved         |
| OVERRIDE                  | Judge reversal with T1 evidence    |
| TTL_BREACH                | Stale data triggered re-validation |
| COACHING                  | Honest Error Track remediation     |
| HASH_TAMPERING            | Step hash mismatch detected        |
| SUPERVISED_RERUN          | Triggered by hash chain break      |

### 11.4. Step Hashing (Chain-of-Thought Hygiene)

Every reasoning step in the Scrivener's chain is hashed to detect tampering:

- `step_hash = SHA256(step_index + content + prev_step_hash)`
- Breaks or mismatches trigger `HASH_TAMPERING` event and `SUPERVISED_RERUN`
- **Relevance Filter:** Sentinel removes steps that add no information

---

## 12. Operational Modes

The system adapts rigor based on load, but **never compromises L3 safety**. A hard **25% Compute Reserve** is always dedicated to L3 verification, regardless of system load.

| Mode       | Description          | L1           | L2        | L3         |
| :--------- | :------------------- | :----------- | :-------- | :--------- |
| **NORMAL** | Standard operation   | 100%         | 100%      | 100%       |
| **LEAN**   | Resource constrained | 10% sampling | 100%      | 100%       |
| **SURGE**  | High traffic         | Deferred     | 100%      | 100%       |
| **SAFE**   | Threat detected      | Suspended    | Suspended | Human only |

#### Mode Transition Triggers

| Mode  | Trigger Condition                 | Exit Condition               |
| :---- | :-------------------------------- | :--------------------------- |
| LEAN  | CPU > 70% sustained for 5 min     | CPU < 50% for 10 min         |
| SURGE | Queue depth > 50 pending tasks    | Queue depth < 10             |
| SAFE  | Security event OR manual override | Manual clearance by Overseer |

> _In SAFE mode, fallback rules (Section 4.2) are suspended; all non-L3 work is halted until threat is resolved._

#### Variable Behavior by Resource Tier

Verification depth scales with available compute budget:

| Tier           | Characteristics                   | Verification Approach               |
| :------------- | :-------------------------------- | :---------------------------------- |
| **Sovereign**  | Local-only, legacy HW (< 4GB RAM) | Bounded checks, sampling, heuristic |
| **Hybrid**     | Local + free cloud tier           | Full Sentinel + cloud Scrivener     |
| **Enterprise** | Dedicated GPU/cloud               | Full BMC, multi-model quorum        |

### 12.1. Resource Governance Thresholds

| Threshold             | Value | Action                                   |
| :-------------------- | :---- | :--------------------------------------- |
| Budget Alert          | 10%   | Alert when 10% over allocated budget     |
| CPU Throttle (Legacy) | 40%   | Cap Sentinel CPU to prevent HW crash     |
| L3 Compute Reserve    | 25%   | Protected allocation for safety-critical |
| RAM Limit (Legacy)    | < 4GB | Maximum memory for Sentinel operations   |
| Circuit Breaker       | N/A   | Auto-suspend agent on budget breach      |

### 12.2. Circuit Breakers

Automatic throttling mechanisms to prevent runaway costs:

- **Budget Tracker:** Real-time remaining budget signal injected into reasoning loop
- **Auto-Throttle:** If agent approaches limit, suspend further calls
- **BATS Framework:** Budget-awareness generalized across multi-agent systems

---

## 13. Technical Implementation Requirements

### 13.1. Required Components

| Component         | Purpose                          | Technology           |
| :---------------- | :------------------------------- | :------------------- |
| MCP Server        | Tool exposure to Agent           | FastMCP (Python)     |
| Memory MCP Server | Persistent state across sessions | Knowledge graph/DB   |
| SQLite Database   | SOA Ledger + Shadow Genome       | SQLite 3             |
| Sentinel Engine   | Verification logic               | Python + AST         |
| Identity Manager  | DID/key generation               | cryptography library |

### 13.2. Future Research

| Area             | Goal                             | Benchmark/Target         |
| :--------------- | :------------------------------- | :----------------------- |
| Real BMC         | Replace regex with CBMC/ESBMC    | N/A                      |
| HRM Model        | Train actual 27M-param verifier  | ~1K labeled samples      |
| PyVeritas        | Python-to-C transpilation for FV | ~80% accuracy            |
| JDoctor          | Comment-to-spec generation       | ~92% precision           |
| Semantic Drift   | Embedding-based drift detection  | Cosine < 0.85            |
| Diversity Quorum | Multi-model L3 verification      | ≥2 model families        |
| Epistemic Logic  | MCMAS-based agent knowledge      | Track "what agents know" |

---

## Appendix A: Acceptance Criteria

> _Note: Targets marked with † are "forcing functions" that require specific architectural components to achieve. (See RESEARCH_VALIDATION.md §4, §5)_

| Metric                   | Target     | Measurement                     | Required Components                      |
| :----------------------- | :--------- | :------------------------------ | :--------------------------------------- |
| Scrivener Hallucination  | ≤ 1%†      | Rate per 1000 claims (30d)      | RAG + CoT + Span Verification            |
| Hallucination Catch Rate | ≥ 95%      | True positives on trap prompts  | Sentinel + verification loop             |
| False Positive Rate      | ≤ 5%†      | Good code incorrectly rejected  | Enterprise-grade SAST (Veracode-class)   |
| L3 Verification SLA      | 100% < 24h | Time to human approval          | Queue management                         |
| L3 First Response        | < 2 min    | Safe guidance before full truth | Immediate feedback (50ms acknowledgment) |
| Sentinel FV Latency      | ~0.17s     | Per-snippet verification time³  | Symbolic execution (ACCA-class)          |
| PII Leakage              | 0%         | Raw PII in logs                 | Mandatory redaction layer                |
| Merkle Chain Integrity   | 100%       | Hash verification on read       | SQLite + cryptography                    |
| Determinism              | Semantic\* | Logically equivalent verdicts   | Seed logging + drift tracking            |
| Defect Reduction         | ~78%       | Relative drop vs baseline⁴      | Full verification pipeline               |

**Critical Notes on Targets:**

1. **Hallucination ≤ 1%:** Raw LLM output hallucinates at 18-50% (HaluEval). RAG reduces to ~5%. The <1% target requires span-level verification post-generation. This is a "forcing function" ensuring proper architecture.

2. **FPR ≤ 5%:** Standard SAST tools exhibit 36-82% FPR. Only verified enterprise tools achieve <5%. This target is valid only with appropriate tooling investment.

3. **Semantic Determinism:** Bitwise reproducibility is infeasible due to GPU floating-point non-associativity. The system mandates:
   - Fixed random seeds for LLM inference
   - System fingerprint logging (CUDA version, hardware)
   - Drift tracking between runs
   - Logical equivalence verification for audit

> ³ _ACCA system symbolic execution benchmark (computerfraudsecurity.com)_
>
> ⁴ _Fintech case study: defect rates fell from 4.82% to 1.06% after adding formal checks (computerfraudsecurity.com)_

---

## Appendix B: Research Metrics

| Metric                     | Description                               | Formula             |
| :------------------------- | :---------------------------------------- | :------------------ |
| **Precision**              | How many "Verified" were actually correct | `TP / (TP + FP)`    |
| **Recall**                 | How many hallucinations were caught       | `TP / (TP + FN)`    |
| **F1 Score**               | Harmonic mean of Precision and Recall     | `2 * (P*R) / (P+R)` |
| **Abstention Rate**        | Correct "I don't know" responses          | `Unknown / Total`   |
| **Failure Detection Rate** | Did we catch the bug? (Recall alias)      | Same as Recall      |
| **False Positive Rate**    | Did we block good code?                   | `FP / (FP + TN)`    |
| **Convergence Speed**      | Generations to solve error class          | Count               |
| **Fitness Improvement**    | Score delta across generations            | `Δ Fitness Score`   |

---

## Appendix C: Citations and References

### Research Library

**Primary Reference:** [Research Library Index](./research/INDEX.md) — Complete catalog of QoreLogic research documentation.

**Design Validation:** [RESEARCH_VALIDATION.md](./research/synthesis/RESEARCH_VALIDATION.md) — Comprehensive empirical justification for all design parameters, including 57 academic and industry citations.

**Open Questions:** [GAPS_AND_QUESTIONS.md](./research/synthesis/GAPS_AND_QUESTIONS.md) — Research gaps and comprehensive prompt for future research.

### Specification Citations

| Citation | Source                                         | Claim                                                                 |
| :------- | :--------------------------------------------- | :-------------------------------------------------------------------- |
| ¹        | HRM vs CoT Benchmarks                          | 80% cost reduction via local latent reasoning (ARC-AGI, Sudoku tasks) |
| ²        | Datadog Engineering                            | LLM-based SAST triage reduces false positives by ~90%                 |
| ³        | ACCA System (computerfraudsecurity.com)        | Symbolic execution verifies snippets in ~0.17 seconds                 |
| ⁴        | Fintech Case Study (computerfraudsecurity.com) | Defects fell from 4.82% to 1.06% (~78% reduction)                     |
| ⁵        | JDoctor (homes.cs.washington.edu)              | Comment-to-spec generation with ~92% precision                        |
| ⁶        | PyVeritas (arxiv.org)                          | Python-to-C transpilation achieves ~80% verification accuracy         |
| ⁷        | Official HRM Repository (github.com)           | 27M-param HRM trained on ~1K labeled samples                          |
| ⁸        | Differential Privacy Research                  | ε budget values: Apple (2-16), US Census (≈19.1), Google RAPPOR (1-9) |
| ⁹        | Source Credibility Research                    | SCI thresholds: 90/60/35 (NewsGuard, Wikipedia RS, human trust)       |

### Primary Sources

**Formal Verification & Security:**

- **Formal Verification in CI/CD:** `computerfraudsecurity.com/index.php/journal/article/download/793/544/1528`
- **PyVeritas Paper:** `arxiv.org/html/2508.08171v1`
- **JDoctor Paper:** `homes.cs.washington.edu/~mernst/pubs/comments-specs-issta2018.pdf`
- **OWASP Benchmark:** Static Analysis Tool Evaluation
- **NIST SP 800-57:** Key Management Recommendations
- **NIST SP 800-161:** Supply Chain Risk Management

**Trust & Reputation Systems:**

- **Lewicki & Bunker (1996):** "Developing and Maintaining Trust in Work Relationships"
- **Kamvar et al. (2003):** "The EigenTrust Algorithm for Reputation Management in P2P Networks"
- **Nagin (2013):** "Deterrence in the Twenty-First Century" - HILS vs LIHS

**AI & Hallucination:**

- **Li et al. (2023):** "HaluEval: A Large-Scale Hallucination Evaluation Benchmark"
- **Lin et al. (2022):** "TruthfulQA: Measuring How Models Mimic Human Falsehoods"
- **Wei et al. (2022):** "Chain-of-Thought Prompting Elicits Reasoning in LLMs"

**Privacy & Compliance:**

- **Dwork (2006):** "Differential Privacy" - Foundational DP paper
- **Apple DP Team (2017):** "Learning with Privacy at Scale"
- **GDPR Article 33:** Data Breach Notification (72-hour mandate)
- **CERT/CC:** Vulnerability Disclosure Policy (45-day standard)

**SRE & Resource Governance:**

- **Google SRE Handbook:** Service Level Objectives, Four Golden Signals
- **Beyer et al. (2016):** "Site Reliability Engineering" (O'Reilly)
- **FinOps Foundation:** Cloud Cost Management Framework

**Psychology & UX:**

- **Yerkes & Dodson (1908):** Arousal-Performance Relationship
- **Maister (1985):** "The Psychology of Waiting Lines"

**Original Sources (Preserved):**

- **C2S Paper:** `cs.purdue.edu/homes/lintan/publications/c2s-fse20.pdf`
- **MCMAS Model Checker:** `link.springer.com/article/10.1007/s10009-015-0378-x`
- **Datadog FP Filtering:** `datadoghq.com/blog/using-llms-to-filter-out-false-positives/`
- **HRM Architecture:** `github.com` (Official HRM repository)
- **Abowd (2018):** "The U.S. Census Bureau Adopts Differential Privacy" - High-stakes DP
- **Lazer et al. (2018):** "The science of fake news" - Misinformation thresholding
- **Gupta et al. (2014):** "TweetCred: Real-Time Credibility Assessment" - Automated scoring
- **Metzger (2007):** "Making sense of credibility on the Web" - Human trust factors

### Research Citation Keys (v2.3+)

The following keys reference documents in the Research Library:

| Key         | Document                                   | Topic                                |
| :---------- | :----------------------------------------- | :----------------------------------- |
| [MAC-002]   | `technologies/MULTI_AGENT_COORDINATION.md` | JSON-RPC 2.0, backpressure           |
| [LLM-001]   | `technologies/LLM_RELIABILITY.md`          | Verification pipeline, hallucination |
| [TRUST-001] | `foundations/TRUST_DYNAMICS.md`            | EigenTrust algorithm                 |
| [TRUST-002] | `foundations/TRUST_DYNAMICS.md`            | Lewicki-Bunker trust stages          |
| [TRUST-004] | `foundations/TRUST_DYNAMICS.md`            | RiskMetrics decay factors            |
| [COMP-001]  | `compliance/AI_GOVERNANCE.md`              | GDPR Article 22                      |
| [COMP-002]  | `compliance/AI_GOVERNANCE.md`              | NIST AI RMF                          |
| [COMP-003]  | `compliance/AI_GOVERNANCE.md`              | ISO 42001                            |
| [COMP-004]  | `compliance/AI_GOVERNANCE.md`              | Google Project Zero disclosure       |
| [SRE-001]   | `technologies/MULTI_AGENT_COORDINATION.md` | Backpressure, load shedding          |

---

## Changelog

| Version | Date           | Changes                                                                                                                                                                           |
| :------ | :------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1.0     | 2025-12        | Initial specification                                                                                                                                                             |
| 2.0     | 2025-12        | Consolidated Research Standard                                                                                                                                                    |
| 2.3     | 2025-12-17     | Research integration, empirical validation                                                                                                                                        |
| **2.4** | **2025-12-17** | **Added: Communication protocol (§2.5), Edge deployment (§2.6), 3-tier pipeline (§3.3), Trust dynamics (§5.3.5-6), Disclosure policy (§8.5-6), Governance schema fields (§11.2)** |
| **9.0** | **2025-12-20** | **Phase 9.0 Complete: Z3 integration active, Trust Dynamics fully operational, Identity Fortress hardened, Contract Verifier implemented**                                        |
| **9.1** | **2025-12-22** | **Documentation alignment: Version consistency updates across all documentation files**                                                                                           |
