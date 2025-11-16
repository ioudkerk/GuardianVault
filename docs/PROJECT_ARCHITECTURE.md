# GuardianVault - Project Architecture

## Overview

GuardianVault is a Multi-Party Computation (MPC) cryptocurrency key manager implementing threshold cryptography for Bitcoin and Ethereum. The system ensures that private keys are never reconstructed in a single location, providing enterprise-grade security for digital asset management.

## Directory Structure

```
GuardianVault/
├── guardianvault/              # Core Python package
│   ├── __init__.py
│   ├── threshold_mpc_keymanager.py   # MPC key generation & BIP32
│   ├── threshold_signing.py          # Threshold signature protocol
│   ├── threshold_addresses.py        # Address generation (BTC/ETH)
│   ├── bitcoin_transaction.py        # Bitcoin transaction builder
│   ├── crypto_mpc_keymanager.py      # Legacy MPC implementation
│   └── enhanced_crypto_mpc.py        # Enhanced legacy implementation
│
├── examples/                   # Example scripts and demos
│   ├── bitcoin_regtest_test.py       # Interactive Bitcoin test
│   ├── bitcoin_regtest_test_auto.py  # Automated Bitcoin test
│   ├── bitcoin_networks_demo.py      # Network support demo
│   ├── complete_mpc_workflow.py      # Full MPC workflow
│   ├── mpc_cli.py                    # CLI interface
│   ├── mpc_workflow_example.py       # Basic workflow example
│   └── README.md
│
├── tests/                      # Test suite
│   ├── test_coordination_server.py   # Server integration tests
│   └── debug_transaction.py          # Transaction debugging
│
├── docs/                       # Documentation
│   ├── BITCOIN_REGTEST_INTEGRATION.md  # Bitcoin test guide (NEW)
│   ├── PROJECT_ARCHITECTURE.md         # This file (NEW)
│   ├── ARCHITECTURE.md                 # System architecture
│   ├── ARCHITECTURE_THRESHOLD.md       # Threshold cryptography
│   ├── PROJECT_SUMMARY.md              # Project overview
│   ├── QUICKSTART.md                   # Quick start guide
│   ├── GUARDIAN_APP_IMPLEMENTATION.md  # Guardian app docs
│   ├── UI_ARCHITECTURE.md              # UI design
│   ├── bitcoin-regtest-integration.md  # Regtest setup
│   └── README.md
│
├── coordination-server/        # MPC coordination server
│   ├── app/
│   │   ├── main.py            # FastAPI application
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # Database setup
│   │   ├── models/            # SQLAlchemy models
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic
│   │   └── websocket/         # WebSocket handlers
│   ├── requirements.txt
│   └── README.md
│
├── guardian-app/               # Desktop guardian application
│   ├── python/
│   │   └── crypto_ops.py      # Python crypto operations
│   ├── TESTING_GUIDE.md
│   └── README.md
│
├── scripts/                    # Utility scripts
│   └── run_bitcoin_regtest.sh # Bitcoin regtest launcher
│
├── todo/                       # Project roadmap
│   ├── 01-GUARDIAN-APP.md
│   ├── 02-SECURITY.md
│   ├── 03-BLOCKCHAIN.md
│   ├── 04-ADMIN-DASHBOARD.md
│   ├── 05-MOBILE.md
│   ├── 99-FUTURE-ENHANCEMENTS.md
│   └── README.md
│
├── docker-compose.regtest.yml  # Bitcoin regtest environment
├── pyproject.toml              # Poetry dependencies
├── poetry.lock                 # Locked dependencies
├── requirements.txt            # Pip requirements
├── README.md                   # Main README
├── INSTALL.md                  # Installation guide
├── TESTING_SUMMARY.md          # Test results summary
└── LICENSE                     # License file
```

## Core Components

### 1. MPC Key Management (`guardianvault/`)

#### threshold_mpc_keymanager.py
**Purpose**: Core MPC key generation and hierarchical deterministic (HD) key derivation.

