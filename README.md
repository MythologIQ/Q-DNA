# QoreLogic: The Autopoietic Code Governance Engine

**Version:** 2.1.0 ("Sterile Fortress")
**Status:** Production Ready

---

## 🚀 Quick Start (Zero-Setup)

**QoreLogic Gatekeeper** is now a fully isolated, sovereign appliance. You do not need to install Python or dependencies on your host machine.

### 1. Launch the System

Navigate to the `launcher` directory and double-click:

> **`Launch_QoreLogic.bat`**

This will open the **Command Center**, where you can:

- **Initialize** the sterile Docker container (auto-builds if missing).
- **Configure** your host environment variables.
- **Manage** isolated workspaces.

### 2. CLI Usage

Once initialized, you can use the generated wrapper in your project:

```powershell
.\qorelogic-check.bat --monitor src/my_code.py
```

---

## 🛡️ Features

- **Sterile Isolation**: Runs entirely in Docker. No local `pip` pollution.
- **Sovereign Ledger**: All trust data is stored locally in `~/.qorelogic/ledger`.
- **Real-Time Dashboard**: Built-in visual interface for telemetry and auditing.
- **Multi-Workspace**: Support for isolated environments (Standard vs. Strict).

---

## 📚 Documentation

The complete manual for developers, integrators, and architects:

👉 **[READ THE DEVELOPER MANUAL](docs/DEVELOPER_MANUAL.md)**

- **Architecture**: Deep dive into the Sovereign Ledger and Trust Models.
- **Integration**: API Reference for custom dashboards.
- **Troubleshooting**: Managing L3 approvals and system modes.

---

## License

Apache License 2.0 - See [LICENSE](LICENSE).

**MythologIQ Studio** | _Building trustworthy AI systems_
