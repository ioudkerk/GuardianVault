# GuardianVault - User Interface Architecture

> **Complete Enterprise Solution: Admin Dashboard + Guardian Apps**

## 🎯 System Overview

GuardianVault consists of 3 main components:

1. **Admin Web Dashboard** - Vault management, guardian coordination
2. **Guardian Desktop App** (Electron) - Secure share storage, transaction signing
3. **Coordination Server** (Backend API) - Multi-party protocol coordination

---

## 🏗️ Complete Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GUARDIANVAULT ECOSYSTEM                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   Admin Dashboard    │  (Web - React/Next.js)
│   (Vault Manager)    │
└──────────┬───────────┘
           │
           │ HTTPS/WebSocket
           │
           ▼
┌──────────────────────┐
│  Coordination Server │  (Node.js/Python FastAPI)
│   - API Endpoints    │
│   - WebSocket Hub    │  ← Real-time coordination
│   - Transaction Pool │
│   - Audit Logs       │
└──────────┬───────────┘
           │
           │ WebSocket/HTTPS
           │
     ┌─────┴─────┬─────────┬─────────┐
     │           │         │         │
     ▼           ▼         ▼         ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│Guardian │ │Guardian │ │Guardian │ │Guardian │
│ App #1  │ │ App #2  │ │ App #3  │ │ App #4  │
│(Electron)│ │(Electron)│ │(Electron)│ │(Electron)│
└─────────┘ └─────────┘ └─────────┘ └─────────┘
   CFO         CTO         CEO       Board Member

Each Guardian App:
- Stores share encrypted locally
- Signs transactions with their share
- Never reconstructs full private key
```

---

## 1️⃣ Admin Web Dashboard

### 🎨 Pages & Features

#### **1.1 Dashboard Home**
```
┌─────────────────────────────────────────────────────┐
│ GuardianVault                        [Admin: CFO]  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  📊 Overview                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐│
│  │  Total Value │ │ Active Vaults│ │  Guardians  ││
│  │   $2.5M      │ │      3       │ │   5 Active  ││
│  └──────────────┘ └──────────────┘ └─────────────┘│
│                                                      │
│  🔔 Pending Approvals (2)                          │
│  ┌────────────────────────────────────────────────┐│
│  │ ⏳ Withdraw 0.5 BTC → Vendor Payment           ││
│  │    Status: 2/3 signatures | Created: 2h ago   ││
│  │    [View Details]                              ││
│  ├────────────────────────────────────────────────┤│
│  │ ⏳ New Guardian Invitation                     ││
│  │    Status: Pending | Expires: 24h             ││
│  │    [Resend Invite]                             ││
│  └────────────────────────────────────────────────┘│
│                                                      │
│  💼 Recent Activity                                 │
│  • CFO approved withdrawal request                  │
│  • New deposit address generated                    │
│  • CTO signed transaction #1234                     │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Real-time overview of vault status
- Pending transaction approvals
- Guardian activity feed
- Quick actions (generate address, propose transaction)
- Asset portfolio view (BTC, ETH)

#### **1.2 Vaults Management**
```
┌─────────────────────────────────────────────────────┐
│ Vaults                              [+ Create Vault]│
├─────────────────────────────────────────────────────┤
│                                                      │
│  🏦 Treasury Vault - Main                          │
│  Type: Threshold (3-of-5) | BTC + ETH              │
│  Balance: 10.5 BTC ($450K) | 250 ETH ($400K)       │
│  Guardians: CFO, CTO, CEO, Board#1, Board#2        │
│  [View] [Generate Address] [Propose Transaction]   │
│                                                      │
│  🔒 Cold Storage Vault                             │
│  Type: Shamir SSS (3-of-5) | BTC Only              │
│  Balance: 50 BTC ($2.1M)                           │
│  Last Access: 45 days ago                          │
│  [View] [Reconstruct]                              │
│                                                      │
│  💳 Operations Vault                               │
│  Type: Threshold (2-of-3) | ETH Only               │
│  Balance: 100 ETH ($160K)                          │
│  Guardians: CFO, Finance Manager, Controller       │
│  [View] [Generate Address] [Propose Transaction]   │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Create new vaults with different security models
- Configure threshold (2-of-3, 3-of-5, etc.)
- Multi-asset support (BTC, ETH per vault)
- Vault templates (Treasury, Cold Storage, Operations)
- Balance and transaction history per vault

#### **1.3 Guardian Management**
```
┌─────────────────────────────────────────────────────┐
│ Guardians                        [+ Invite Guardian]│
├─────────────────────────────────────────────────────┤
│                                                      │
│  Active Guardians (5)                               │
│                                                      │
│  👤 John Smith (CFO)                               │
│  Email: john@company.com | Status: ✅ Active        │
│  Devices: Desktop (Win), Mobile (iOS)              │
│  Last Active: 2 hours ago                          │
│  Vaults: Treasury (3/5), Operations (2/3)          │
│  [View Details] [Remove] [Reset Share]             │
│                                                      │
│  👤 Sarah Johnson (CTO)                            │
│  Email: sarah@company.com | Status: ✅ Active       │
│  Devices: Desktop (macOS)                          │
│  Last Active: 5 hours ago                          │
│  Vaults: Treasury (3/5)                            │
│  Hardware Key: YubiKey #AB123 🔑                   │
│  [View Details] [Remove] [Reset Share]             │
│                                                      │
│  ⏳ Pending Invitations (1)                        │
│  📧 mike@company.com (Board Member)                │
│  Invited: 2 days ago | Expires: 5 days             │
│  [Resend] [Cancel]                                 │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Invite guardians via email
- Role-based permissions (Admin, Guardian, Auditor)
- Guardian device management
- Hardware key registration
- Share recovery/reset process
- Activity monitoring per guardian

