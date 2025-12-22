import { useState, useEffect } from 'react';
import { HostAPI, ContainerAPI, ConnectionState } from './api';

/**
 * System Control Panel
 * 
 * Provides lifecycle controls for the QoreLogic system:
 * - Start/Stop container
 * - Connection status indicators
 * - Auto-redirect handling when container comes online
 */
export default function SystemControls({ onStatusChange }) {
  const [hostConnected, setHostConnected] = useState(false);
  const [containerConnected, setContainerConnected] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [stopping, setStopping] = useState(false);

  // Poll connection status
  useEffect(() => {
    const checkStatus = async () => {
      const status = await ConnectionState.checkAll();
      setHostConnected(status.host);
      setContainerConnected(status.container);
      onStatusChange?.(status);
    };

    checkStatus();
    const interval = setInterval(checkStatus, 3000);
    return () => clearInterval(interval);
  }, [onStatusChange]);

  const handleStop = async () => {
    if (!confirm('Stop the QoreLogic system?')) return;
    
    setStopping(true);
    const result = await HostAPI.stop();
    
    if (result.success) {
      setContainerConnected(false);
    } else {
      alert(`Error stopping: ${result.error}`);
    }
    setStopping(false);
  };

  const handleReturnToLauncher = () => {
    window.location.href = 'http://localhost:5500';
  };

  return (
    <div className="glass-panel" style={{ padding: '16px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          {/* Host Status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              background: hostConnected ? 'var(--success)' : 'var(--error)',
              boxShadow: `0 0 8px ${hostConnected ? 'var(--success)' : 'var(--error)'}`
            }} />
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Host {hostConnected ? 'Connected' : 'Offline'}
            </span>
          </div>

          {/* Container Status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              background: containerConnected ? 'var(--success)' : 'var(--warning)',
              boxShadow: `0 0 8px ${containerConnected ? 'var(--success)' : 'var(--warning)'}`
            }} />
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Container {containerConnected ? 'Running' : 'Stopped'}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          {containerConnected ? (
            <button
              onClick={handleStop}
              disabled={stopping || !hostConnected}
              style={{
                padding: '8px 16px',
                background: 'var(--error)',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: stopping ? 'not-allowed' : 'pointer',
                opacity: stopping ? 0.6 : 1,
                fontWeight: 600,
                fontSize: '13px'
              }}
            >
              {stopping ? 'Stopping...' : '⏹ Stop System'}
            </button>
          ) : (
            <button
              onClick={handleReturnToLauncher}
              disabled={!hostConnected}
              style={{
                padding: '8px 16px',
                background: 'var(--accent-primary)',
                color: '#000',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '13px'
              }}
            >
              🚀 Return to Launcher
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
