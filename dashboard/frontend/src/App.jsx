import { useState, useEffect } from 'react';
import './index.css';

const API_BASE = "http://localhost:8000/api";

const Icons = {
  Dashboard: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>,
  List: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>,
  Folder: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>,
  Settings: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>,
  Plus: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
};

function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [status, setStatus] = useState(null);
  const [ledger, setLedger] = useState([]);

  const fetchData = async () => {
    try {
      const [statusRes, ledgerRes] = await Promise.all([
        fetch(`${API_BASE}/status`).catch(() => null),
        fetch(`${API_BASE}/ledger?limit=20`).catch(() => null)
      ]);
      
      if (statusRes && statusRes.ok) setStatus(await statusRes.json());
      if (ledgerRes && ledgerRes.ok) setLedger(await ledgerRes.json());
    } catch (e) {
      console.error("Fetch error", e);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', background: 'var(--bg-primary)' }}>
      {/* Sidebar */}
      <nav style={{ 
        width: '260px', 
        borderRight: '1px solid var(--border-subtle)', 
        background: 'var(--bg-secondary)',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 16px'
      }}>
        <div style={{ marginBottom: '32px', paddingLeft: '12px' }}>
          <h2 style={{ fontSize: '20px', display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--accent-primary)' }}>
            <span style={{ fontSize: '24px' }}>⬢</span>
            QoreLogic
          </h2>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px', letterSpacing: '0.05em' }}>
            SOVEREIGN GATEKEEPER
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <NavItem icon={<Icons.Dashboard/>} label="Overview" active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} />
          <NavItem icon={<Icons.List/>} label="Ledger" active={activeTab === 'ledger'} onClick={() => setActiveTab('ledger')} />
          <NavItem icon={<Icons.Folder/>} label="Workspace" active={activeTab === 'workspace'} onClick={() => setActiveTab('workspace')} />
          <NavItem icon={<Icons.Settings/>} label="Environment" active={activeTab === 'environment'} onClick={() => setActiveTab('environment')} />
          <NavItem icon={<Icons.Plus/>} label="New Workspace" active={activeTab === 'new-workspace'} onClick={() => setActiveTab('new-workspace')} />
        </div>

        <div style={{ marginTop: 'auto' }}>
          <div className="glass-panel" style={{ padding: '16px', fontSize: '12px', background: 'rgba(255, 215, 0, 0.03)', borderColor: 'rgba(255, 215, 0, 0.1)' }}>
            <div style={{ color: 'var(--accent-primary)', marginBottom: '8px', fontWeight: 600 }}>SYSTEM STATUS</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: status?.current_mode === 'NORMAL' ? 'var(--success)' : 'var(--warning)', boxShadow: `0 0 10px ${status?.current_mode === 'NORMAL' ? 'var(--success)' : 'var(--warning)'}` }}></div>
              <span style={{ fontWeight: 500 }}>{status?.current_mode || 'OFFLINE'}</span>
            </div>
            <div style={{ color: 'var(--text-secondary)' }}>v2.1.0-alpha</div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main style={{ flex: 1, padding: '40px', overflowY: 'auto' }}>
        <header style={{ marginBottom: '40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontSize: '28px', color: 'var(--text-primary)', marginBottom: '8px' }}>
              {activeTab === 'new-workspace' ? 'Initialize Workspace' : 
               activeTab === 'environment' ? 'System Environment' : 
               activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
            </h1>
            <div style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
              {activeTab === 'overview' && 'Real-time telemetry and system health.'}
              {activeTab === 'ledger' && 'Immutable audit trail of all agent interactions.'}
              {activeTab === 'workspace' && 'Manage files and security context.'}
              {activeTab === 'environment' && 'Configure global QoreLogic variables.'}
              {activeTab === 'new-workspace' && 'Bootstrap a new isolated project environment.'}
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '12px' }}>
             <button className="glass-panel" style={{ padding: '8px 16px', color: 'var(--text-secondary)', cursor: 'pointer', transition: 'all 0.2s' }} onClick={fetchData}>
               Refresh
             </button>
          </div>
        </header>

        {activeTab === 'overview' && <Overview status={status} ledger={ledger} />}
        {activeTab === 'ledger' && <LedgerView ledger={ledger} />}
        {activeTab === 'workspace' && <WorkspaceView />}
        {activeTab === 'environment' && <EnvironmentView />}
        {activeTab === 'new-workspace' && <NewWorkspaceView />}
      </main>
    </div>
  );
}

function NavItem({ icon, label, active, onClick }) {
  return (
    <button 
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        width: '100%',
        padding: '12px 16px',
        background: active ? 'rgba(255, 215, 0, 0.1)' : 'transparent',
        border: 'none',
        borderRadius: '8px',
        color: active ? 'var(--accent-primary)' : 'var(--text-secondary)',
        cursor: 'pointer',
        textAlign: 'left',
        transition: 'all 0.2s',
        borderLeft: active ? '3px solid var(--accent-primary)' : '3px solid transparent'
      }}
    >
      <div style={{ color: active ? 'var(--accent-primary)' : 'inherit' }}>{icon}</div>
      <span style={{ fontWeight: active ? 600 : 400 }}>{label}</span>
    </button>
  )
}