**Key Classes**:
- `KeyShare`: Represents a single party's share of a private key
- `ThresholdKeyGeneration`: Generates distributed key shares
- `ThresholdBIP32`: BIP32 hierarchical key derivation using MPC
- `ExtendedPublicKey`: BIP32 extended public key (xpub)
- `PublicKeyDerivation`: Non-hardened child key derivation

**Key Functions**:
```python
# Generate key shares (private key never assembled)
key_shares, public_key = ThresholdKeyGeneration.generate_shares(num_parties=3)

# Derive master keys
master_shares, master_pub, chain = ThresholdBIP32.derive_master_keys_threshold(
    key_shares, seed
)

# Derive account xpub (m/44'/0'/0')
btc_xpub = ThresholdBIP32.derive_account_xpub_threshold(
    master_shares, chain, coin_type=0, account=0
)
```

#### threshold_signing.py
**Purpose**: Threshold signature protocol implementation.

**Key Classes**:
- `ThresholdSignature`: ECDSA signature (r, s) components
- `ThresholdSigner`: Individual party signing operations
- `ThresholdSigningWorkflow`: Complete multi-round signing protocol

**Signing Protocol**:
1. **Round 1**: Nonce generation (each party generates k_i)
2. **Round 2**: Nonce combination (R = Σ R_i)
3. **Round 3**: Signature share computation (s_i = k_i^-1 · (hash + r · share_i))
4. **Round 4**: Signature combination (s = Σ s_i)

**Key Functions**:
```python
signature = ThresholdSigningWorkflow.sign_message(
    key_shares,      # List of KeyShare objects
    message,         # Message to sign (or hash if prehashed=True)
    public_key,      # Public key for verification
    prehashed=False  # Set True for pre-hashed messages
)
```

#### threshold_addresses.py
**Purpose**: Cryptocurrency address generation from public keys.

**Key Classes**:
- `BitcoinAddressGenerator`: Bitcoin P2PKH address generation
- `EthereumAddressGenerator`: Ethereum address generation with EIP-55 checksum

**Key Functions**:
```python
# Bitcoin address
address = BitcoinAddressGenerator.pubkey_to_address(
    public_key, network="mainnet"  # or "testnet" or "regtest"
)

# Multiple Bitcoin addresses from xpub
addresses = BitcoinAddressGenerator.generate_addresses_from_xpub(
    xpub, change=0, start_index=0, count=10, network="mainnet"
)

# Ethereum address
eth_address = EthereumAddressGenerator.pubkey_to_address(public_key)
```

#### bitcoin_transaction.py
**Purpose**: Bitcoin transaction construction and signing.

**Key Classes**:
- `TxInput`: Transaction input
- `TxOutput`: Transaction output
- `BitcoinTransaction`: Transaction builder and serializer
- `BitcoinTransactionBuilder`: High-level transaction builder

**Key Functions**:
```python
# Build P2PKH transaction
tx, script_code = BitcoinTransactionBuilder.build_p2pkh_transaction(
    utxo_txid="abc...",
    utxo_vout=0,
    utxo_amount_btc=1.0,
    sender_address="1ABC...",
    recipient_address="1XYZ...",
    send_amount_btc=0.5,
    fee_btc=0.0001
)

# Get sighash for signing
sighash = tx.get_sighash(input_index=0, script_code=script_code)

# Add signature
tx = BitcoinTransactionBuilder.sign_transaction(
    tx, input_index=0, script_code=script_code,
    signature_der=sig_bytes, public_key=pubkey_bytes
)

# Serialize for broadcast
raw_tx = tx.serialize().hex()
```

### 2. Examples (`examples/`)

#### bitcoin_regtest_test.py
**Purpose**: Interactive Bitcoin regtest integration test.

**Features**:
- Step-by-step interactive prompts
- Full MPC workflow demonstration
- Real Bitcoin transaction signing
- Balance verification

**Usage**:
```bash
python3 examples/bitcoin_regtest_test.py
```

