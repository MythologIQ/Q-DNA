# QoreLogic Dashboard Frontend

**Version:** 9.0
**Technology:** React + Vite
**Purpose:** Web-based interface for monitoring and controlling QoreLogic governance system

---

## Overview

The QoreLogic Dashboard provides a real-time visual interface for:

- **System Monitoring**: Track verification pipeline status, agent health, and system performance
- **Agent Management**: View and configure Scrivener, Sentinel, Judge, and Overseer agents
- **Trust Dynamics**: Monitor Source Credibility Index (SCI) and agent trust scores
- **Audit Trail**: Browse the SOA Ledger and verification history
- **Control Interface**: Switch operational modes (NORMAL, LEAN, SURGE, SAFE)

---

## Features

### System Controls

- Real-time system status display
- Operational mode switching with confirmation
- Resource utilization monitoring (CPU, RAM, queue depth)
- Emergency SAFE mode activation

### Agents View

- Agent status and health indicators
- Trust score visualization with decay trends
- Performance metrics and SLA compliance
- L3 approval queue management

### Audit & Compliance

- SOA Ledger browser with filtering
- Verification history search
- GDPR Article 22 trigger alerts
- Compliance status indicators

---

## Technology Stack

- **Frontend**: React 18 with Vite for fast development
- **Styling**: CSS with responsive design
- **API Communication**: RESTful API calls to QoreLogic backend
- **State Management**: React hooks for local state
- **Build Tool**: Vite with HMR for development

---

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
npm install
```

### Development Server

```bash
npm run dev
```

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

---

## API Integration

The frontend communicates with the QoreLogic MCP server via the API layer:

- **Endpoint**: `http://localhost:8001` (default)
- **Authentication**: DID-based identity verification
- **Data Format**: JSON with Pydantic schema validation

Key API endpoints:

- `/api/system/status` - System health and mode
- `/api/agents/list` - Agent registry and status
- `/api/ledger/events` - SOA Ledger access
- `/api/trust/scores` - Trust dynamics data

---

## Security Considerations

- All API calls require valid DID authentication
- Sensitive data (PII) is redacted before display
- No local storage of audit trail data
- HTTPS required for production deployment

---

## Troubleshooting

### Common Issues

1. **API Connection Failed**

   - Verify QoreLogic backend is running on port 8001
   - Check firewall settings
   - Ensure DID authentication is configured

2. **Real-time Updates Not Working**

   - Verify WebSocket connection is established
   - Check browser console for connection errors
   - Refresh the page to re-establish connection

3. **Trust Scores Not Updating**
   - Verify backend trust engine is active
   - Check for agent activity in the system
   - Review audit logs for trust calculation events

---

## Contributing

When contributing to the dashboard frontend:

1. Follow QoreLogic's L1/L2/L3 risk grading for changes
2. All UI changes require visual testing in multiple browsers
3. API changes must maintain backward compatibility
4. Security-related changes require L3 approval

---

## License

Apache License 2.0 - See [../../../LICENSE](../../../LICENSE)
