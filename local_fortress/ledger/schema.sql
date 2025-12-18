-- Q-DNA SOA Ledger Schema v2.5
-- Aligned with Q-DNA_SPECIFICATION.md v2.5 (Fully Integrated)

-- Agent Identity Registry (Enhanced for Trust Integration - Track INT)
CREATE TABLE IF NOT EXISTS agent_registry (
    did TEXT PRIMARY KEY,
    public_key TEXT NOT NULL,
    private_key_hash TEXT, -- Never store raw private key
    role TEXT NOT NULL CHECK(role IN ('Scrivener', 'Sentinel', 'Judge', 'Overseer')),
    influence_weight REAL DEFAULT 1.0 CHECK(influence_weight >= 0 AND influence_weight <= 2.0),
    status TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'QUARANTINED', 'SUSPENDED')),
    -- Trust Dynamics Integration (Phase 8.5 Track INT)
    trust_score REAL DEFAULT 0.4 CHECK(trust_score >= 0.0 AND trust_score <= 1.0),  -- Normalized 0-1
    last_trust_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verification_count INTEGER DEFAULT 0,  -- For probation tracking (Spec §5.3.2)
    daily_penalty_sum REAL DEFAULT 0.0,    -- For micro-penalty cap (Spec §9.1)
    penalty_reset_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SOA Ledger (Merkle-Chained Event Log)
-- v2.4: Added model_version, trust_score, verification_*, gdpr fields
CREATE TABLE IF NOT EXISTS soa_ledger (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT, 
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent_did TEXT NOT NULL,
    model_version TEXT,                          -- v2.4: Model used for this action
    trust_score REAL,                            -- v2.4: Agent trust score at action time
    event_type TEXT NOT NULL CHECK(event_type IN (
        'GENESIS_AXIOM', 'PROPOSAL', 'PROPOSAL_RETRY', 
        'AUDIT_REQUEST', 'AUDIT_PASS', 'AUDIT_FAIL', 'AUDIT_VERDICT',
        'L3_APPROVAL_REQUEST', 'L3_APPROVED', 'L3_REJECTED',
        'PENALTY', 'REWARD', 'COMMIT', 'QUARANTINE',
        'MODE_CHANGE', 'SHADOW_ARCHIVE',
        'GENERATION_COMPLETE', 'SHADOW_RECALL', 'VARIANT_ARCHIVED',
        'MICRO_PENALTY', 'COOLING_OFF_START', 'COOLING_OFF_END',
        'TRUST_DECAY', 'GDPR_ESCALATION', 'DISCLOSURE_DEFERRAL',
        'TTL_BREACH', 'COACHING', 'HASH_TAMPERING', 'SUPERVISED_RERUN',
        'OVERRIDE'
    )),
    risk_grade TEXT CHECK(risk_grade IN ('L1', 'L2', 'L3')),
    payload JSON NOT NULL,
    verification_method TEXT CHECK(verification_method IN ('TIER_1', 'TIER_2', 'TIER_3', NULL)),  -- v2.4
    verification_result TEXT CHECK(verification_result IN ('PASS', 'FAIL', NULL)),                -- v2.4
    gdpr_art22_trigger INTEGER DEFAULT 0,        -- v2.4: 1 if legal effect detected
    human_approver TEXT,                         -- v2.4: DID of human approver if escalated
    entry_hash TEXT NOT NULL UNIQUE,
    prev_hash TEXT NOT NULL,
    signature TEXT NOT NULL,
    FOREIGN KEY (agent_did) REFERENCES agent_registry(did)
);

-- Reputation Change Log (Audit Trail for Influence Weights)
CREATE TABLE IF NOT EXISTS reputation_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent_did TEXT NOT NULL,
    previous_weight REAL NOT NULL,
    new_weight REAL NOT NULL,
    adjustment REAL NOT NULL,
    reason TEXT NOT NULL,
    ledger_ref_id INTEGER,
    FOREIGN KEY (agent_did) REFERENCES agent_registry(did),
    FOREIGN KEY (ledger_ref_id) REFERENCES soa_ledger(entry_id)
);

