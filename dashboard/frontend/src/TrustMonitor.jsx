import { useState, useEffect } from 'react';
import { HostAPI } from './api';

/**
 * Trust Dynamics Monitor
 * Visualizes the agent's trust score, Lewicki-Bunker stage, and penalty history.
 */
export default function TrustMonitor() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchTrust = async () => {
    // Default to Sentinel for the monitor view
    const res = await HostAPI.trustStatus("did:myth:sentinel"); 
    if (res.success) {
      setData(res);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchTrust();
    const interval = setInterval(fetchTrust, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ color: 'var(--text-secondary)' }}>Initializing Trust Vector...</div>
      </div>
    );
  }

  // Calculate gauge parameters
  const score = data?.score || 1.0;
  const percentage = Math.round(score * 100);
  const radius = 60;
  const stroke = 8;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (score * circumference);
  
  // Color based on score
  let color = 'var(--accent-primary)';
  if (score < 0.5) color = 'var(--error)';
  else if (score < 0.8) color = 'var(--warning)';

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
      {/* Main Score Gauge */}
      <div className="glass-panel" style={{ padding: '32px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <h3 style={{ marginBottom: '24px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Trust Score</h3>
        
        <div style={{ position: 'relative', width: '160px', height: '160px' }}>
          <svg height="160" width="160" style={{ transform: 'rotate(-90deg)' }}>
            <circle
              stroke="rgba(255,255,255,0.1)"
              strokeWidth={stroke}
              r={normalizedRadius}
              cx="80"
              cy="80"
              fill="transparent"
            />
            <circle
              stroke={color}
              strokeWidth={stroke}
              strokeDasharray={circumference + ' ' + circumference}
              style={{ strokeDashoffset, transition: 'stroke-dashoffset 0.5s ease-in-out' }}
              strokeLinecap="round"
              r={normalizedRadius}
              cx="80"
              cy="80"
              fill="transparent"
            />
          </svg>
          <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', fontSize: '32px', fontWeight: 'bold' }}>
            {percentage}%
          </div>
        </div>

        <div style={{ marginTop: '24px', textAlign: 'center' }}>
          <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>TRUST STAGE</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--text-primary)', marginTop: '4px' }}>
            {data?.stage || 'UNKNOWN'}
          </div>
        </div>
      </div>

      {/* Trust Physics Details */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ marginBottom: '16px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Trust Physics</h3>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <MetricRow 
            label="Multiplier (λ)" 
            value={data?.stage_multiplier?.toFixed(2) + 'x'} 
            desc="Impact of penalties based on current stage."
          />
          <MetricRow 
            label="Loss Aversion" 
            value="2.0" 
            desc="Asymmetry between gain and loss (Research: §9.1)"
          />
          <MetricRow 
            label="Decay Rate (δ)" 
            value="0.95" 
            desc="Daily score retention (EWMA)"
          />
          
          <div style={{ padding: '16px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '8px', marginTop: '8px' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#ef4444', marginBottom: '4px' }}>RECENT PENALTIES</div>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
              No recent infractions recorded. System integrity optimal.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricRow({ label, value, desc }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <div>
        <div style={{ fontSize: '14px', color: 'var(--text-primary)', fontWeight: 500 }}>{label}</div>
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{desc}</div>
      </div>
      <div style={{ fontSize: '14px', fontWeight: 'bold', fontFamily: 'var(--font-mono)' }}>{value}</div>
    </div>
  )
}
