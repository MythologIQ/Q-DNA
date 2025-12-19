# QoreLogic Developer Manual

**Version:** 2.1.0
**Scope:** Installation, Configuration, Integration, and Architecture.

---

## 1. Quick Start (Get Running)

### 1.1. Installation

QoreLogic is available as a standard Python package.

```bash
# Standard Install
pip install qorelogic-gatekeeper

# For this repository (Editable Mode)
pip install -e local_fortress
```

### 1.2. Automated Setup (IDE / Agent)

If you are in an Agentic IDE, use the slash command to auto-detect and install:

> `/bootstrap_qorelogic`

---

## 2. Tools & Usage

The package provides two primary tools: **The Hook** (Active) and **The Daemon** (Passive).

### 2.1. The Hook (`qorelogic-check`)

This CLI tool audits code against the QoreLogic Trust System. It returns an Exit Code of `1` on failure, making it ideal for CI/CD.

**Manual Run:**

```bash
qorelogic-check path/to/file.py
```

**Git Pre-Commit Hook:**
Add this to `.git/hooks/pre-commit` to block insecure code locally:

```bash
#!/bin/sh
git diff --cached --name-only --diff-filter=ACM | grep '\.py$' | xargs -r qorelogic-check
```

### 2.2. The Daemon (`qorelogic-server`)

The Daemon runs in the background, maintaining the Sovereign Ledger, Trust Scores, and Context.

**Run in Foreground:**

```bash
qorelogic-server
```

**Run in Docker (Recommended for Isolation):**
Use our [Docker Compose Template](docker-compose.yml) to run isolated daemons for different workspaces.

```bash
docker-compose up -d
```

---

## 3. Integration Guide (for Tool Builders)

Building a dashboard like **Project Failsafe**? The Daemon exposes an MCP (Model Context Protocol) API.

### 3.1. Connection Architecture

The Daemon listens on `stdio` by default.

- **Client Libs:** `mcp` (Python), `@modelcontextprotocol/sdk` (Node.js)

### 3.2. API Reference

#### System Health (For Status Boards)

**Tool:** `get_system_status()`
Returns current operational mode (NORMAL, SURGE, SAFE) and pending approval counts.

#### Verification Telemetry (For Graphs)

**Tool:** `get_telemetry_metrics()`
Returns real-time stats: Request Count, Latency, Error Rate.

#### Ledger Activity (For Feeds)

**Resource:** `ledger://recent`
Returns a JSON list of the most recent governance events (Audits, Penalties, Approvals).

---

## 4. Configuration

The system is configured via Environment Variables.

| Variable            | Description           | Default                            |
| :------------------ | :-------------------- | :--------------------------------- |
| `QORELOGIC_DB_PATH` | Path to SQLite Ledger | `./ledger/qorelogic_soa_ledger.db` |
| `QORELOGIC_MODE`    | Force start mode      | `NORMAL`                           |

---

## 5. Troubleshooting

**"Module Not Found"**

- Ensure you ran `pip install` in the active environment.
- If using Docker, ensure the volume mount maps to `/app/ledger`.

**"Commit Blocked"**

- Read the error message.
- If `L3_REQUIRED`, you must request human approval via the `request_overseer_approval` tool.
