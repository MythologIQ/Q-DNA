import { useState, useEffect } from 'react';
import { HostAPI } from './api';

export default function LedgerView() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  const fetchLedger = async () => {
    setLoading(true);
    // Use the Host Bridge to get deeper history directly from SQLite
    const res = await HostAPI.queryHostLedger();
    if (res.success && res.events) {
      setEvents(res.events);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchLedger();
  }, []);

  const filteredEvents = events.filter(e => 
    e.event_type?.toLowerCase().includes(filter.toLowerCase()) ||
    e.agent_did?.toLowerCase().includes(filter.toLowerCase()) ||
    e.payload?.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Toolbar */}
      <div style={{ padding: '16px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <input 
          type="text" 
          placeholder="Filter ledger events..." 
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="input-field"
          style={{ width: '300px' }}
        />
        <button className="btn-secondary" onClick={fetchLedger}>
          Refresh Ledger
        </button>
      </div>

      {/* Table Container */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-secondary)', zIndex: 10 }}>
            <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-subtle)' }}>
              <th style={thStyle}>Event</th>
              <th style={thStyle}>Agent</th>
              <th style={thStyle}>Risk</th>
              <th style={thStyle}>Workspace</th>
              <th style={thStyle}>Time</th>
              <th style={thStyle}>Hash</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="6" style={{ padding: '40px', textAlign: 'center' }}>Loading Ledger...</td></tr>
            ) : filteredEvents.length === 0 ? (
              <tr><td colSpan="6" style={{ padding: '40px', textAlign: 'center' }}>No matching events found.</td></tr>
            ) : (
              filteredEvents.map(entry => (
                <tr key={entry.entry_hash} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '12px 16px', color: 'var(--text-primary)' }}>{entry.event_type}</td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                    {entry.agent_did?.split(':')[2] || 'System'}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                     {/* Risk logic might need adjusting if fields differ in DB vs container API */}
                     <span style={{ 
                        padding: '2px 6px', borderRadius: '4px', fontSize: '11px',
                        background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)' 
                     }}>
                       N/A
                     </span>
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                    {entry.workspace_id || 'default'}
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                    {new Date(entry.timestamp * 1000).toLocaleString()}
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'monospace', fontSize: '12px', color: 'var(--text-secondary)' }}>
                    {entry.entry_hash?.substring(0, 8)}...
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const thStyle = {
  padding: '12px 16px',
  fontWeight: 600,
  color: 'var(--text-secondary)',
  fontSize: '12px',
  textTransform: 'uppercase'
};
