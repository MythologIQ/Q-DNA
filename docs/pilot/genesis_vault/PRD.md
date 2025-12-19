# Pilot: Genesis Vault (PRD)

**Project:** Genesis Vault (Vault-KV)
**Phase:** 14 (Pilot Deployment)
**Gatekeeper:** QoreLogic Daemon (v2.1)

## 1. Executive Summary

"Genesis Vault" is a secure, persistent Key-Value store designed to test the **QoreLogic Trust System** in a real-world development scenario. The goal is not just to build the app, but to measure the _friction_ and _guidance_ provided by the active QoreLogic daemon during the build process.

## 2. Product Specifications

### 2.1 Core Features

1.  **Secure Storage:** Store secrets (API Keys, DB Creds) encrypted at rest (Fernet/AES).
2.  **RBAC:** Role-Based Access Control (Admin vs. User).
3.  **Audit Logs:** Immutable log of all access attempts.
4.  **HTTP API:** RESTful interface (FastAPI) for PUT/GET/DELETE.

### 2.2 Technical Constraints (The "Gauntlet")

- **Language:** Python 3.12+
- **Database:** SQLite (for portability in pilot)
- **Security:**
  - No hardcoded secrets (Env vars only).
  - No PII in logs.
  - Strict Input Validation (No Injection).
  - _Constraint:_ Must pass Sentinel L2 checks to commit.

## 3. The Experiment (Metasystem)

We are testing the **System**, not just the App.

### 3.1 Success Metrics

| Metric              | Definition                                     | Target        |
| :------------------ | :--------------------------------------------- | :------------ |
| **Trust Velocity**  | Rate of Agent Trust Score increase per commit  | > +0.05 / day |
| **Rejection Rate**  | % of commits blocked by Sentinel               | < 20%         |
| **False Positives** | % of blocks that were incorrect                | < 5%          |
| **"Save" Rate**     | % of blocks that caught actual vulnerabilities | > 80%         |

### 3.2 The Split-Test Strategy (A/B)

To measure the impact of QoreLogic without building the app twice, we will split the build:

1.  **Control Group (The "Naked" Build):**
    - **Component:** `utils/` and `network/` (approx 30% of code).
    - **Mode:** Daemon DISABLED.
    - **Metric:** Raw coding speed, latent bugs found later.
2.  **Experimental Group (The "Protected" Build):**
    - **Component:** `storage/` and `auth/` (Critical 70%).
    - **Mode:** Daemon ACTIVE (Full Sentinel).
    - **Metric:** Trust Velocity, standardized quality, "Friction" overhead.

### 3.3 Isolation Strategy

- **Codebase:** `src/pilot/vault_kv/` (Isolated from main QoreLogic core)
- **Tests:** `tests/pilot/`
- **Artifacts:** `docs/pilot/genesis_vault/`

## 4. Roadmap

1.  **Setup:** Initialize Repo & Env (Phase 14.1)
2.  **Core:** Implement Storage Engine (Phase 14.2)
3.  **API:** Implement FastAPI Interface (Phase 14.3)
4.  **Hardening:** Apply Encryption & RBAC (Phase 14.4)
5.  **Review:** Final Audit & Report (Phase 14.5)
