# Guardian Desktop Application

**Priority**: HIGH
**Estimated Time**: 2-3 weeks
**Status**: Not Started

## Overview

Build an Electron desktop application that allows guardians to:
- Securely store their key shares
- Connect to the coordination server
- Participate in threshold signing ceremonies
- View vault status and transaction history

## Architecture

```
Guardian Desktop App (Electron + React)
├── Main Process (Node.js)
│   ├── Key Share Storage (encrypted file system)
│   ├── WebSocket Client (Socket.IO)
│   └── Crypto Operations (threshold signing)
└── Renderer Process (React + TypeScript)
    ├── Setup/Onboarding
    ├── Dashboard
    ├── Transaction Signing UI
    └── Settings
```

## Tasks

### Phase 1: Project Setup (Days 1-2)

- [ ] **1.1 Initialize Electron + React Project**
  - [ ] Create `guardian-app/` directory
  - [ ] Set up Vite + React + TypeScript
  - [ ] Configure Electron with React
  - [ ] Add Tailwind CSS for styling
  - [ ] Set up development hot-reload

- [ ] **1.2 Project Structure**
  ```
  guardian-app/
  ├── src/
  │   ├── main/              # Electron main process
  │   │   ├── main.ts
  │   │   ├── preload.ts
  │   │   └── ipc/           # IPC handlers
  │   ├── renderer/          # React app
  │   │   ├── App.tsx
  │   │   ├── pages/
  │   │   ├── components/
  │   │   ├── services/
  │   │   └── hooks/
  │   └── shared/            # Shared types
  ├── package.json
  ├── vite.config.ts
  └── electron-builder.yml
  ```

- [ ] **1.3 Dependencies**
  - [ ] Install Electron
  - [ ] Install React + React Router
  - [ ] Install Socket.IO client
  - [ ] Install crypto libraries
  - [ ] Install UI components (shadcn/ui or similar)

### Phase 2: Key Share Management (Days 3-5)

- [ ] **2.1 Secure Storage**
  - [ ] Implement encrypted key share storage using Electron's safe-storage API
  - [ ] Create key share import functionality (from JSON file)
  - [ ] Add password/PIN protection for key access
  - [ ] Implement auto-lock after inactivity

- [ ] **2.2 Guardian Setup Flow**
  - [ ] Welcome/onboarding screen
  - [ ] Invitation code entry UI
  - [ ] Key share import wizard
  - [ ] Guardian profile setup (name, contact)
  - [ ] Connection test with coordination server

- [ ] **2.3 Key Share Operations**
  - [ ] Load key share from secure storage
  - [ ] Decrypt key share with password
  - [ ] Display guardian info (without showing private data)
  - [ ] Export backup (encrypted)
  - [ ] Key share rotation support

### Phase 3: Coordination Server Integration (Days 6-8)

- [ ] **3.1 WebSocket Connection**
  - [ ] Implement Socket.IO client in main process
  - [ ] Connection manager with auto-reconnect
  - [ ] Authentication with vault ID and guardian ID
  - [ ] Event handlers for all server events:
    - [ ] `connect` / `disconnect`
    - [ ] `guardian:connected` / `guardian:disconnected`
    - [ ] `signing:round2_ready`
    - [ ] `signing:complete`
    - [ ] `transaction:created`

- [ ] **3.2 Vault Management**
  - [ ] Fetch vault details from server
  - [ ] Display vault status (active, guardians count, etc.)
  - [ ] Show other connected guardians
  - [ ] Real-time status updates

- [ ] **3.3 Transaction Monitoring**
  - [ ] Fetch pending transactions
  - [ ] Subscribe to transaction updates
  - [ ] Display transaction queue
  - [ ] Transaction detail view

### Phase 4: Threshold Signing Implementation (Days 9-11)

- [ ] **4.1 Crypto Integration**
  - [ ] Port threshold signing Python code to TypeScript/Node.js
  - [ ] Or use Python subprocess to execute signing operations
  - [ ] Implement Round 1: Nonce generation
  - [ ] Implement Round 3: Signature share computation
  - [ ] Test vectors to verify correctness

- [ ] **4.2 Signing Workflow**
  - [ ] Transaction approval UI
    - [ ] Display transaction details
    - [ ] Show recipient, amount, fee
    - [ ] Risk indicators (unusual amount, new recipient)
  - [ ] Guardian approval/rejection
  - [ ] Round 1 execution and submission
  - [ ] Wait for Round 2 (server-side)
  - [ ] Round 3 execution and submission
  - [ ] Display final signature

- [ ] **4.3 Security Features**
  - [ ] Transaction verification
  - [ ] Address validation
  - [ ] Amount confirmation
  - [ ] 2FA/biometric approval (optional)
  - [ ] Signing timeout
  - [ ] Multiple signing requests queue

### Phase 5: User Interface (Days 12-14)

- [ ] **5.1 Dashboard**
  - [ ] Guardian status card
  - [ ] Active vaults list
  - [ ] Recent transactions
  - [ ] Pending approvals counter
  - [ ] Connection status indicator

- [ ] **5.2 Transaction Signing Screen**
  - [ ] Transaction details panel
  - [ ] Signing progress indicator (Round 1, 2, 3, 4)
  - [ ] Other guardians status
  - [ ] Approve/Reject buttons
  - [ ] Signature result display

