# Admin Web Dashboard

**Priority**: MEDIUM
**Estimated Time**: 2-3 weeks
**Status**: Not Started

## Overview

Build a web-based admin dashboard for managing vaults, guardians, and monitoring system activity. This is a separate application from the Guardian Desktop App.

## Architecture

```
Admin Dashboard (React Web App)
├── Authentication (Admin login)
├── Vault Management
├── Guardian Management
├── Transaction Monitoring
├── Analytics & Reports
└── System Settings
```

## Tasks

### Phase 1: Project Setup (Days 1-2)

- [ ] **1.1 Initialize React Project**
  - [ ] Create `admin-dashboard/` directory
  - [ ] Set up Vite + React + TypeScript
  - [ ] Add React Router
  - [ ] Add Tailwind CSS
  - [ ] Configure build pipeline

- [ ] **1.2 Authentication System**
  - [ ] Admin login page
  - [ ] JWT token handling
  - [ ] Protected routes
  - [ ] Session management
  - [ ] Logout functionality

- [ ] **1.3 Layout Components**
  - [ ] Sidebar navigation
  - [ ] Top bar with user menu
  - [ ] Page containers
  - [ ] Loading states
  - [ ] Error boundaries

### Phase 2: Vault Management (Days 3-6)

- [ ] **2.1 Vault List View**
  - [ ] Display all vaults
  - [ ] Filter by status (active, setup, archived)
  - [ ] Search by name
  - [ ] Sort by date, name, balance
  - [ ] Pagination

- [ ] **2.2 Create New Vault**
  - [ ] Vault creation form
    - [ ] Name
    - [ ] Coin type (Bitcoin/Ethereum)
    - [ ] Threshold (K)
    - [ ] Total guardians (N)
    - [ ] Account index
  - [ ] Form validation
  - [ ] Success confirmation
  - [ ] Error handling

- [ ] **2.3 Vault Detail View**
  - [ ] Basic info (name, coin, threshold)
  - [ ] Status badge
  - [ ] Guardian list
  - [ ] Recent transactions
  - [ ] Balance display
  - [ ] Address list
  - [ ] Edit vault details
  - [ ] Archive vault

- [ ] **2.4 Vault Actions**
  - [ ] Activate vault (after guardians join)
  - [ ] Pause vault
  - [ ] Archive vault
  - [ ] Export vault data
  - [ ] View audit log

### Phase 3: Guardian Management (Days 7-9)

- [ ] **3.1 Guardian List View**
  - [ ] Display all guardians
  - [ ] Filter by vault, status
  - [ ] Search by name, email
  - [ ] Show connection status
  - [ ] Last active timestamp

- [ ] **3.2 Invite New Guardian**
  - [ ] Invitation form
    - [ ] Select vault
    - [ ] Guardian name
    - [ ] Email address
    - [ ] Role/description
  - [ ] Generate invitation code
  - [ ] Display invitation code
  - [ ] Send email (optional)
  - [ ] Copy to clipboard

- [ ] **3.3 Guardian Detail View**
  - [ ] Basic info (name, email, role)
  - [ ] Associated vaults
  - [ ] Signing statistics
    - [ ] Total signatures
    - [ ] Success rate
    - [ ] Average response time
  - [ ] Recent activity
  - [ ] Connection history

- [ ] **3.4 Guardian Actions**
  - [ ] Edit guardian info
  - [ ] Revoke invitation
  - [ ] Remove guardian
  - [ ] Reset guardian key (if compromised)
  - [ ] View audit log

### Phase 4: Transaction Monitoring (Days 10-12)

- [ ] **4.1 Transaction List View**
  - [ ] Display all transactions
  - [ ] Filter by vault, status, type
  - [ ] Search by txid, recipient
  - [ ] Sort by date, amount
  - [ ] Status badges (pending, signing, completed, failed)
  - [ ] Pagination

- [ ] **4.2 Create New Transaction**
  - [ ] Transaction form
    - [ ] Select vault
    - [ ] Recipient address
    - [ ] Amount
    - [ ] Fee level (low, medium, high)
    - [ ] Memo/description
  - [ ] Address validation
  - [ ] Balance check
  - [ ] Fee estimation
  - [ ] Confirmation dialog
  - [ ] Submit to coordination server

- [ ] **4.3 Transaction Detail View**
  - [ ] Transaction info
    - [ ] Type, status, amount
    - [ ] Recipient address
    - [ ] Fee, memo
    - [ ] Message hash
  - [ ] Signing progress
    - [ ] Round status (1, 2, 3, 4)
    - [ ] Guardian signatures received
    - [ ] Waiting for guardians
  - [ ] Final signature (r, s)
  - [ ] Blockchain link
  - [ ] Confirmation count

- [ ] **4.4 Transaction Actions**
  - [ ] View on blockchain explorer
  - [ ] Cancel pending transaction (if possible)
  - [ ] Retry failed transaction
  - [ ] Export transaction data

### Phase 5: Real-Time Updates (Days 13-14)

- [ ] **5.1 WebSocket Integration**
  - [ ] Connect to coordination server
  - [ ] Subscribe to vault events
  - [ ] Subscribe to transaction events
  - [ ] Handle disconnections

- [ ] **5.2 Live Status Updates**
  - [ ] Guardian connection/disconnection
  - [ ] Transaction status changes
  - [ ] Signing round progress
  - [ ] New transactions created
  - [ ] Toast notifications