-- Shadow Genome (Failure Archive for "Fail Forward" Training)
CREATE TABLE IF NOT EXISTS shadow_genome (
    genome_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    input_vector TEXT NOT NULL,       -- The code/claim that failed
    decision_rationale TEXT,          -- Agent's intent/reasoning for this choice
    context JSON NOT NULL,            -- Environment, dependencies, etc.
    failure_mode TEXT NOT NULL,       -- Category of failure (e.g., INJECTION, HALLUCINATION)
    causal_vector TEXT,               -- Why it failed (Sentinel rationale)
    remediation_status TEXT DEFAULT 'UNRESOLVED' CHECK(remediation_status IN ('UNRESOLVED', 'RESOLVED', 'WONT_FIX')),
    resolved_by_entry_id INTEGER,     -- Link to the fix
    FOREIGN KEY (resolved_by_entry_id) REFERENCES soa_ledger(entry_id)
);

-- L3 Approval Queue (Human-in-the-Loop)
CREATE TABLE IF NOT EXISTS l3_approval_queue (
    queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    artifact_hash TEXT NOT NULL,       -- Hash of the artifact awaiting approval
    requesting_agent TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')),
    overseer_did TEXT,                 -- Who approved/rejected
    decision_timestamp TIMESTAMP,
    ledger_ref_id INTEGER,
    FOREIGN KEY (requesting_agent) REFERENCES agent_registry(did),
    FOREIGN KEY (overseer_did) REFERENCES agent_registry(did),
    FOREIGN KEY (ledger_ref_id) REFERENCES soa_ledger(entry_id)
);

-- Operational Mode State (Singleton Table)
CREATE TABLE IF NOT EXISTS system_state (
    state_id INTEGER PRIMARY KEY CHECK(state_id = 1), -- Enforce singleton
    current_mode TEXT DEFAULT 'NORMAL' CHECK(current_mode IN ('NORMAL', 'LEAN', 'SURGE', 'SAFE')),
    mode_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mode_reason TEXT,
    l3_reserve_available INTEGER DEFAULT 100  -- L3 compute budget (units)
);

-- Initialize System State
INSERT OR IGNORE INTO system_state (state_id) VALUES (1);

-- Trust Score History (Track INT - Phase 8.5)
CREATE TABLE IF NOT EXISTS trust_updates (
    update_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent_did TEXT NOT NULL,
    old_score REAL NOT NULL,
    new_score REAL NOT NULL,
    delta REAL NOT NULL,
    update_type TEXT NOT NULL CHECK(update_type IN (
        'EWMA_UPDATE',         -- Standard EWMA decay update
        'TEMPORAL_DECAY',      -- Inactivity drift toward baseline
        'MICRO_PENALTY',       -- Small penalty applied
        'VIOLATION_PENALTY',   -- Stage demotion penalty
        'COOLING_OFF_START',   -- Cooling-off period initiated
        'COOLING_OFF_END',     -- Cooling-off period completed
        'PROBATION_START',     -- Probation initiated
        'PROBATION_END',       -- Probation completed
        'MANUAL_ADJUSTMENT'    -- Human override
    )),
    context TEXT,              -- Risk context or reason for update
    ledger_ref_id INTEGER,     -- Link to triggering SOA event
    FOREIGN KEY (agent_did) REFERENCES agent_registry(did),
    FOREIGN KEY (ledger_ref_id) REFERENCES soa_ledger(entry_id)
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_ledger_timestamp ON soa_ledger(timestamp);
CREATE INDEX IF NOT EXISTS idx_ledger_agent ON soa_ledger(agent_did);
CREATE INDEX IF NOT EXISTS idx_ledger_event ON soa_ledger(event_type);
CREATE INDEX IF NOT EXISTS idx_shadow_failure ON shadow_genome(failure_mode);
CREATE INDEX IF NOT EXISTS idx_l3_status ON l3_approval_queue(status);
CREATE INDEX IF NOT EXISTS idx_trust_updates_agent ON trust_updates(agent_did);
CREATE INDEX IF NOT EXISTS idx_trust_updates_timestamp ON trust_updates(timestamp);