- [ ] **5.3 History View**
  - [ ] Transaction history table
  - [ ] Filter by status, date, type
  - [ ] Export to CSV
  - [ ] Transaction details modal

- [ ] **5.4 Settings**
  - [ ] Connection settings (server URL)
  - [ ] Security settings (auto-lock, password)
  - [ ] Notification preferences
  - [ ] Key share backup/restore
  - [ ] About/version info

### Phase 6: Security & Polish (Days 15-17)

- [ ] **6.1 Security Hardening**
  - [ ] Implement secure IPC between main and renderer
  - [ ] No sensitive data in renderer console
  - [ ] Memory clearing after crypto operations
  - [ ] Secure random number generation
  - [ ] Certificate pinning for server connection

- [ ] **6.2 Error Handling**
  - [ ] Network error recovery
  - [ ] Transaction timeout handling
  - [ ] Key share corruption detection
  - [ ] User-friendly error messages
  - [ ] Logging (without sensitive data)

- [ ] **6.3 User Experience**
  - [ ] Loading states
  - [ ] Progress indicators
  - [ ] Toast notifications
  - [ ] Keyboard shortcuts
  - [ ] Dark mode
  - [ ] Responsive layout

- [ ] **6.4 Testing**
  - [ ] Unit tests for crypto operations
  - [ ] Integration tests with coordination server
  - [ ] E2E tests with Playwright
  - [ ] Security audit checklist
  - [ ] Performance testing

### Phase 7: Packaging & Distribution (Days 18-19)

- [ ] **7.1 Build Configuration**
  - [ ] Configure electron-builder
  - [ ] Set up code signing
  - [ ] Create installer for macOS
  - [ ] Create installer for Windows
  - [ ] Create installer for Linux

- [ ] **7.2 Documentation**
  - [ ] Installation guide
  - [ ] User manual
  - [ ] Troubleshooting guide
  - [ ] Security best practices
  - [ ] Update `/docs/GUARDIAN_APP_IMPLEMENTATION.md`

- [ ] **7.3 Release**
  - [ ] Version 1.0.0-beta
  - [ ] Release notes
  - [ ] Distribution mechanism
  - [ ] Update checking

## Implementation Notes

### Technology Stack

**Frontend:**
- React 18 with TypeScript
- React Router for navigation
- TailwindCSS for styling
- Zustand for state management
- React Query for server state

**Backend (Electron Main):**
- Electron latest
- Socket.IO client
- Node.js crypto or Python subprocess

**Development:**
- Vite for fast development
- ESLint + Prettier
- Playwright for E2E tests
- Jest for unit tests

### Key Design Decisions

1. **Crypto Operations Location**
   - Option A: Port Python crypto to TypeScript/JS
   - Option B: Use Python subprocess for crypto ops
   - **Decision**: Start with Option B (reuse existing Python code), optimize later

2. **Key Storage**
   - Use Electron's `safeStorage` API
   - Encrypt with guardian's password/PIN
   - Store in app's userData directory
   - Backup to external file (encrypted)

3. **Connection Architecture**
   - WebSocket handled in main process
   - Events forwarded to renderer via IPC
   - Signing operations in main process (security)

### Security Considerations

1. **Key Share Protection**
   - Never send unencrypted key share over IPC
   - Clear from memory after use
   - Lock app after inactivity
   - Require authentication for signing

2. **Server Communication**
   - Use TLS/WSS for all connections
   - Verify server certificate
   - Timeout on stale connections
   - Rate limiting on signing requests

3. **Transaction Verification**
   - Display all transaction details clearly
   - Highlight unusual patterns
   - Require explicit user approval
   - Log all signing operations

## Testing Strategy

### Unit Tests
- Crypto operations (nonce generation, signature computation)
- Key share encryption/decryption
- WebSocket message handling
- State management

### Integration Tests
- Connection to coordination server
- Complete signing workflow (all 4 rounds)
- Multi-guardian scenarios
- Error recovery

### E2E Tests
- Complete onboarding flow
- Sign a transaction end-to-end
- Handle disconnection during signing
- App update and restart

### Security Tests
- Key share cannot be extracted
- No sensitive data in logs
- Memory cleared after operations
- IPC security

## Success Criteria

- [ ] Guardian can import key share and connect to server
- [ ] Guardian can see pending transactions
- [ ] Guardian can approve and sign transactions
- [ ] Complete signing workflow works with 3+ guardians
- [ ] App reconnects automatically after network issues
- [ ] Key share is encrypted at rest
- [ ] No private keys visible in UI or console
- [ ] App passes security audit checklist

## Dependencies on Other Tasks

- **02-SECURITY.md**: Need JWT authentication from server
- **03-BLOCKCHAIN.md**: Need actual transaction broadcasting to test signatures

## Resources

- `/docs/GUARDIAN_APP_IMPLEMENTATION.md` - Detailed design spec
- `/coordination-server/README.md` - Server API documentation
- `/test_coordination_server.py` - Reference implementation for signing
- `http://localhost:8000/docs` - Server API docs (when running)

## Questions to Resolve

1. Should we use TypeScript or keep Python for crypto operations?
2. What level of 2FA/biometric should we implement?
3. How to handle guardian key rotation?
4. Should we support multiple vaults per guardian?
5. How to handle app updates without disrupting active signing?
