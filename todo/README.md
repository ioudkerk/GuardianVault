# GuardianVault Development Roadmap

> **Status**: Core MPC coordination server is working! ✅

This folder contains the development roadmap and next steps for GuardianVault.

## Current Status (November 2025)

### ✅ Completed
- [x] Threshold cryptography implementation (additive secret sharing)
- [x] BIP32/BIP44 hierarchical key derivation
- [x] Bitcoin and Ethereum address generation
- [x] 4-round threshold ECDSA signing protocol
- [x] Coordination server with FastAPI + Socket.IO
- [x] MongoDB integration for transaction state
- [x] Complete end-to-end test workflow
- [x] WebSocket real-time communication
- [x] Round-based MPC protocol orchestration

### 🚧 In Progress
- [ ] Guardian Desktop Application (see `01-GUARDIAN-APP.md`)
- [ ] Production security hardening (see `02-SECURITY.md`)

### 📋 Planned
- [ ] Blockchain integration (see `03-BLOCKCHAIN.md`)
- [ ] Admin dashboard (see `04-ADMIN-DASHBOARD.md`)
- [ ] Mobile guardian app (see `05-MOBILE.md`)

## Priority Order

1. **HIGH PRIORITY**: Guardian Desktop App (`01-GUARDIAN-APP.md`)
   - Needed for actual guardian participation
   - Foundation for user experience
   - Estimated: 2-3 weeks

2. **HIGH PRIORITY**: Security Hardening (`02-SECURITY.md`)
   - Critical before any production use
   - JWT authentication, rate limiting, TLS
   - Estimated: 1-2 weeks

3. **MEDIUM PRIORITY**: Blockchain Integration (`03-BLOCKCHAIN.md`)
   - Required to actually broadcast transactions
   - Bitcoin/Ethereum node connections
   - Estimated: 2 weeks

4. **MEDIUM PRIORITY**: Admin Dashboard (`04-ADMIN-DASHBOARD.md`)
   - Vault management and monitoring
   - Guardian oversight
   - Estimated: 2-3 weeks

5. **LOW PRIORITY**: Mobile App (`05-MOBILE.md`)
   - Optional convenience feature
   - Can use desktop app initially
   - Estimated: 3-4 weeks

## Quick Links

- **[01-GUARDIAN-APP.md](01-GUARDIAN-APP.md)** - Guardian Desktop Application (Electron)
- **[02-SECURITY.md](02-SECURITY.md)** - Production security hardening
- **[03-BLOCKCHAIN.md](03-BLOCKCHAIN.md)** - Blockchain integration for transaction broadcasting
- **[04-ADMIN-DASHBOARD.md](04-ADMIN-DASHBOARD.md)** - Admin web dashboard
- **[05-MOBILE.md](05-MOBILE.md)** - Mobile guardian application
- **[99-FUTURE-ENHANCEMENTS.md](99-FUTURE-ENHANCEMENTS.md)** - Long-term vision

## Development Workflow

### Before Starting Any Task

1. Read the specific todo file for that component
2. Review relevant documentation in `/docs`
3. Test the coordination server to ensure it's working
4. Create a feature branch: `git checkout -b feature/task-name`

### Testing Requirements

All new features must include:
- Unit tests for core logic
- Integration tests with coordination server
- Security review checklist
- Documentation updates

### Getting Started

```bash
# 1. Ensure coordination server is working
cd coordination-server
/Users/ivan/.virtualenvs/claude-mcp/bin/python -m app.main

# 2. Test complete workflow
/Users/ivan/.virtualenvs/claude-mcp/bin/python test_coordination_server.py

# 3. Start working on Guardian App
cd guardian-app
npm install
npm run dev
```

## Contributing

When completing tasks:
1. Check off completed items in the relevant todo file
2. Update this README with current status
3. Document any architectural decisions
4. Add tests for new functionality
5. Update main documentation in `/docs`

## Questions?

- Technical questions: See `/docs/CLAUDE.md`
- Architecture questions: See `/docs/ARCHITECTURE_THRESHOLD.md`
- Coordination server: See `/coordination-server/README.md`
- Guardian app design: See `/docs/GUARDIAN_APP_IMPLEMENTATION.md`
