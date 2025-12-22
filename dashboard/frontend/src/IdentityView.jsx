import { useState, useEffect } from 'react';
import { HostAPI } from './api';

export default function IdentityView() {
  const [identities, setIdentities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [rotating, setRotating] = useState(null);

  const fetchIdentities = async () => {
    try {
      const res = await HostAPI.listIdentities();
      if (res.success && res.identities) {
        setIdentities(res.identities);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchIdentities();
  }, []);

  const handleRotate = async (did) => {
    if (!confirm("Are you sure you want to rotate this key? The old key will be archived.")) return;
    
    setRotating(did);
    const res = await HostAPI.rotateKey(did);
    if (res.success) {
      alert("Key rotated successfully!");
      fetchIdentities();
    } else {
      alert(`Rotation failed: ${res.error}`);
    }
    setRotating(null);
  };

  if (loading) return <div>Loading Identities...</div>;

  return (
    <div className="glass-panel" style={{ padding: '24px' }}>
      <h3 style={{ marginBottom: '24px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Identity Fortress</h3>
      
      <p style={{ marginBottom: '24px', color: 'var(--text-secondary)', fontSize: '14px', maxWidth: '800px' }}>
        Manage sovereign identities and cryptographic keys. 
        Keys are derived using Argon2id (GPU-resistant) and stored locally.
      </p>

      <div style={{ display: 'grid', gap: '16px' }}>
        {identities.map((id) => (
          <div key={id.did} style={{ 
            padding: '20px', 
            background: 'rgba(0,0,0,0.2)', 
            border: '1px solid var(--border-subtle)', 
            borderRadius: '8px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                <span style={{ fontSize: '16px', fontWeight: 600, color: 'var(--accent-primary)' }}>{id.role || 'Unknown Agent'}</span>
                <span style={{ 
                  fontSize: '11px', 
                  padding: '2px 6px', 
                  borderRadius: '4px', 
                  background: id.algorithm === 'argon2id' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                  color: id.algorithm === 'argon2id' ? '#10b981' : '#ef4444',
                  border: '1px solid transparent'
                }}>
                  {id.algorithm?.toUpperCase()}
                </span>
              </div>
              
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                {id.did}
              </div>
              
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Key Age: {Math.floor((Date.now()/1000 - id.created_at) / 86400)} days
              </div>
            </div>

            <button 
              onClick={() => handleRotate(id.did)}
              disabled={rotating === id.did}
              style={{
                padding: '8px 16px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                borderRadius: '6px',
                cursor: 'pointer'
              }}
            >
              {rotating === id.did ? 'Rotating...' : 'Rotate Key'}
            </button>
          </div>
        ))}
        
        {identities.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
            No identities found in keystore.
          </div>
        )}
      </div>
    </div>
  );
}
