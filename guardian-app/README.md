# GuardianVault Desktop App

**Guardian Desktop Application** - Secure desktop app for GuardianVault threshold signing guardians.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# The Electron app will open automatically
```

## Features (MVP - Phase 1-3 Complete)

### ✅ Implemented

- **Secure Key Management**
  - Import guardian key shares (JSON file or paste)
  - Dual-layer encryption (AES-256-GCM + OS keychain)
  - Password-protected keystore

- **Cryptographic Operations**
  - Round 1: Generate nonce shares
  - Round 3: Compute signature shares
  - Python subprocess integration for crypto operations

- **Modern UI**
  - Beautiful import screen with file upload
  - Real-time validation
  - Error handling and user feedback
  - TailwindCSS styling

### 🚧 Coming Soon (Phase 4-6)

- WebSocket connection to coordination server
- Vault joining with invitation codes
- Real-time transaction signing requests
- Transaction approval UI
- Dashboard with vault status

## Project Structure

```
guardian-app/
├── src/
│   ├── main/               # Electron main process (Node.js)
│   │   ├── index.ts        # Main entry, IPC handlers
│   │   ├── keystore.ts     # Encrypted key storage
│   │   ├── crypto-bridge.ts # Python subprocess bridge
│   │   └── session.ts      # Session management
│   │
│   ├── preload/            # Electron preload script
│   │   └── index.ts        # IPC bridge to renderer
│   │
│   └── renderer/           # React UI
│       ├── App.tsx         # Main app component
│       ├── components/
│       │   └── Setup/
│       │       └── ImportKey.tsx  # Key import screen
│       └── styles.css      # TailwindCSS styles
│
├── python/
│   └── crypto_ops.py       # Python CLI for threshold crypto
│
├── test_guardian1_keyshare.json  # Test key share
└── TESTING_GUIDE.md        # Comprehensive testing instructions
```

## Technology Stack

- **Frontend:** React 18 + TypeScript
- **Desktop:** Electron 28
- **Build:** Vite + electron-vite
- **Styling:** TailwindCSS
- **Crypto:** Python subprocess (guardianvault library)
- **Security:** Electron safeStorage (OS keychain integration)

## Testing

See [TESTING_GUIDE.md](./TESTING_GUIDE.md) for detailed testing instructions.

### Quick Test

1. **Start the app:** `npm run dev`
2. **Import test key:** Use `test_guardian1_keyshare.json`
3. **Set password:** `testpassword123`
4. **Success!** You should see the dashboard placeholder

## Security

### Key Storage Security

1. **Password Encryption**
   - PBKDF2 key derivation (100,000 iterations)
   - AES-256-GCM authenticated encryption
   - Unique salt and IV per encryption

2. **OS-Level Encryption**
   - macOS: Keychain
   - Windows: DPAPI (Data Protection API)
   - Linux: libsecret/kwallet

3. **Session Management**
   - Key shares cached in memory after unlock
   - No plaintext keys written to disk
   - Cleared on app close

### Best Practices

- Never share your key share file
- Use a strong password (min 8 characters)
- Store backups securely offline
- Verify app authenticity before use

## Development

### Scripts

```bash
npm run dev        # Start development server
npm run build      # Build for production
npm run lint       # Run ESLint
npm run typecheck  # Run TypeScript checks
```

### Adding New Features

1. **IPC Handler (Main Process):**
   - Add handler in `src/main/index.ts`
   - Export types in `src/preload/index.ts`

2. **UI Component (Renderer):**
   - Create in `src/renderer/components/`
   - Use `window.electronAPI` for IPC calls

3. **Python Crypto Op:**
   - Add command in `python/crypto_ops.py`
   - Add bridge method in `src/main/crypto-bridge.ts`

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GUARDIAN DESKTOP APP                      │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐         IPC          ┌──────────────────┐
│  Renderer        │◄────────────────────►│  Main Process    │
│  (React UI)      │    contextBridge     │  (Node.js)       │
│                  │                       │                  │
│ - ImportKey.tsx  │                       │ - keystore.ts    │
│ - Dashboard.tsx  │                       │ - session.ts     │
│ - Signing.tsx    │                       │ - crypto-bridge  │
└──────────────────┘                       └────────┬─────────┘
                                                    │
                                                    │ spawn
                                                    ▼
                                           ┌──────────────────┐
                                           │  Python Script   │
                                           │  crypto_ops.py   │
                                           │                  │
                                           │ - round1         │
                                           │ - round3         │
                                           └──────────────────┘
                                                    │
                                                    │ import
                                                    ▼
                                           ┌──────────────────┐
                                           │  GuardianVault   │
                                           │  Library         │
                                           │                  │
                                           │ - threshold_*    │
                                           └──────────────────┘
```

## Dependencies

### Production
- `electron-store`: Persistent configuration
- `socket.io-client`: WebSocket for coordination (Phase 4)

### Development
- `electron`: Desktop framework
- `electron-vite`: Build tool
- `react`: UI library
- `typescript`: Type safety
- `tailwindcss`: Styling
- `vite`: Fast dev server

## Roadmap

- [x] Phase 1: Project setup and IPC
- [x] Phase 2: Key management and storage
- [x] Phase 3: Crypto operations bridge
- [ ] Phase 4: WebSocket integration
- [ ] Phase 5: Transaction signing UI
- [ ] Phase 6: End-to-end testing

## License

See [../LICENSE](../LICENSE) - Non-Commercial Open Source License

## Support

For issues or questions:
1. Check [TESTING_GUIDE.md](./TESTING_GUIDE.md)
2. Review terminal output and DevTools console
3. Verify all prerequisites are met
4. Check that the guardianvault library is accessible

---

Built with ❤️ for GuardianVault