#### **1.4 Transactions & Approvals**
```
┌─────────────────────────────────────────────────────┐
│ Transactions                   [+ Propose New TX]   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Filters: [All] [Pending] [Approved] [Executed]    │
│                                                      │
│  ⏳ PENDING - TX#1234                              │
│  Withdraw 0.5 BTC → 1A1zP1eP5QG...                 │
│  Purpose: Vendor Payment - Monthly Services         │
│  Vault: Treasury (3-of-5 threshold)                │
│  ┌──────────────────────────────────────────────┐  │
│  │ Signatures: 2/3 required                     │  │
│  │ ✅ CFO (John Smith) - 2 hours ago            │  │
│  │ ✅ CTO (Sarah Johnson) - 1 hour ago          │  │
│  │ ⏳ CEO (Pending)                             │  │
│  │ ⏳ Board#1 (Pending)                         │  │
│  │ ⏳ Board#2 (Pending)                         │  │
│  └──────────────────────────────────────────────┘  │
│  [View Details] [Cancel] [Remind Guardians]        │
│                                                      │
│  ✅ EXECUTED - TX#1233                             │
│  Withdraw 1.0 BTC → 3FZbgi29...                    │
│  Executed: 1 day ago | Confirmations: 6            │
│  [View on Explorer] [Download Receipt]             │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Propose new transactions with metadata
- Real-time signature status
- Transaction approval workflow
- Cancel pending transactions
- Notification to guardians
- Transaction history and audit trail
- Export reports (CSV, PDF)

#### **1.5 Address Management**
```
┌─────────────────────────────────────────────────────┐
│ Addresses                      [+ Generate Address] │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Treasury Vault - Bitcoin Addresses                 │
│                                                      │
│  🔵 Active (10 addresses)                           │
│  1A1zP1eP5QGefi2DMPTfTL...  | Balance: 2.5 BTC    │
│  Label: Client Deposit 2024-11                     │
│  Path: m/44'/0'/0'/0/5                             │
│  [View] [Copy] [QR Code] [Label]                   │
│                                                      │
│  3FZbgi29cpjq2GjdwV8eyHuJ... | Balance: 0.8 BTC    │
│  Label: Exchange Withdrawal                         │
│  [View] [Copy] [QR Code] [Label]                   │
│                                                      │
│  ⚪ Unused (50 addresses)                           │
│  [Show All] [Batch Generate]                       │
│                                                      │
│  💡 Generate New Address                            │
│  ┌────────────────────────────────────────────────┐│
│  │ Label: ________________  [Generate BTC Address]││
│  │                          [Generate ETH Address]││
│  └────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

**Features:**
- Generate addresses without guardian interaction
- Label and organize addresses
- QR code generation
- Balance tracking per address
- Batch address generation
- CSV import/export