#### bitcoin_regtest_test_auto.py
**Purpose**: Automated Bitcoin regtest test.

**Features**:
- Non-interactive execution
- CI/CD friendly
- Returns exit code (0 = success, 1 = failure)
- Comprehensive assertions

**Usage**:
```bash
python3 examples/bitcoin_regtest_test_auto.py
echo $?  # Check exit code
```

#### bitcoin_networks_demo.py
**Purpose**: Demonstrates address generation for all networks.

**Shows**:
- Mainnet addresses (start with '1')
- Testnet addresses (start with 'm' or 'n')
- Regtest addresses (start with 'm' or 'n')
- Address format differences

#### complete_mpc_workflow.py
**Purpose**: Complete MPC workflow from key generation to signing.

**Demonstrates**:
- Key share generation
- BIP32 derivation
- Address generation (Bitcoin & Ethereum)
- Message signing

### 3. Coordination Server (`coordination-server/`)

**Purpose**: WebSocket server for coordinating MPC operations between guardians.

**Architecture**:
```
FastAPI Application
├── REST API (routers/)
│   ├── /vaults         - Vault management
│   ├── /guardians      - Guardian registration
│   └── /transactions   - Transaction proposals
│
├── WebSocket (websocket/)
│   └── /ws/signing     - Real-time signing coordination
│
├── Services (services/)
│   └── mpc_coordinator - MPC protocol coordination
│
└── Database (models/)
    ├── Vault           - Multi-sig vault metadata
    ├── Guardian        - Guardian information
    └── Transaction     - Transaction proposals
```

**Technology Stack**:
- FastAPI (web framework)
- SQLAlchemy (ORM)
- WebSockets (real-time communication)
- SQLite/PostgreSQL (database)

### 4. Guardian App (`guardian-app/`)

**Purpose**: Desktop application for guardians to manage their key shares.

**Features** (Phases 1-3 Complete):
- ✅ Vault creation and joining
- ✅ Key share generation
- ✅ Transaction approval
- ✅ Secure key storage
- 🚧 Biometric authentication (Phase 4)
- 🚧 Hardware wallet integration (Phase 4)

**Technology Stack**:
- Electron (desktop framework)
- React (UI framework)
- Python (crypto operations via python-shell)

## Data Flow

### 1. Key Generation Flow

```
┌──────────┐
│ Guardian │
│    1     │
└────┬─────┘
     │
     ├─ Generate Share 1
     │
     v
┌────────────┐     ┌──────────┐     ┌──────────┐
│Coordinator │<───>│Guardian 2│<───>│Guardian 3│
│   Server   │     └──────────┘     └──────────┘
└─────┬──────┘
      │
      ├─ Collect public share points
      ├─ Compute public key: P = Σ P_i
      │
      v
┌──────────────┐
│  Public Key  │  (Shared with all)
│  Xpub/Chain  │
└──────────────┘
```

### 2. Transaction Signing Flow

```
┌──────────────┐
│ Transaction  │
│  Proposal    │
└──────┬───────┘
       │
       v
┌──────────────┐
│  Coordinator │
│    Server    │
└──────┬───────┘
       │
       ├─ Round 1: Collect nonce commitments
       ├─ Round 2: Collect nonce reveals & compute R
       ├─ Round 3: Collect signature shares
       ├─ Round 4: Combine shares → Final signature
       │
       v
┌──────────────┐
│   Signed     │
│ Transaction  │
└──────────────┘
       │
       v
┌──────────────┐
│  Blockchain  │
└──────────────┘
```

## Security Architecture

### Threat Model

| Threat | Mitigation |
|--------|------------|
| Single guardian compromise | Threshold requirement (t-of-n) |
| Network eavesdropping | Only public data transmitted |
| Server compromise | No private keys stored on server |
| Malicious guardian | Signature verification catches invalid shares |
| Key share extraction | Encrypted storage + biometrics |
| Replay attacks | Nonce uniqueness + transaction ordering |

