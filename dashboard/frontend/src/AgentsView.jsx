import { useState, useEffect } from 'react';
import { HostAPI } from './api';

/**
 * Agent Configuration Panel
 * 
 * Allows configuration of:
 * - LLM Backend (Ollama, OpenAI, Anthropic)
 * - Per-agent model assignment (Sentinel, Judge, Overseer, Scrivener)
 * - System prompts for each agent
 * - Formal Verification Protocol (PyVeritas)
 * 
 * Configuration is persisted to host filesystem via Launcher API (5500)
 */
export default function AgentsView() {
  const [provider, setProvider] = useState('ollama');
  const [endpoint, setEndpoint] = useState('http://localhost:11434');
  const [models, setModels] = useState({
    sentinel: 'default',
    judge: 'default',
    overseer: 'default',
    scrivener: 'default'
  });
  const [prompts, setPrompts] = useState({
    sentinel: 'You are SENTINEL, a static analysis expert focused on security.',
    judge: 'You are JUDGE, the final arbiter of code compliance.',
    overseer: 'You are OVERSEER, a project manager and strategist.',
    scrivener: 'You are SCRIVENER, the technical documentation engine.'
  });
  const [availableModels, setAvailableModels] = useState([]);
  const [modelStatus, setModelStatus] = useState('');
  const [saving, setSaving] = useState(false);
  const [hostConnected, setHostConnected] = useState(false);
  
  // Phase 9: Verification Config
  const [verificationMode, setVerificationMode] = useState('lite');

  // Check host connectivity on mount
  useEffect(() => {
    HostAPI.health().then(res => {
      setHostConnected(res.success && !res.offline);
    });
    
    // Load Verification Config
    HostAPI.verificationConfig().then(res => {
        if (res && res.success && res.config) {
            setVerificationMode(res.config.mode);
        }
    });
  }, []);

  // Update endpoint when provider changes
  useEffect(() => {
    const endpoints = {
      ollama: 'http://localhost:11434',
      openai: 'https://api.openai.com/v1',
      anthropic: 'https://api.anthropic.com/v1'
    };
    setEndpoint(endpoints[provider] || endpoints.ollama);
  }, [provider]);

  const refreshModels = async () => {
    setModelStatus('Scanning...');
    try {
      const res = await fetch(`${endpoint}/api/tags`);
      if (!res.ok) throw new Error('Connection failed');
      
      const data = await res.json();
      const modelList = data.models?.map(m => m.name) || [];
      setAvailableModels(modelList);
      setModelStatus(`✅ Found ${modelList.length} models`);
    } catch (e) {
      setModelStatus('❌ Connection Failed');
      setAvailableModels([]);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    const config = {
      provider,
      endpoint,
      models,
      prompts
    };
    
    // Save Agents Config
    const result = await HostAPI.saveAgentConfig(config);
    
    // Save Verification Config
    const vResult = await HostAPI.verificationConfig({ mode: verificationMode });
    
    if (result.success && vResult.success) {
      alert('Configuration saved successfully!');
    } else {
      alert(`Error saving: ${result.error || vResult.error || 'Unknown error'}`);
    }
    setSaving(false);
  };

  const updateModel = (agent, value) => {
    setModels(prev => ({ ...prev, [agent]: value }));
  };

  const updatePrompt = (agent, value) => {
    setPrompts(prev => ({ ...prev, [agent]: value }));
  };

  if (!hostConnected) {
    return (
      <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
        <h2 style={{ marginBottom: '16px' }}>Host Connection Required</h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          Agent configuration requires the Launcher host server (localhost:5500).
          <br />
          Please ensure the Launcher is running.
        </p>
      </div>
    );
  }

  const agents = [
    { key: 'sentinel', name: 'Sentinel', icon: '🛡️', role: 'Security Auditor' },
    { key: 'judge', name: 'Judge', icon: '⚖️', role: 'Compliance Verifier' },
    { key: 'overseer', name: 'Overseer', icon: '👁️', role: 'Context Manager' },
    { key: 'scrivener', name: 'Scrivener', icon: '📝', role: 'Documentation Engine' }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '900px' }}>
      
      {/* Formal Verification Settings (New Phase 9) */}
      <div className="glass-panel" style={{ padding: '24px', borderLeft: '3px solid var(--accent-primary)' }}>
        <h3 style={{ marginBottom: '8px', color: 'var(--text-primary)' }}>Formal Verification Protocol</h3>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
            Configure PyVeritas verification intensity. 
            Full mode requires GPU resources for LLM transpilation.
        </p>
        
        <div style={{ display: 'flex', gap: '4px', background: 'rgba(0,0,0,0.2)', padding: '4px', borderRadius: '8px', width: 'fit-content' }}>
            {['disabled', 'lite', 'full'].map(mode => (
                <button
                    key={mode}
                    onClick={() => setVerificationMode(mode)}
                    style={{
                        padding: '8px 24px',
                        borderRadius: '6px',
                        border: 'none',
                        background: verificationMode === mode ? 'var(--accent-primary)' : 'transparent',
                        color: verificationMode === mode ? 'var(--bg-primary)' : 'var(--text-secondary)',
                        fontWeight: verificationMode === mode ? 600 : 400,
                        cursor: 'pointer',
                        textTransform: 'capitalize',
                        transition: 'all 0.2s'
                    }}
                >
                    {mode}
                </button>
            ))}
        </div>
        
        <div style={{ marginTop: '16px', fontSize: '12px', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
            {verificationMode === 'disabled' && "Verification disabled. Not recommended for production."}
            {verificationMode === 'lite' && "Pattern-based heuristic scanning (CPU-friendly). Catches 60-70% of issues."}
            {verificationMode === 'full' && "LLM Transpilation + CBMC Bounded Model Checking. High accuracy, higher latency."}
        </div>
      </div>

      {/* LLM Backend Connection */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ marginBottom: '20px', color: 'var(--text-primary)' }}>LLM Backend Connection</h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <label style={labelStyle}>Provider</label>
            <select 
              value={provider} 
              onChange={e => setProvider(e.target.value)}
              className="input-field"
            >
              <option value="ollama">Ollama (Local)</option>
              <option value="openai">OpenAI (API)</option>
              <option value="anthropic">Anthropic (API)</option>
            </select>
          </div>
          
          <div>
            <label style={labelStyle}>Base URL</label>
            <input 
              type="text"
              value={endpoint}
              onChange={e => setEndpoint(e.target.value)}
              className="input-field"
              style={{ fontFamily: 'var(--font-mono)' }}
            />
          </div>
        </div>

        {provider === 'ollama' && (
          <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button 
              onClick={refreshModels}
              style={secondaryButtonStyle}
            >
              🔄 Discover Local Models
            </button>
            <span style={{ fontSize: '12px', color: modelStatus.includes('✅') ? 'var(--success)' : modelStatus.includes('❌') ? 'var(--error)' : 'var(--text-secondary)' }}>
              {modelStatus}
            </span>
          </div>
        )}
      </div>

      {/* Agent Configurations */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ marginBottom: '8px', color: 'var(--text-primary)' }}>Agent Assignment & Directives</h3>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '24px' }}>
          Assign specific models and prompts to each cognitive role.
        </p>

        {agents.map((agent, index) => (
          <div 
            key={agent.key}
            style={{ 
              borderBottom: index < agents.length - 1 ? '1px solid var(--border-subtle)' : 'none',
              paddingBottom: index < agents.length - 1 ? '20px' : 0,
              marginBottom: index < agents.length - 1 ? '20px' : 0
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <label style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>
                {agent.icon} {agent.name} ({agent.role})
              </label>
              <select 
                value={models[agent.key]}
                onChange={e => updateModel(agent.key, e.target.value)}
                style={{ width: '200px' }}
                className="input-field"
              >
                <option value="default">Default (System)</option>
                {availableModels.map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
            <textarea
              value={prompts[agent.key]}
              onChange={e => updatePrompt(agent.key, e.target.value)}
              rows={3}
              style={textareaStyle}
            />
          </div>
        ))}

        <button 
          onClick={handleSave}
          disabled={saving}
          className="btn-primary"
          style={{ marginTop: '24px', width: '100%' }}
        >
          {saving ? 'Saving...' : 'Save Agent Configuration'}
        </button>
      </div>
    </div>
  );
}

// Styles
const labelStyle = {
  display: 'block',
  marginBottom: '8px',
  color: 'var(--text-secondary)',
  fontSize: '14px'
};

const secondaryButtonStyle = {
  padding: '8px 16px',
  fontSize: '12px',
  background: 'rgba(255,255,255,0.05)',
  border: '1px solid var(--border-subtle)',
  borderRadius: '6px',
  color: 'var(--text-primary)',
  cursor: 'pointer'
};

const textareaStyle = {
  width: '100%',
  marginTop: '8px',
  background: 'rgba(0,0,0,0.3)',
  color: 'var(--text-secondary)',
  border: '1px solid var(--border-subtle)',
  padding: '12px',
  borderRadius: '6px',
  fontFamily: 'var(--font-mono)',
  fontSize: '12px',
  resize: 'vertical'
};
