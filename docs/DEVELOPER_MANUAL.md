# QoreLogic Developer Manual

**Version:** 2.1.0 ("Sterile Fortress")
**Scope:** Installation, Configuration, Integration, and Architecture.

---

## 1. Quick Start (Get Running)

QoreLogic operates as a **Sterile Appliance**. It does not install dependencies on your host machine.

### 1.1. The One-Click Launcher

1.  Navigate to the `launcher` directory.
2.  Run **`Launch_QoreLogic.bat`** (Windows).
3.  The **Command Center** will open in your browser.

**From the Command Center:**

- **Initialize System:** Builds the `qorelogic:latest` Docker image.
- **Active Workspace:** Selects the active project context (Default: Local Fortress).
- **Environment:** Configures global encryption keys and paths.

### 1.2. The Dashboard

Once initialized, the **QoreLogic Dashboard** is available at:

> `http://localhost:8000`

It provides:

- **Telemetry**: Real-time system health and L3 approval queues.
- **Ledger**: Immutable audit log of all code verifications.
- **Workspace Manager**: UI for creating isolated project environments.

---

## 2. CLI Usage

After initialization, a wrapper script is generated in your project root: `qorelogic-check.bat`.

### 2.1. Auditing Code

To audit a file against the active workspace's rules:

```powershell
.\qorelogic-check.bat src/main.py
```

- **Exit Code 0**: PASS (or Monitor Mode)
- **Exit Code 1**: FAIL (Block Commit)

### 2.2. Monitor Mode (Non-Blocking)

Run silently without blocking (useful for initial baselining):

```powershell
.\qorelogic-check.bat --monitor src/main.py
```

### 2.3. Launching the Dashboard manually

If the dashboard is not running:

```powershell
.\qorelogic-check.bat --dashboard
```

---

## 3. Architecture: The Sterile Fortress

QoreLogic uses a "Sidecar" architecture to maintain sovereignty.

1.  **Host**: Your machine. Holds only the source code and the `qorelogic-check.bat` wrapper.
2.  **Container**: `qorelogic:latest`. Contains the Python environment, Sentinel Engine, and API.
3.  **Volume**: `~/.qorelogic/ledger`. Persists the Trust Ledger and configurations across container restarts.

### 3.1. Multi-Workspace Isolation

Each project can have its own "Workspace," which provides:

- **Isolated Database**: `project-id.db`
- **Isolated Context**: Separate trust scores and baselines.
- **Environment Template**:
  - **Standard**: Network access allowed, L2 Audit.
  - **Strict**: Network disabled (air-gapped), L3 Audit required.

---

## 4. Integration Guide (API)

The Dashboard Backend exposes an API for custom integrations.

**Base URL:** `http://localhost:8000/api`

### 4.1. Endpoints

| Endpoint      | Method | Description                      |
| :------------ | :----- | :------------------------------- |
| `/status`     | GET    | System mode and queue counts.    |
| `/ledger`     | GET    | Recent audit events.             |
| `/workspaces` | GET    | List registered workspaces.      |
| `/workspaces` | POST   | Create a new isolated workspace. |

---

## 5. Troubleshooting

**"Docker Not Found"**

- Ensure Docker Desktop is running.
- The Launcher checks for the `docker` command on startup.

**"Connection Refused" (Dashboard)**

- The container might be stopped. Run `.\qorelogic-check.bat --dashboard` to restart it.

**"L3 Approval Required"**

- This means the Sentinel Engine detected a high-risk pattern.
- Go to the **Dashboard** > **Overview** to view pending approvals (Feature coming in v2.2).