function Overview({ status, ledger }) {
  if (!status) return <div>Connecting to Telemetry...</div>;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
      <MetricCard 
        label="Total Ledger Entries" 
        value={status.total_ledger_entries?.toLocaleString()} 
        trend="+12 this hour"
        color="var(--accent-primary)"
      />
      <MetricCard 
        label="Pending Approvals" 
        value={status.pending_approvals} 
        trend="Requires Attention"
        color={status.pending_approvals > 0 ? "var(--warning)" : "var(--success)"}
      />
       <MetricCard 
        label="Active Agents" 
        value="4" 
        trend="Judge, Sentinel, Scrivener, Overseer"
        color="var(--text-primary)"
      />
      
      <div className="glass-panel" style={{ gridColumn: '1 / -1', padding: '24px' }}>
        <h3 style={{ marginBottom: '20px', fontSize: '16px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Recent Ledger Activity</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0px' }}>
          {ledger.slice(0, 5).map(entry => (
            <div key={entry.entry_id} style={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              padding: '16px 0',
              borderBottom: '1px solid var(--border-subtle)'
            }}>
              <div>
                <div style={{ fontWeight: 500, marginBottom: '6px', color: 'var(--text-primary)' }}>{entry.event_type}</div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{entry.agent_did}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '12px', padding: '4px 8px', borderRadius: '4px', background: 'rgba(255,255,255,0.05)', display: 'inline-block', border: '1px solid var(--border-subtle)' }}>
                  {entry.risk_grade}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px' }}>
                  {new Date(entry.timestamp * 1000).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function MetricCard({ label, value, trend, color }) {
  return (
    <div className="glass-panel" style={{ padding: '24px' }}>
      <div style={{ color: 'var(--text-secondary)', fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>{label}</div>
      <div style={{ fontSize: '36px', fontWeight: 600, marginBottom: '8px', color: color || 'var(--text-primary)', textShadow: `0 0 20px ${color}40` }}>{value}</div>
      <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{trend}</div>
    </div>
  )
}

function LedgerView({ ledger }) {
  return (
    <div className="glass-panel" style={{ overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
        <thead>
          <tr style={{ background: 'rgba(0,0,0,0.2)', borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
            <th style={{ padding: '16px', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '12px', textTransform: 'uppercase' }}>Event</th>
            <th style={{ padding: '16px', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '12px', textTransform: 'uppercase' }}>Agent</th>
            <th style={{ padding: '16px', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '12px', textTransform: 'uppercase' }}>Risk</th>
            <th style={{ padding: '16px', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '12px', textTransform: 'uppercase' }}>Time</th>
            <th style={{ padding: '16px', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '12px', textTransform: 'uppercase' }}>Hash</th>
          </tr>
        </thead>
        <tbody>
          {ledger.map(entry => (
            <tr key={entry.entry_id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
              <td style={{ padding: '16px', color: 'var(--text-primary)' }}>{entry.event_type}</td>
              <td style={{ padding: '16px', color: 'var(--text-secondary)' }}>
                <span style={{ color: 'var(--accent-primary)' }}>●</span> {entry.agent_did.split(':')[2]}
              </td>
              <td style={{ padding: '16px' }}>
                <span style={{ 
                  padding: '4px 8px', 
                  borderRadius: '4px', 
                  fontSize: '11px',
                  fontWeight: 600,
                  background: entry.risk_grade === 'L3' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.1)',
                  color: entry.risk_grade === 'L3' ? '#ef4444' : '#10b981',
                  border: `1px solid ${entry.risk_grade === 'L3' ? '#ef4444' : '#10b981'}40`
                }}>
                  {entry.risk_grade}
                </span>
              </td>
              <td style={{ padding: '16px', color: 'var(--text-secondary)' }}>{new Date(entry.timestamp * 1000).toLocaleString()}</td>
              <td style={{ padding: '16px', fontFamily: 'monospace', color: 'var(--text-secondary)', fontSize: '12px' }}>
                {entry.entry_hash.substring(0, 8)}...
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function WorkspaceView() {
  const [path, setPath] = useState('');
  const [files, setFiles] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/files?path=${path}`)
      .then(res => res.json())
      .then(data => {
        if (data.items) setFiles(data.items);
      });
  }, [path]);

  const handleNavigate = (itemName, isDir) => {
    if (isDir) {
      setPath(prev => prev ? `${prev}/${itemName}` : itemName);
    }
  };

  const handleUp = () => {
    if (!path) return;
    const parts = path.split('/');
    parts.pop();
    setPath(parts.join('/'));
  };

  return (
    <div className="glass-panel" style={{ padding: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px', paddingBottom: '16px', borderBottom: '1px solid var(--border-subtle)' }}>
        <button onClick={handleUp} disabled={!path} style={{ background: 'none', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', fontSize: '18px' }}>&uarr;</button>
        <div style={{ fontFamily: 'monospace', color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.3)', padding: '4px 8px', borderRadius: '4px' }}>root/{path}</div>
      </div>
      
      <div style={{ display: 'grid', gap: '4px' }}>
        {files.map((item, i) => (
          <div key={i} 
            onClick={() => handleNavigate(item.name, item.is_dir)}
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '12px', 
              padding: '12px 16px', 
              background: 'rgba(255,255,255,0.02)', 
              borderRadius: '6px',
              cursor: item.is_dir ? 'pointer' : 'default',
              transition: 'background 0.2s',
              border: '1px solid transparent'
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
            onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
          >
            <div style={{ color: item.is_dir ? 'var(--accent-primary)' : 'var(--text-secondary)' }}>
              {item.is_dir ? <Icons.Folder /> : <Icons.List />}
            </div>
            <span style={{ color: 'var(--text-primary)' }}>{item.name}</span>
            <div style={{ marginLeft: 'auto', fontSize: '12px', color: 'var(--text-secondary)' }}>
               {item.is_dir ? 'DIR' : `${(item.size / 1024).toFixed(1)} KB`}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function EnvironmentView() {
  const [vars, setVars] = useState({
    "QORELOGIC_ENV": "production",
    "QORELOGIC_DB_PATH": "/app/ledger/qorelogic_soa_ledger.db",
    "QORELOGIC_IDENTITY_PASSPHRASE": "********",
    "QORELOGIC_LOG_LEVEL": "INFO",
    "DOCKER_CONTAINER_ID": "a1b2c3d4e5f6"
  });

  return (
    <div className="glass-panel" style={{ padding: '32px', maxWidth: '800px' }}>
      <div style={{ marginBottom: '24px', color: 'var(--text-secondary)' }}>
        These variables define the runtime behavior of the QoreLogic instance. 
        <br/>Warning: Changing these requires a container restart.
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {Object.entries(vars).map(([key, value]) => (
          <div key={key}>
            <label style={{ display: 'block', color: 'var(--accent-primary)', fontSize: '12px', fontWeight: 600, marginBottom: '8px', fontFamily: 'var(--font-mono)' }}>{key}</label>
            <div style={{ display: 'flex', gap: '12px' }}>
              <input 
                type="text" 
                value={value} 
                readOnly
                className="input-field"
                style={{ fontFamily: 'var(--font-mono)' }}
              />
            </div>
          </div>
        ))}
      </div>
      
      <div style={{ marginTop: '32px', paddingTop: '24px', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
        <button style={{ background: 'transparent', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', padding: '8px 16px', borderRadius: '6px' }}>Discard Changes</button>
        <button className="btn-primary">Save Configuration</button>
      </div>
    </div>
  )
}

function NewWorkspaceView() {
  return (
    <div className="glass-panel" style={{ padding: '40px', maxWidth: '600px', margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <div style={{ width: '48px', height: '48px', background: 'var(--accent-primary)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', color: 'var(--bg-primary)' }}>
          <Icons.Plus />
        </div>
        <h2 style={{ fontSize: '24px', marginBottom: '8px' }}>Create New Workspace</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Initialize a sterile QoreLogic environment for a new project.</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div>
          <label style={{ display: 'block', color: 'var(--text-primary)', fontSize: '14px', fontWeight: 500, marginBottom: '8px' }}>Project Name</label>
          <input type="text" placeholder="e.g., Project Alpha" className="input-field" />
        </div>

        <div>
          <label style={{ display: 'block', color: 'var(--text-primary)', fontSize: '14px', fontWeight: 500, marginBottom: '8px' }}>Workspace Root</label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input type="text" placeholder="/src/projects/new-project" className="input-field" />
            <button style={{ padding: '8px 12px', background: 'rgba(255,255,255,0.1)', border: '1px solid var(--border-subtle)', borderRadius: '6px', color: 'var(--text-primary)' }}>Browse</button>
          </div>
        </div>

        <div>
           <label style={{ display: 'block', color: 'var(--text-primary)', fontSize: '14px', fontWeight: 500, marginBottom: '8px' }}>Environment Template</label>
           <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
             <button style={{ padding: '16px', border: '2px solid var(--accent-primary)', borderRadius: '8px', background: 'rgba(255, 215, 0, 0.1)', textAlign: 'left' }}>
               <div style={{ fontWeight: 600, marginBottom: '4px', color: 'var(--text-primary)' }}>Standard</div>
               <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Python 3.11 + L2 Audit</div>
             </button>
             <button style={{ padding: '16px', border: '1px solid var(--border-subtle)', borderRadius: '8px', background: 'transparent', textAlign: 'left', opacity: 0.6 }}>
               <div style={{ fontWeight: 600, marginBottom: '4px', color: 'var(--text-primary)' }}>Strict</div>
               <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>No Network + L3 Audit</div>
             </button>
           </div>
        </div>

        <div>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)', cursor: 'pointer' }}>
            <input type="checkbox" style={{ width: '16px', height: '16px' }} defaultChecked />
            <span>Initialize Git Repository</span>
          </label>
        </div>

        <button className="btn-primary" style={{ marginTop: '16px', padding: '12px' }}>Initialize Workspace</button>
      </div>
    </div>
  )
}

export default App;