### Security Boundaries

```
┌─────────────────────────────────────────────┐
│           Guardian 1 Device                  │
│  ┌──────────────────────────────────────┐  │
│  │  Encrypted Storage                    │  │
│  │  ├─ Key Share 1                       │  │
│  │  └─ Biometric Protection              │  │
│  └──────────────────────────────────────┘  │
└──────────────┬──────────────────────────────┘
               │
               │ TLS
               │
┌──────────────▼──────────────────────────────┐
│        Coordination Server                   │
│  ┌──────────────────────────────────────┐  │
│  │  Public Data Only:                    │  │
│  │  ├─ Public keys                       │  │
│  │  ├─ Nonce points (R_i)                │  │
│  │  ├─ Transaction proposals             │  │
│  │  └─ Signature shares                  │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘

KEY SECURITY PROPERTY:
  Private keys NEVER leave guardian devices
  Server never has enough shares to reconstruct keys
```

### Cryptographic Primitives

| Component | Algorithm | Key Size |
|-----------|-----------|----------|
| ECDSA | secp256k1 | 256-bit |
| Key Derivation | BIP32 HMAC-SHA512 | 512-bit |
| Hashing | SHA-256 | 256-bit |
| Bitcoin Addresses | RIPEMD-160 | 160-bit |
| Ethereum Addresses | Keccak-256 | 256-bit |

## Network Architecture

### Bitcoin Regtest Environment

```
┌─────────────────────────────────────────────┐
│         Docker Compose Stack                 │
│                                              │
│  ┌─────────────────┐  ┌──────────────────┐ │
│  │  Bitcoin Core   │  │   Mempool DB     │ │
│  │   (regtest)     │  │   (MariaDB)      │ │
│  │  Port: 18443    │  │                  │ │
│  └────────┬────────┘  └────────┬─────────┘ │
│           │                    │            │
│           │         ┌──────────▼─────────┐  │
│           │         │  Mempool Backend   │  │
│           └────────>│  (Indexer)         │  │
│                     └──────────┬─────────┘  │
│                                │            │
│                     ┌──────────▼─────────┐  │
│                     │  Mempool Web UI    │  │
│                     │  Port: 8080        │  │
│                     └────────────────────┘  │
└─────────────────────────────────────────────┘
                      │
                      │ HTTP
                      │
┌─────────────────────▼─────────────────────┐
│           Test Scripts                     │
│  - bitcoin_regtest_test.py                │
│  - bitcoin_regtest_test_auto.py           │
└───────────────────────────────────────────┘
```

## Development Workflow

### 1. Setup

```bash
# Clone repository
git clone <repo-url>
cd GuardianVault

# Install dependencies
poetry install
# or
pip3 install -r requirements.txt base58

# Start Bitcoin regtest
docker compose -f docker-compose.regtest.yml up -d
```

### 2. Testing

```bash
# Run automated test
python3 examples/bitcoin_regtest_test_auto.py

# Run interactive test
python3 examples/bitcoin_regtest_test.py

# Run coordination server tests
python3 tests/test_coordination_server.py

# Run unit tests (when available)
pytest tests/
```

### 3. Development

```bash
# Work on core MPC features
vim guardianvault/threshold_*.py

# Work on examples
vim examples/

# Work on coordination server
cd coordination-server/
uvicorn app.main:app --reload

# Work on guardian app
cd guardian-app/
npm start
```

## API Reference

### Core API

#### ThresholdKeyGeneration

```python
class ThresholdKeyGeneration:
    @staticmethod
    def generate_shares(
        num_parties: int,
        threshold: int = None
    ) -> Tuple[List[KeyShare], bytes]:
        """Generate distributed key shares"""
```

#### ThresholdBIP32

