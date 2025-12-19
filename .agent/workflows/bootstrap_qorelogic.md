---
description: Bootstrap QoreLogic in a new workspace
---

# Bootstrap QoreLogic

**Trigger:** `/bootstrap_qorelogic`

This workflow helps you set up the QoreLogic Gatekeeper in a new environment.

## Workflow Steps

1.  **Environment Check**

    - usage: `run_command`
    - Check if `qorelogic-check` is already available in the PATH.

    ```bash
    qorelogic-check --help
    ```

2.  **Installation (Conditional)**

    - If Step 1 failed (command not found):
    - **Option A (Local Repo):** If `local_fortress` directory exists, install editable.
      ```bash
      pip install -e local_fortress
      ```
    - **Option B (Standard):** If no local source, attempt standard install.
      ```bash
      pip install qorelogic-gatekeeper
      ```

3.  **Verification**
    // turbo

    - Verify the installation by checking system status.

    ```bash
    qorelogic-server --version
    ```

4.  **MCP Connection (Optional)**
    - If you prefer NOT to install locally (e.g., Docker usage), you can configure your IDE/Agent to connect to an existing Daemon via MCP.
    - _Action:_ Create a `qorelogic.json` config file pointing to the Docker instance.

## Output

- **Success:** QoreLogic is active.
- **Fail:** Troubleshoot Python environment or Docker connection.