#### **1.6 Audit Logs**
```
┌─────────────────────────────────────────────────────┐
│ Audit Logs                          [Export Logs]  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Filters: [All] [Auth] [Transactions] [Guardians]  │
│  Date Range: [Last 30 Days ▼]                      │
│                                                      │
│  📅 2025-11-04 10:23:15 | User: john@company.com   │
│  Action: TRANSACTION_PROPOSED                       │
│  Details: Withdraw 0.5 BTC from Treasury           │
│  IP: 192.168.1.100 | Device: Chrome/Desktop        │
│                                                      │
│  📅 2025-11-04 09:15:42 | User: sarah@company.com  │
│  Action: TRANSACTION_SIGNED                         │
│  Details: TX#1234 signed with share #2             │
│  IP: 10.0.0.50 | Device: Guardian App/macOS        │
│                                                      │
│  📅 2025-11-03 16:45:23 | System                   │
│  Action: ADDRESS_GENERATED                          │
│  Details: New BTC address at path m/44'/0'/0'/0/10 │
│  Triggered By: admin@company.com                    │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Complete audit trail of all actions
- Filter by user, action type, date
- Export for compliance (PDF, CSV)
- Tamper-proof logging
- Integration with SIEM systems

---

## 2️⃣ Guardian Desktop App (Electron)

### 🎨 Interface & Features

#### **2.1 Setup Wizard**
```
┌─────────────────────────────────────────────────────┐
│         GuardianVault - Guardian Setup               │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Step 1 of 4: Welcome                               │
│                                                      │
│  🛡️ Welcome, Guardian!                              │
│                                                      │
│  You've been invited to be a guardian for:          │
│  Company: Acme Corp                                 │
│  Vault: Treasury Vault                              │
│  Role: CFO Guardian (3-of-5 threshold)              │
│                                                      │
│  Your share will be securely stored on this device. │
│  You'll need to approve transactions collaboratively│
│  with other guardians.                              │
│                                                      │
│                         [Continue →]                │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│         GuardianVault - Guardian Setup               │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Step 2 of 4: Secure Your Share                    │
│                                                      │
│  🔐 Set Master Password                             │
│  Your share will be encrypted with this password.   │
│                                                      │
│  Password: ____________________________             │
│  Confirm:  ____________________________             │
│                                                      │
│  Strength: ████████████████░░ Very Strong           │
│                                                      │
│  ☐ Enable biometric unlock (TouchID/FaceID)        │
│  ☐ Require hardware key (YubiKey) for signing      │
│                                                      │
│              [← Back]        [Continue →]           │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│         GuardianVault - Guardian Setup               │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Step 3 of 4: Receive Your Share                   │
│                                                      │
│  🔗 Connecting to GuardianVault server...           │
│  Status: ✅ Connected                               │
│                                                      │
│  Receiving encrypted share from coordinator...      │
│  ████████████████████████ 100%                      │
│                                                      │
│  ✅ Share received and encrypted                    │
│  ✅ Stored securely on this device                  │
│                                                      │
│  Share ID: #2 of 5                                  │
│  Vault: Treasury                                    │
│  Threshold: 3-of-5 signatures required              │
│                                                      │
│              [← Back]        [Continue →]           │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│         GuardianVault - Guardian Setup               │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Step 4 of 4: Backup Your Share                    │
│                                                      │
│  ⚠️ CRITICAL: Backup your encrypted share           │
│                                                      │
│  Options:                                           │
│  ┌────────────────────────────────────────────────┐│
│  │ 💾 [Export to USB Drive]                       ││
│  │    Store encrypted backup on external drive    ││
│  │                                                 ││
│  │ ☁️  [Backup to Cloud]                          ││
│  │    Encrypted backup to Google Drive/iCloud     ││
│  │                                                 ││
│  │ 🖨️  [Print Recovery Sheet]                     ││
│  │    Print encrypted share for safe storage      ││
│  └────────────────────────────────────────────────┘│
│                                                      │
│  ☐ I understand losing access means losing my vote │
│                                                      │
│              [← Back]        [Complete Setup]       │
└─────────────────────────────────────────────────────┘
```

#### **2.2 Main Dashboard**
```
┌─────────────────────────────────────────────────────┐
│ GuardianVault           👤 John Smith (CFO)  [⚙️]  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  🔔 Notifications (2)                               │
│  ┌────────────────────────────────────────────────┐│
│  │ 🔴 URGENT: Signature Required                  ││
│  │ Withdraw 0.5 BTC → Vendor Payment              ││
│  │ Signatures: 2/3 | Expires in 4 hours           ││
│  │ [Review & Sign]                                ││
│  ├────────────────────────────────────────────────┤│
│  │ 📧 New Guardian Added                          ││
│  │ Mike Wilson joined as Board Member             ││
│  │ 2 hours ago                                    ││
│  └────────────────────────────────────────────────┘│
│                                                      │
│  📊 Your Status                                     │
│  ┌────────────────────────────────────────────────┐│
│  │ Guardian ID: #2 of 5                          │ │
│  │ Vault: Treasury (3-of-5 threshold)            │ │
│  │ Share Status: ✅ Secured & Encrypted          │ │
│  │ Last Signed: 2 days ago                       │ │
│  │ Total Signatures: 47                          │ │
│  └────────────────────────────────────────────────┘│
│                                                      │
│  📜 Recent Activity                                 │
│  • ✅ You signed TX#1230 (3 days ago)              │
│  • 📥 New transaction proposed (2 hours ago)       │
│  • ✅ CTO signed TX#1234 (5 hours ago)             │
│                                                      │
│  [View All Transactions] [Settings]                │
└─────────────────────────────────────────────────────┘
```

#### **2.3 Transaction Signing**
```
┌─────────────────────────────────────────────────────┐
│ Sign Transaction                        [X] Close   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Transaction Details                                │
│  ┌────────────────────────────────────────────────┐│
│  │ TX ID: #1234                                   ││
│  │ Type: Withdrawal                               ││
│  │ Amount: 0.5 BTC ($21,500)                      ││
│  │ To: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa          ││
│  │                                                 ││
│  │ Purpose: Vendor Payment - Monthly Services     ││
│  │ Proposed by: admin@company.com                 ││
│  │ Proposed: 2 hours ago                          ││
│  │                                                 ││
│  │ Vault: Treasury                                ││
│  │ Network: Bitcoin Mainnet                       ││
│  │ Fee: 0.0001 BTC (Standard)                     ││
│  └────────────────────────────────────────────────┘│
│                                                      │
│  Current Signatures: 2/3 Required                   │
│  ✅ CFO (John Smith) - 2 hours ago                 │
│  ✅ CTO (Sarah Johnson) - 1 hour ago               │
│  ⏳ CEO - Waiting...                               │
│                                                      │
│  ⚠️ Warning: This action cannot be undone          │
│                                                      │
│  [ ] I have verified the recipient address          │
│  [ ] I approve this transaction                     │
│                                                      │
│         [Reject]              [Sign Transaction]    │
│                                                      │
│  🔒 Requires: Master Password + Hardware Key        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Authenticate to Sign                                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  🔐 Enter Master Password                           │
│  Password: ____________________________             │
│                                                      │
│  🔑 Insert Hardware Key (YubiKey)                   │
│  Status: ⏳ Waiting for key...                      │
│                                                      │
│  [Cancel]                [Authenticate]             │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Signing in Progress...                              │
├─────────────────────────────────────────────────────┤
│                                                      │
│  🔄 Computing signature with your share...          │
│  ████████████████░░░░░░░░░░ 60%                     │
│                                                      │
│  1. Decrypting your share... ✅                     │
│  2. Generating nonce... ✅                          │
│  3. Computing signature share... ⏳                 │
│  4. Sending to coordinator... ⏳                    │
│                                                      │
│  Please wait...                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Transaction Signed! ✅                              │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ✅ Your signature has been recorded                │
│                                                      │
│  TX ID: #1234                                       │
│  Your Signature: 3/3 signatures collected           │
│                                                      │
│  🎉 Transaction is now ready for execution!         │
│                                                      │
│  The transaction will be broadcast to the Bitcoin   │
│  network within the next 5 minutes.                 │
│                                                      │
│  [View Transaction] [Back to Dashboard]             │
└─────────────────────────────────────────────────────┘
```

#### **2.4 Settings & Security**
```
┌─────────────────────────────────────────────────────┐
│ Settings                                    [X]     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  📱 Account                                         │
│  Email: john@company.com                           │
│  Role: CFO Guardian                                │
│  Member Since: Oct 15, 2025                        │
│  [Edit Profile]                                    │
│                                                      │
│  🔒 Security                                        │
│  ✅ Master Password Set                            │
│  ✅ Hardware Key Registered (YubiKey #AB123)       │
│  ✅ Biometric Unlock Enabled (TouchID)             │
│  [Change Password] [Manage Hardware Keys]          │
│                                                      │
│  💾 Backup & Recovery                              │
│  Last Backup: 5 days ago                           │
│  Location: USB Drive E:\                           │
│  [Backup Now] [Restore from Backup]                │
│                                                      │
│  🔔 Notifications                                   │
│  ☑️ Transaction approvals                          │
│  ☑️ New guardians added                            │
│  ☑️ System updates                                 │
│  ☐ Daily digest email                              │
│                                                      │
│  🌐 Network                                         │
│  Server: https://vault.company.com                 │
│  Status: ✅ Connected                               │
│  [Test Connection]                                 │
│                                                      │
│  ℹ️ About                                           │
│  Version: 1.0.0                                    │
│  [Check for Updates] [View Logs]                   │
└─────────────────────────────────────────────────────┘
```

---

## 3️⃣ Coordination Server (Backend)

### 🔧 Core Services

```python
# FastAPI Backend Structure

/api/v1/
├── /auth
│   ├── POST /login              # Admin login
│   ├── POST /logout
│   └── POST /refresh-token
│
├── /guardians
│   ├── GET  /                   # List all guardians
│   ├── POST /invite             # Invite new guardian
│   ├── GET  /:id                # Guardian details
│   ├── PUT  /:id                # Update guardian
│   └── DELETE /:id              # Remove guardian
│
├── /vaults
│   ├── GET  /                   # List all vaults
│   ├── POST /create             # Create new vault
│   ├── GET  /:id                # Vault details
│   ├── POST /:id/setup          # Setup vault (distribute shares)
│   └── GET  /:id/balance        # Get vault balance
│
├── /addresses
│   ├── GET  /vault/:id          # List addresses for vault
│   ├── POST /generate           # Generate new address
│   └── GET  /:address/balance   # Get address balance
│
├── /transactions
│   ├── GET  /                   # List all transactions
│   ├── POST /propose            # Propose new transaction
│   ├── GET  /:id                # Transaction details
│   ├── POST /:id/sign           # Submit signature share
│   ├── POST /:id/execute        # Execute transaction
│   └── DELETE /:id              # Cancel transaction
│
├── /mpc
│   ├── POST /setup/initiate     # Start MPC setup
│   ├── POST /setup/share        # Distribute share to guardian
│   ├── POST /sign/round1        # Nonce generation
│   ├── POST /sign/round2        # Combine nonces
│   ├── POST /sign/round3        # Signature shares
│   └── POST /sign/round4        # Combine signatures
│
├── /audit
│   ├── GET  /logs               # Audit logs
│   └── GET  /export             # Export logs
│
└── /ws
    └── /guardian/:id            # WebSocket for real-time updates
```

### 📦 Tech Stack

**Backend:**
- **Python FastAPI** or **Node.js Express**
- **PostgreSQL** - Database for vaults, transactions, audit logs
- **Redis** - Real-time coordination, WebSocket state
- **WebSocket** - Real-time guardian coordination
- **Celery** - Background tasks (transaction monitoring)

**Admin Dashboard:**
- **React** + **TypeScript** + **Next.js**
- **TailwindCSS** - Styling
- **Shadcn/ui** - Component library
- **React Query** - API state management
- **Zustand** - Client state
- **Socket.io-client** - Real-time updates

**Guardian Desktop App:**
- **Electron** + **React** + **TypeScript**
- **Electron-store** - Encrypted local storage
- **Node-forge** - Cryptography
- **WebSocket** - Server communication
- **YubiKey SDK** - Hardware key support

---

## 🚀 Additional Features & Improvements

### **4. Mobile App (React Native)** 🆕
**Purpose:** Approval notifications and 2FA

**Features:**
- Push notifications for pending transactions
- Biometric approval (FaceID/TouchID)
- View-only mode (see transactions, can't sign)
- 2FA for admin dashboard login
- Emergency guardian approval via phone

### **5. Hardware Wallet Integration** 🆕
**Supported:** Ledger, Trezor, YubiKey

**Features:**
- Store guardian share on hardware device
- Sign transactions with hardware key
- Never expose share to computer
- USB/Bluetooth connectivity

### **6. Multi-Vault Support** 🆕
**Vault Types:**
- **Treasury Vault** - Main company funds (3-of-5)
- **Cold Storage Vault** - Long-term holdings (5-of-7)
- **Operations Vault** - Daily operations (2-of-3)
- **Petty Cash Vault** - Small transactions (2-of-2)

**Features per vault:**
- Different guardian sets
- Different thresholds
- Different asset types (BTC-only, ETH-only, Multi)
- Spending limits

### **7. Transaction Workflows** 🆕
**Approval Flows:**
- **Simple Approval** - Any K of N guardians
- **Hierarchical** - Must include specific roles (e.g., CFO + any 2)
- **Time-locked** - Transactions executable after delay
- **Spending Limits** - Auto-approve under threshold

**Example:**
```
Withdraw < 1 BTC: Any 2 of 5 guardians
Withdraw 1-10 BTC: Must include CFO + 2 others
Withdraw > 10 BTC: All 5 guardians + 24h time lock
```

### **8. Compliance & Reporting** 🆕
**Features:**
- Tax reporting (CSV export for accountants)
- Transaction receipts (PDF)
- Monthly treasury reports
- Audit trail export (SOC 2 compliant)
- GDPR compliance
- AML/KYC integration hooks

### **9. Emergency Recovery** 🆕
**Scenarios:**
- **Guardian Unavailable:** Replace guardian with recovery process
- **Lost Device:** Restore share from backup
- **Compromised Share:** Regenerate all shares (requires all guardians)

**Recovery Process:**
```
1. Admin initiates recovery
2. Remaining guardians vote to approve
3. New shares generated from existing threshold
4. Old shares invalidated
5. New guardian receives fresh share
```

### **10. Advanced Security** 🆕
**Features:**
- **Geofencing** - Sign only from approved locations
- **Time-based restrictions** - No transactions outside business hours
- **Rate limiting** - Max N transactions per day
- **Anomaly detection** - Alert on unusual patterns
- **Session recording** - Video audit of signing sessions
- **Duress codes** - Silent alarm if coerced

---

## 📋 Implementation Roadmap

### **Phase 1: MVP (3 months)**
- ✅ Backend API (FastAPI)
- ✅ Admin Dashboard - Core features
  - Vault creation
  - Guardian management
  - Transaction proposals
- ✅ Guardian Desktop App - Core features
  - Share storage
  - Transaction signing
- ✅ Shamir's SSS implementation

### **Phase 2: Threshold Crypto (2 months)**
- ✅ Threshold ECDSA implementation
- ✅ 4-round MPC protocol
- ✅ WebSocket real-time coordination
- ✅ Address generation from xpub

### **Phase 3: Enterprise Features (2 months)**
- Multi-vault support
- Role-based access control
- Audit logs and compliance
- Transaction workflows
- Hardware key integration

### **Phase 4: Mobile & Advanced (2 months)**
- Mobile app (React Native)
- Hardware wallet integration
- Advanced security features
- Emergency recovery
- Reporting & analytics

### **Phase 5: Production (1 month)**
- Security audit
- Penetration testing
- Performance optimization
- Documentation
- Deployment

---

## 🎨 Design System

**Color Palette:**
```css
/* GuardianVault Brand Colors */
--primary: #2563EB;      /* Blue - Trust */
--secondary: #10B981;    /* Green - Security */
--accent: #F59E0B;       /* Amber - Attention */
--danger: #EF4444;       /* Red - Critical */
--background: #F9FAFB;   /* Light Gray */
--surface: #FFFFFF;      /* White */
--text: #111827;         /* Dark Gray */
```

**Typography:**
- **Headings:** Inter Bold
- **Body:** Inter Regular
- **Monospace:** JetBrains Mono (for addresses, hashes)

---

## 🔐 Security Architecture

### **Data Flow:**
```
Guardian Share Storage (Encrypted at Rest)
    └─> Master Password + OS Keychain
    └─> AES-256-GCM encryption
    └─> Hardware key (optional)

Transaction Signing
    └─> Guardian app never sends share
    └─> Only signature share transmitted
    └─> TLS 1.3 encryption in transit
    └─> Server coordinates, never sees shares

Admin Dashboard
    └─> JWT authentication
    └─> 2FA required for sensitive actions
    └─> Rate limiting per IP
    └─> Audit log all actions
```

---

## 📱 Supported Platforms

**Admin Dashboard:**
- ✅ Web (Chrome, Firefox, Safari, Edge)
- ✅ Responsive (Desktop, Tablet)

**Guardian Desktop App:**
- ✅ Windows 10/11
- ✅ macOS 11+
- ✅ Linux (Ubuntu 20.04+)

**Mobile App:**
- ✅ iOS 14+
- ✅ Android 11+

---

## 💡 Next Steps

Want me to:

1. **Create detailed wireframes** for specific screens?
2. **Build a prototype** of the admin dashboard?
3. **Implement the Electron app** structure?
4. **Design the API** with OpenAPI spec?
5. **Create database schema** for PostgreSQL?
6. **Build the WebSocket** coordination system?

Let me know which component you'd like to start building first! 🚀
