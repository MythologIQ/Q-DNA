# QoreLogic: The Autopoietic Code Governance Engine

**Version:** 9.0 ("Formal Verification Active")
**Status:** Production Ready
**Phase:** 9.0 (Z3 Integration Complete)
**Last Updated:** December 22, 2025

---

## 🚀 Quick Start (Zero-Setup)

**QoreLogic Gatekeeper** is now a fully isolated, sovereign appliance. You do not need to install Python or dependencies on your host machine.

### 1. Launch the System

Navigate to the `launcher` directory and double-click:

> **`Launch_QoreLogic.bat`**

This will open the **Command Center**, where you can:

- **Initialize** the sovereign Docker engine (runs continuously).
- **Create & Switch** isolated workspaces instantly without restarting.
- **Audit** multiple projects with strict data segregation.

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
- **Three-Tier Verification**: Static Analysis → Design by Contract → Formal Verification.
- **Trust Dynamics**: EWMA-based scoring with Lewicki-Bunker stages and micro-penalties.
- **Z3 Integration**: Active formal contract verification for logical consistency.
- **Identity Fortress**: Ed25519 cryptographic identities with automatic rotation.

---

## 📚 Documentation

The complete manual for developers, integrators, and architects:

👉 **[READ THE DEVELOPER MANUAL](docs/DEVELOPER_MANUAL.md)**

- **Architecture**: Deep dive into the Sovereign Ledger and Trust Models.
- **Integration**: API Reference for custom dashboards.
- **Verification Pipeline**: Details on the three-tier verification system.
- **Trust Dynamics**: EWMA scoring, stage transitions, and penalty system.
- **Troubleshooting**: Managing L3 approvals and system modes.

### Additional Documentation

- **[QoreLogic Specification](docs/QoreLogic_SPECIFICATION.md)**: Complete technical specification
- **[Research vs Reality](docs/RESEARCH_VS_REALITY_v2.md)**: Implementation status report
- **[Development Plan](docs/DEVELOPMENT_PLAN.md)**: Roadmap and task breakdown

---

## License

Apache License 2.0 - See [LICENSE](LICENSE).

**MythologIQ Studio** | _Building trustworthy AI systems_
