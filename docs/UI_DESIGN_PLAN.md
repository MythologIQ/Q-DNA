# QoreLogic UI Design Plan & Functionality Audit

**Version:** 1.0
**Date:** December 21, 2025
**Status:** Approved for Implementation

---

## 1. Functionality Audit

| Feature Domain     | Backend Capability                                                                           | Current UI State                                                                   | Gap / Requirement                                                                         |
| :----------------- | :------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------- |
| **Agent Config**   | `agent_config.py` loads `agents.json`. Supports endpoint, model per agent, prompt overrides. | **Partial.** `AgentsView.jsx` exists but needs to sync with new backend structure. | Update `AgentsView` to match `agent_config.py` schema directly.                           |
| **Verification**   | `verification_config.py` supports `full`, `lite`, `disabled` modes.                          | **None.** No controls for formal verification.                                     | **NEW:** `VerificationSettings` component. Toggles for mode, LLM selection for Full mode. |
| **Trust Dynamics** | `trust_engine.py` tracks scores, stages (Lewicki-Bunker), penalties, history.                | **None.** Hidden internal state.                                                   | **NEW:** `TrustMonitor` widget. Visualization of scores, current stage, and penalty log.  |
| **Identity**       | `identity_manager.py` manages DIDs, keys (Argon2id), rotation.                               | **None.** CLI only.                                                                | **NEW:** `IdentityFortress` view. List active DIDs, key age, "Rotate Key" action.         |
| **Ledger**         | `myth_soa_init.py` stores `workspace_id` stamped events.                                     | **None.** Database file only.                                                      | **NEW:** `LedgerExplorer` view. Read-only grid of `soa_ledger` events.                    |

---

## 2. Design Philosophy: "Digital Glass"

- **Visual Style:** Dark mode, deep blurred backgrounds (Glassmorphism), neon accent gradients (Cyberpunk/Sci-Fi).
- **Typography:** Inter/JetBrains Mono. Technical, crisp, high contrast.
- **Interaction:** Instant feedback, smooth transitions, explicit "Save" actions for config.

---

## 3. Implementation Plan

### 3.1 Extended Agents View (`AgentsView.jsx`)

**Updates:**

- Add a new section: **"Formal Verification Protocol"** (below Agent Assignment).
- Controls:
  - **Mode Selector:** Segmented control [ Disabled | Lite | Full ].
  - **Lite Mode:** Show "Patterns Active: 23" badge.
  - **Full Mode:** Show "Transpiler Model" dropdown (filters for coding models) + "Timeout" slider.

**Mockup Structure:**

```jsx
<GlassPanel title="Security Protocols">
  <div className="mode-toggle">
    <Button active={mode === "disabled"}>Disabled</Button>
    <Button active={mode === "lite"}>Lite (Heuristic)</Button>
    <Button active={mode === "full"}>Full (Formal Verification)</Button>
  </div>
  {mode === "full" && (
    <div className="advanced-settings">
      <ModelSelect label="Transpiler Model" />
      <Slider label="Timeout (s)" min={10} max={120} />
    </div>
  )}
</GlassPanel>
```

### 3.2 Trust Monitor Widget (`TrustMonitor.jsx`)

**Location:** Dashboard Home (New Widget)

**Features:**

- **Score Gauge:** Circular progress bar showing calculated Trust Score (0.0 - 1.0).
- **Stage Indicator:** Badge showing "CALCULUS" / "KNOWLEDGE" / "IDENTIFICATION".
- **Penalty Feed:** Scrollable list of recent negative events (e.g., "Micro-Penalty: Schema Violation (-0.05)").

### 3.3 Identity Fortress View (`IdentityView.jsx`)

**Location:** New Tab in Navigation

**Features:**

- **Agent Card:** One card per role (Sentinel, Judge, etc.).
- **Details:** DID string (copyable), Key Fingerprint (short hash), Key Age (days).
- **Action:** "Rotate Key" button (triggers `identity_manager.rotate_key` via API).
- **Security Badge:** "Argon2id" tag if using new KDF.

### 3.4 Ledger Explorer (`LedgerView.jsx`)

**Location:** New Tab in Navigation

**Features:**

- **Table:** Timestamp | Workspace | Agent | Event Type | Hash (short).
- **Filter:** Global search box (filter by DID, type, or payload).
- **Detail View:** Clicking a row expands identifying JSON payload.

---

## 4. API Extensions Required

To support these views, `launcher/server.ps1` (Host API) needs new endpoints:

| Endpoint                   | Method   | Purpose                                       |
| :------------------------- | :------- | :-------------------------------------------- |
| `/api/verification/config` | GET/POST | Read/Write `verification_config.py` settings. |
| `/api/trust/status`        | GET      | Read current Trust Score and history.         |
| `/api/identity/list`       | GET      | List public identity info (DIDs, key ages).   |
| `/api/identity/rotate`     | POST     | Trigger key rotation for a role.              |
| `/api/ledger/events`       | GET      | Query `soa_ledger` rows (limit 100).          |

---

## 5. Execution Order

1.  **Backend API:** Extend `launcher/server.ps1` and Python bridge to expose new data.
2.  **Frontend Components:**
    - Build `TrustMonitor` (High impact visual).
    - Update `AgentsView` (High utility).
    - Build `IdentityView` (Security feature).
    - Build `LedgerView` (Auditability).
3.  **Integration:** Wire components to real API data.