```python
class ThresholdBIP32:
    @staticmethod
    def derive_master_keys_threshold(
        key_shares: List[KeyShare],
        seed: bytes
    ) -> Tuple[List[KeyShare], bytes, bytes]:
        """Derive BIP32 master keys"""

    @staticmethod
    def derive_account_xpub_threshold(
        master_shares: List[KeyShare],
        master_chain: bytes,
        coin_type: int,
        account: int
    ) -> ExtendedPublicKey:
        """Derive account xpub (m/44'/coin'/account')"""
```

#### ThresholdSigningWorkflow

```python
class ThresholdSigningWorkflow:
    @staticmethod
    def sign_message(
        key_shares: List[KeyShare],
        message: bytes,
        public_key: bytes,
        prehashed: bool = False
    ) -> ThresholdSignature:
        """Sign message using threshold protocol"""
```

#### BitcoinAddressGenerator

```python
class BitcoinAddressGenerator:
    @staticmethod
    def pubkey_to_address(
        public_key: bytes,
        network: str = "mainnet"  # or "testnet" or "regtest"
    ) -> str:
        """Convert public key to Bitcoin address"""

    @staticmethod
    def generate_addresses_from_xpub(
        xpub: ExtendedPublicKey,
        change: int = 0,
        start_index: int = 0,
        count: int = 10,
        network: str = "mainnet"
    ) -> List[dict]:
        """Generate multiple addresses from xpub"""
```

#### BitcoinTransactionBuilder

```python
class BitcoinTransactionBuilder:
    @staticmethod
    def build_p2pkh_transaction(
        utxo_txid: str,
        utxo_vout: int,
        utxo_amount_btc: float,
        sender_address: str,
        recipient_address: str,
        send_amount_btc: float,
        fee_btc: float = 0.00001
    ) -> Tuple[BitcoinTransaction, bytes]:
        """Build P2PKH transaction"""

    @staticmethod
    def sign_transaction(
        tx: BitcoinTransaction,
        input_index: int,
        script_code: bytes,
        signature_der: bytes,
        public_key: bytes
    ) -> BitcoinTransaction:
        """Add signature to transaction"""
```

## Configuration

### Environment Variables

```bash
# Bitcoin RPC
BITCOIN_RPC_HOST=localhost
BITCOIN_RPC_PORT=18443
BITCOIN_RPC_USER=regtest
BITCOIN_RPC_PASSWORD=regtest

# Coordination Server
COORDINATION_SERVER_URL=http://localhost:8000
DATABASE_URL=sqlite:///./guardianvault.db

# Guardian App
GUARDIAN_STORAGE_PATH=~/.guardianvault
LOG_LEVEL=INFO
```

### Docker Configuration

See `docker-compose.regtest.yml` for Bitcoin regtest configuration.

## Performance Considerations

### Optimization Opportunities

1. **Parallel Key Derivation**: Derive multiple child keys in parallel
2. **Batch Signing**: Sign multiple transactions in one round
3. **Precomputed Tables**: Cache elliptic curve operations
4. **Hardware Acceleration**: Use hardware RNG for nonce generation

### Benchmarks

See `docs/BITCOIN_REGTEST_INTEGRATION.md` for detailed benchmarks.

## Future Enhancements

See `todo/` directory for detailed roadmap:

1. **Guardian App** (`01-GUARDIAN-APP.md`)
   - Hardware wallet integration
   - Mobile app support
   - Multi-device sync

2. **Security** (`02-SECURITY.md`)
   - Formal verification
   - Security audits
   - Bug bounty program

3. **Blockchain** (`03-BLOCKCHAIN.md`)
   - SegWit support
   - Lightning Network
   - Additional blockchains (Solana, Cosmos, etc.)

4. **Admin Dashboard** (`04-ADMIN-DASHBOARD.md`)
   - Organization management
   - Policy management
   - Audit logs

5. **Mobile** (`05-MOBILE.md`)
   - iOS and Android apps
   - Push notifications
   - Biometric authentication

## Contributing

See `README.md` for contribution guidelines.

## License

See `LICENSE` file for license information.

---

**Last Updated**: 2025-11-11
**Version**: 1.0.0