- [ ] **5.3 Dashboard Page**
  - [ ] System overview
    - [ ] Total vaults
    - [ ] Active guardians
    - [ ] Pending transactions
    - [ ] System health
  - [ ] Recent activity feed
  - [ ] Quick actions
  - [ ] Alerts/warnings

### Phase 6: Analytics & Reports (Days 15-17)

- [ ] **6.1 Analytics Dashboard**
  - [ ] Charts and graphs
    - [ ] Transaction volume over time
    - [ ] Signing success rate
    - [ ] Guardian activity
    - [ ] Average signing time
  - [ ] Key metrics
    - [ ] Total transaction value
    - [ ] Average transaction size
    - [ ] Most active vaults
    - [ ] Guardian response times

- [ ] **6.2 Reports**
  - [ ] Generate reports
    - [ ] Transaction history (date range)
    - [ ] Guardian activity
    - [ ] Vault summary
    - [ ] Audit trail
  - [ ] Export formats (PDF, CSV, JSON)
  - [ ] Scheduled reports (optional)

- [ ] **6.3 Audit Log**
  - [ ] Display all audit events
  - [ ] Filter by event type, user, date
  - [ ] Search audit log
  - [ ] Export audit log
  - [ ] Immutable audit trail

### Phase 7: System Settings (Days 18-19)

- [ ] **7.1 Configuration**
  - [ ] Server settings
    - [ ] Coordination server URL
    - [ ] MongoDB connection
    - [ ] API keys
  - [ ] Security settings
    - [ ] Session timeout
    - [ ] Password policy
    - [ ] 2FA settings
  - [ ] Notification settings
    - [ ] Email alerts
    - [ ] Webhook URLs

- [ ] **7.2 User Management**
  - [ ] Admin users list
  - [ ] Create new admin
  - [ ] Edit admin permissions
  - [ ] Deactivate admin
  - [ ] Role-based access control

- [ ] **7.3 System Health**
  - [ ] Coordination server status
  - [ ] MongoDB status
  - [ ] Blockchain node status
  - [ ] System logs
  - [ ] Error monitoring

### Phase 8: Polish & Testing (Days 20-21)

- [ ] **8.1 UI/UX Polish**
  - [ ] Consistent styling
  - [ ] Loading states
  - [ ] Error messages
  - [ ] Empty states
  - [ ] Responsive design (mobile-friendly)
  - [ ] Dark mode (optional)

- [ ] **8.2 Testing**
  - [ ] Unit tests for components
  - [ ] Integration tests with API
  - [ ] E2E tests with Playwright
  - [ ] Accessibility testing
  - [ ] Performance testing

- [ ] **8.3 Documentation**
  - [ ] Admin user guide
  - [ ] Deployment guide
  - [ ] API documentation
  - [ ] Troubleshooting guide

## Technology Stack

**Frontend:**
- React 18 with TypeScript
- React Router for navigation
- TailwindCSS + shadcn/ui
- React Query for data fetching
- Chart.js or Recharts for analytics
- Socket.IO client for real-time updates

**Build Tools:**
- Vite for development and build
- ESLint + Prettier
- Playwright for E2E tests
- Vitest for unit tests

## API Integration

### REST API Endpoints

```typescript
// Vaults
GET    /api/vaults
POST   /api/vaults
GET    /api/vaults/:id
PATCH  /api/vaults/:id
DELETE /api/vaults/:id
POST   /api/vaults/:id/activate

// Guardians
GET    /api/guardians
POST   /api/guardians/invite
GET    /api/guardians/:id
PATCH  /api/guardians/:id
DELETE /api/guardians/:id

// Transactions
GET    /api/transactions
POST   /api/transactions
GET    /api/transactions/:id
PATCH  /api/transactions/:id
DELETE /api/transactions/:id
```

### WebSocket Events

```typescript
// Subscribe to vault events
socket.emit('subscribe:vault', { vaultId });

// Listen for events
socket.on('vault:updated', (data) => {});
socket.on('guardian:connected', (data) => {});
socket.on('transaction:created', (data) => {});
socket.on('transaction:completed', (data) => {});
socket.on('signing:round2_ready', (data) => {});
```

## Security Considerations

1. **Authentication**
   - Admin-only access
   - Strong password requirements
   - 2FA recommended
   - Session timeout

2. **Authorization**
   - Role-based permissions
   - API key for admin operations
   - Audit all admin actions

3. **Data Protection**
   - No display of private keys
   - Redact sensitive data in logs
   - Secure API communication (HTTPS)

4. **Input Validation**
   - Validate all form inputs
   - Sanitize user input
   - Prevent XSS attacks

## Deployment

### Development
```bash
cd admin-dashboard
npm install
npm run dev
# Runs at http://localhost:5173
```

### Production Build
```bash
npm run build
# Deploy build/ directory to web server
```

### Docker (Optional)
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## Success Criteria

- [ ] Admin can log in securely
- [ ] Can create and manage vaults
- [ ] Can invite and manage guardians
- [ ] Can create and monitor transactions
- [ ] Real-time updates work
- [ ] Analytics provide useful insights
- [ ] Audit log is complete
- [ ] UI is responsive and intuitive
- [ ] All tests pass

## Dependencies on Other Tasks

- **02-SECURITY.md**: Needs admin API authentication
- **03-BLOCKCHAIN.md**: Needs blockchain integration for transaction monitoring

## Resources

- `/docs/UI_ARCHITECTURE.md` - UI design specification
- `/coordination-server/README.md` - API documentation
- `http://localhost:8000/docs` - Interactive API docs
- [shadcn/ui](https://ui.shadcn.com/) - UI components
- [React Query](https://tanstack.com/query) - Data fetching
