/**
 * QoreLogic API Client
 * 
 * Provides typed access to both Host (Launcher) and Container (Dashboard) APIs.
 * 
 * Architecture:
 * - Host API (localhost:5500): Lifecycle control, host filesystem access, agent config persistence
 * - Container API (localhost:8000): Ledger, status, workspace management, file browsing
 */

const HOST_API = "http://localhost:5500/api";
const CONTAINER_API = "http://localhost:8000/api";

/**
 * Safe fetch wrapper with offline detection and circuit breaker support.
 * 
 * @param {string} url - Full URL to fetch
 * @param {object} options - Fetch options
 * @returns {Promise<{success: boolean, data?: any, offline?: boolean, error?: string}>}
 */
async function safeFetch(url, options = {}) {
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    if (!res.ok) {
      return { success: false, error: `HTTP ${res.status}: ${res.statusText}` };
    }
    
    const data = await res.json();
    return { success: true, data };
  } catch (e) {
    return { success: false, offline: true, error: e.message };
  }
}

// ============================================================================
// HOST API (Launcher at localhost:5500)
// Operations that require host-side access (not available inside container)
// ============================================================================

export const HostAPI = {
  /**
   * Check if the Launcher server is running
   */
  health: () => safeFetch(`${HOST_API}/health`),
  
  /**
   * Launch the QoreLogic container
   * @param {object} params - { path?: string, workspace?: string }
   */
  launch: (params = {}) => safeFetch(`${HOST_API}/launch`, {
    method: 'POST',
    body: JSON.stringify(params)
  }),
  
  /**
   * Stop the QoreLogic container
   */
  stop: () => safeFetch(`${HOST_API}/stop`, { method: 'POST' }),
  
  /**
   * Open native folder browser dialog (Windows)
   * @returns {Promise<{success: boolean, data?: {path: string}}>}
   */
  browseFolder: () => safeFetch(`${HOST_API}/dialog/folder`),
  
  /**
   * Get/Set operational mode (NORMAL, LEAN, SURGE, SAFE)
   * @param {string|null} mode - If provided, sets the mode. Otherwise returns current.
   * @param {string} workspace - Workspace ID for scoped mode
   */
  mode: async (mode = null, workspace = 'default') => {
    if (mode) {
      return safeFetch(`${HOST_API}/config/mode`, {
        method: 'POST',
        body: JSON.stringify({ mode, workspace })
      });
    }
    return safeFetch(`${HOST_API}/config/mode?workspace=${workspace}`);
  },
  
  /**
   * Save agent configuration (LLM providers, models, prompts)
   * @param {object} config - Agent configuration object
   */
  saveAgentConfig: (config) => safeFetch(`${HOST_API}/config/agents`, {
    method: 'POST',
    body: JSON.stringify(config)
  }),

  // --- Phase 9/10 Extensions ---
  
  /**
   * Get/Set Verification Config (Full/Lite/Disabled)
   * @param {object|null} config - If provided, sets config.
   */
  verificationConfig: (config = null) => {
    if (config) {
      return safeFetch(`${HOST_API}/verification/config`, {
        method: 'POST',
        body: JSON.stringify(config)
      });
    }
    return safeFetch(`${HOST_API}/verification/config`);
  },

  /**
   * Get Trust Status for Agent
   * @param {string} did - e.g. "did:myth:sentinel"
   */
  trustStatus: (did = null) => {
    const url = did ? `${HOST_API}/trust/status?did=${did}` : `${HOST_API}/trust/status`;
    return safeFetch(url);
  },

  /**
   * List Agent Identities
   */
  listIdentities: () => safeFetch(`${HOST_API}/identity/list`),

  /**
   * Rotate Key for Identity
   * @param {string} did 
   */
  rotateKey: (did) => safeFetch(`${HOST_API}/identity/rotate`, {
    method: 'POST',
    body: JSON.stringify({ did })
  }),
  
  /**
   * Query Ledger Events (via Host Bridge)
   */
  queryHostLedger: () => safeFetch(`${HOST_API}/ledger/events`)
};

// ============================================================================
// CONTAINER API (Dashboard at localhost:8000)
// Operations available from within the container's FastAPI backend
// ============================================================================

export const ContainerAPI = {
  /**
   * Check if the container is running and API is available
   */
  health: () => safeFetch(`${CONTAINER_API}/health`),
  
  /**
   * Get system status (ledger count, mode, etc.)
   * @param {string|null} workspaceId - Optional workspace for scoped stats
   */
  status: (workspaceId = null) => {
    const url = workspaceId 
      ? `${CONTAINER_API}/status?ws_id=${workspaceId}`
      : `${CONTAINER_API}/status`;
    return safeFetch(url);
  },
  
  /**
   * Get ledger entries
   * @param {number} limit - Max entries to return
   * @param {string|null} workspaceId - Optional workspace filter
   */
  ledger: (limit = 50, workspaceId = null) => {
    let url = `${CONTAINER_API}/ledger?limit=${limit}`;
    if (workspaceId) url += `&ws_id=${workspaceId}`;
    return safeFetch(url);
  },
  
  /**
   * List files in workspace
   * @param {string} path - Path relative to workspace root
   */
  files: (path = '') => safeFetch(`${CONTAINER_API}/files?path=${encodeURIComponent(path)}`),
  
  /**
   * List all registered workspaces
   */
  listWorkspaces: () => safeFetch(`${CONTAINER_API}/workspaces`),
  
  /**
   * Register a new workspace
   * @param {object} workspace - { name, path, env_type? }
   */
  createWorkspace: (workspace) => safeFetch(`${CONTAINER_API}/workspaces`, {
    method: 'POST',
    body: JSON.stringify(workspace)
  }),
  
  /**
   * Activate a workspace by ID
   * @param {string} id - Workspace ID
   */
  activateWorkspace: (id) => safeFetch(`${CONTAINER_API}/workspaces/activate`, {
    method: 'POST',
    body: JSON.stringify({ id })
  })
};

// ============================================================================
// CONNECTION STATE UTILITIES
// ============================================================================

export const ConnectionState = {
  /**
   * Check both Host and Container connectivity
   * @returns {Promise<{host: boolean, container: boolean}>}
   */
  checkAll: async () => {
    const [hostRes, containerRes] = await Promise.all([
      HostAPI.health(),
      ContainerAPI.health()
    ]);
    
    return {
      host: hostRes.success && !hostRes.offline,
      container: containerRes.success && !containerRes.offline
    };
  }
};

export default { HostAPI, ContainerAPI, ConnectionState };
