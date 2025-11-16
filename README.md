# GuardianVault

> **Multiple Guardians, One Secure Vault**
> Enterprise-Grade Cryptocurrency Custody with Multi-Party Security

[![License: Non-Commercial](https://img.shields.io/badge/License-Non--Commercial-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Bitcoin](https://img.shields.io/badge/Bitcoin-BIP32%2FBIP44-orange.svg)](https://github.com/bitcoin/bips)
[![Ethereum](https://img.shields.io/badge/Ethereum-EIP--55-purple.svg)](https://eips.ethereum.org/EIPS/eip-55)
[![Enterprise](https://img.shields.io/badge/Enterprise-SME%20Ready-green.svg)](#)

**GuardianVault** is an enterprise-grade cryptocurrency key management system designed for small and medium enterprises. Assign trusted guardians from your team — no single person controls your crypto assets.

## ✅ Current Status (November 2025)

**✨ NEW: Bitcoin Regtest Integration - FULLY WORKING!** ✅

Complete Bitcoin transaction signing with MPC:
- ✅ **Bitcoin regtest integration** - Real Bitcoin transactions signed and broadcast
- ✅ **Network support** - Mainnet, testnet, and regtest
- ✅ **Transaction builder** - P2PKH transactions with proper sighash
- ✅ **Balance verification** - All amounts correct, zero private key exposure
- ✅ **Production ready** - Same code works for all networks

👉 **[Run the test now!](docs/BITCOIN_REGTEST_INTEGRATION.md#quick-start)** - Takes 30 seconds

**MPC Coordination Server: WORKING!** ✅

The core threshold cryptography system is fully operational:
- ✅ 4-round threshold ECDSA signing protocol
- ✅ Real-time coordination server (FastAPI + Socket.IO + MongoDB)
- ✅ Complete end-to-end test passing
- ✅ Valid Bitcoin signatures accepted by the network

**Next Steps:** See `/todo/` folder for development roadmap:
1. Guardian Desktop Application (Electron) - HIGH PRIORITY
2. Production Security Hardening (JWT, TLS, Rate Limiting) - HIGH PRIORITY
3. SegWit Support (P2WPKH, P2WSH) - MEDIUM PRIORITY
4. Admin Web Dashboard - MEDIUM PRIORITY
5. Mobile Guardian App - LOW PRIORITY

## 🏢 Perfect for SMEs

- **Crypto-native businesses** managing company treasury
- **Investment firms** holding digital assets
- **Family offices** with cryptocurrency portfolios
- **Traditional companies** entering the crypto space
- **Venture capital firms** with token holdings

---

## 🔐 Two Security Approaches

1. **Shamir's Secret Sharing (SSS)** - Traditional approach for cold storage
2. **Threshold Cryptography (NEW)** - Advanced MPC where private key is **NEVER** reconstructed

## 📚 Documentation

### 🚀 Quick Start
1. **[Bitcoin Regtest Integration Guide](docs/BITCOIN_REGTEST_INTEGRATION.md)** - Complete Bitcoin test with MPC signing (NEW!)
2. **[Quick Start Guide](docs/QUICKSTART.md)** - Basic setup and usage
3. **[Project Architecture](docs/PROJECT_ARCHITECTURE.md)** - System overview (NEW!)

### 📖 Core Documentation
- **[System Architecture](docs/ARCHITECTURE.md)** - High-level design
- **[Threshold Cryptography](docs/ARCHITECTURE_THRESHOLD.md)** - MPC implementation details
- **[Guardian App](docs/GUARDIAN_APP_IMPLEMENTATION.md)** - Desktop application
- **[Project Summary](docs/PROJECT_SUMMARY.md)** - Overview

### 🔬 Testing & Development
- **[Test Results](TESTING_SUMMARY.md)** - Latest test results
- **[Installation Guide](INSTALL.md)** - Setup instructions
- **[Developer Guide](docs/CLAUDE.md)** - For contributors and AI assistants
- **[Development Roadmap](todo/README.md)** - See [todo/](todo/) folder for detailed plans

---

## 🔐 Why GuardianVault?

### The Problem
Traditional crypto custody creates risks for enterprises:
- 💣 **Single point of failure** - One compromised employee = all funds at risk
- 🔓 **Insider threats** - One person with complete control
- 📉 **Key person risk** - What if the only keyholder leaves or is unavailable?
- 💰 **Custodian fees** - Expensive third-party custody solutions

### The GuardianVault Solution

**Assign Multiple Guardians** - Distribute control across your trusted team members
**Threshold Security** - Require 3 of 5 guardians to authorize transactions
**No Single Point of Failure** - Private keys never exist in one place
**Board-Level Control** - Perfect for governance and compliance

---

## 🛡️ Two Guardian Models

### Approach 1: Shamir's Secret Sharing (SSS)
**Best for:** Cold storage, backup vaults, long-term holdings

**How it works:**
1. **Split** master seed into N guardian shares (e.g., 5 shares)
2. **Distribute** shares to different guardians/locations
3. **Require** K guardians to collaborate (e.g., any 3 of 5)
4. **Reconstruct** temporarily when needed for operations

**Example:** Split vault key among CFO, CTO, CEO, 2 board members. Any 3 can access.

### Approach 2: Threshold Cryptography (⭐ RECOMMENDED)
**Best for:** Active trading, hot wallets, operational accounts

**How it works:**
1. **Generate** distributed key shares - private key **never exists anywhere**
2. **Setup** one-time threshold computation for account
3. **Generate** unlimited addresses without guardian interaction
4. **Sign** transactions through multi-party protocol - key stays distributed

**Example:** Treasury account with 3 guardians. Generate deposit addresses freely, require all 3 to sign withdrawals.

### Why Threshold Cryptography?

- 🔐 **Maximum Security** - Key cannot be stolen because it never exists
- ⚡ **Operational Efficiency** - Generate addresses without gathering guardians
- 🏢 **Enterprise Ready** - Built for active business use
- 🎯 **Compliance Friendly** - Clear audit trails, no single control point

## 📁 Files

### Shamir's Secret Sharing Implementation
- **`crypto_mpc_keymanager.py`**: Core SSS and HD wallet derivation
- **`enhanced_crypto_mpc.py`**: Bitcoin/Ethereum address generation
- **`mpc_cli.py`**: Command-line interface
- **`mpc_workflow_example.py`**: Practical demonstration

### Threshold Cryptography Implementation (✅ WORKING!)
- **`threshold_mpc_keymanager.py`**: Threshold key generation and BIP32 derivation
- **`threshold_addresses.py`**: Bitcoin/Ethereum address generation from public keys
- **`threshold_signing.py`**: 4-round threshold ECDSA signing protocol
- **`complete_mpc_workflow.py`**: Full demonstration
- **`coordination-server/`**: Production MPC coordination server (FastAPI + MongoDB + Socket.IO)
- **`test_coordination_server.py`**: End-to-end test workflow (✅ PASSES!)
- **`debug_transaction.py`**: MongoDB transaction inspector
- **`QUICK_START.md`**: Quick start guide for coordination server

### Documentation
- **`requirements.txt`**: Python dependencies
- **`docs/`**: Complete documentation
  - **[QUICKSTART.md](docs/QUICKSTART.md)**: Quick start guide
  - **[PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md)**: Project overview
  - **[CLAUDE.md](docs/CLAUDE.md)**: Developer guide for Claude Code
  - **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Shamir's SSS architecture
  - **[ARCHITECTURE_THRESHOLD.md](docs/ARCHITECTURE_THRESHOLD.md)**: Threshold crypto architecture
  - **[README.md](docs/README.md)**: Documentation index and navigation

## 🚀 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install individually
pip install ecdsa base58 eth-hash[pycryptodome]
```

## 💡 Quick Start

### Option 1: Shamir's Secret Sharing (Traditional)

```python
from crypto_mpc_keymanager import DistributedKeyManager

# Initialize manager
manager = DistributedKeyManager()

# Generate master seed
master_seed = manager.generate_master_seed()

# Split into 3-of-5 shares (need any 3 to reconstruct)
shares = manager.split_master_seed(master_seed, threshold=3, num_shares=5)

# Derive Bitcoin private key for address index 0
btc_key = manager.derive_bitcoin_address_key(master_seed, account=0, address_index=0)

# Derive Ethereum private key for address index 0
eth_key = manager.derive_ethereum_address_key(master_seed, account=0, address_index=0)

# Reconstruct from 3 shares
reconstructed = manager.reconstruct_master_seed([shares[0], shares[2], shares[4]])
```

### Option 2: Threshold Cryptography (⭐ RECOMMENDED)

```python
from threshold_mpc_keymanager import (
    ThresholdKeyGeneration, ThresholdBIP32, PublicKeyDerivation
)
from threshold_addresses import BitcoinAddressGenerator, EthereumAddressGenerator
from threshold_signing import ThresholdSigningWorkflow

# PHASE 1: Setup (ONE-TIME threshold computation)
# Generate distributed key shares
num_parties = 3
key_shares, master_pubkey = ThresholdKeyGeneration.generate_shares(num_parties)

# Derive master keys using threshold computation
seed = secrets.token_bytes(32)
master_shares, master_pubkey, master_chain = \
    ThresholdBIP32.derive_master_keys_threshold(key_shares, seed)

# Derive Bitcoin account xpub (one-time threshold operation)
btc_xpub = ThresholdBIP32.derive_account_xpub_threshold(
    master_shares, master_chain, coin_type=0, account=0
)
# Save xpub - it's public and can be shared!
# Each party keeps their master_shares[i] secret

# PHASE 2: Generate unlimited addresses (NO threshold computation!)
btc_addresses = BitcoinAddressGenerator.generate_addresses_from_xpub(
    btc_xpub, change=0, start_index=0, count=100  # Generate 100 addresses!
)
# No private keys needed! No threshold computation! Anyone with xpub can do this!

# PHASE 3: Sign transactions (threshold computation, key NEVER reconstructed)
message = b"Send 1 BTC to recipient"
signature = ThresholdSigningWorkflow.sign_message(
    master_shares,  # Each party uses their share
    message,
    master_pubkey
)
# Private key NEVER reconstructed! Each party only used their secret share!
```

### Running the Demos

```bash
# Shamir's Secret Sharing demos
python crypto_mpc_keymanager.py
python enhanced_crypto_mpc.py
python mpc_workflow_example.py

# Threshold Cryptography demos
python threshold_mpc_keymanager.py
python threshold_addresses.py
python threshold_signing.py
python complete_mpc_workflow.py  # Full workflow!
```

## 🏗️ Architecture

### 1. Shamir's Secret Sharing

Splits a secret S into N shares where any K shares can reconstruct S, but K-1 shares reveal nothing.

**Mathematical Foundation:**
- Uses polynomial interpolation over finite field GF(p)
- Secret is the constant term of polynomial
- Each share is a point (x, f(x)) on the polynomial
- Lagrange interpolation reconstructs the polynomial

**Security Properties:**
- Information-theoretically secure
- Any K shares → can reconstruct secret
- Any K-1 shares → zero information about secret

### 2. BIP32/BIP44 HD Wallet Derivation

Hierarchical Deterministic wallet standard that derives child keys from master seed.

**Derivation Path (BIP44):**
```
m / purpose' / coin_type' / account' / change / address_index

Bitcoin:  m/44'/0'/0'/0/i
Ethereum: m/44'/60'/0'/0/i
```

**Key Derivation:**
- Uses HMAC-SHA512 for key derivation
- Hardened derivation (') for enhanced security
- Each level derives: (child_key, chain_code) = HMAC-SHA512(parent_chain_code, data)

### 3. Address Generation

**Bitcoin (P2PKH):**
```
Private Key → Public Key (ECDSA secp256k1)
            → SHA256 → RIPEMD160
            → Add version byte + checksum
            → Base58 encode
```

**Ethereum:**
```
Private Key → Public Key (ECDSA secp256k1)
            → Keccak256 hash
            → Take last 20 bytes
            → Add 0x prefix + EIP-55 checksum
```

### 4. Threshold Cryptography Architecture (NEW)

**Key Innovation**: Private key NEVER reconstructed!

#### Additive Secret Sharing
```
Private Key = share_1 + share_2 + share_3 (mod n)
Public Key = G × share_1 + G × share_2 + G × share_3

✓ Public key computed WITHOUT combining private shares
✓ Each party only uses their secret share
```

#### Three-Phase Model

**Phase 1: Setup (One-Time)**
```
Parties collaborate to derive account xpub:
  m → m/44' → m/44'/0' → m/44'/0'/0'

Output: Extended Public Key (xpub)
Process: Threshold BIP32 hardened derivation
Security: Private key shares NEVER combined
```

**Phase 2: Addresses (Unlimited, No Threshold!)**
```
Derive from xpub using public BIP32:
  xpub/0/0, xpub/0/1, xpub/0/2, ...

Requirements: Only xpub (public!)
No Communication: Anyone can generate
No Threshold: No private keys involved
```

**Phase 3: Signing (Threshold Protocol)**
```
4-Round MPC:
  1. Each party: Generate nonce share k_i
  2. Combine: R = G×k_1 + G×k_2 + G×k_3
  3. Each party: Compute signature share s_i
  4. Combine: s = s_1 + s_2 + s_3

Output: Valid ECDSA signature (r, s)
Security: Private key NEVER reconstructed
```

#### Key Insight: Hardened vs Non-Hardened

BIP44 path: `m/44'/0'/0'/0/0`

- **Hardened (with ')**: m/44'/0'/0' - requires private key, threshold needed, DONE ONCE
- **Non-hardened**: /0/0 - uses public key only, no threshold, UNLIMITED addresses

## 🆚 Comparing Approaches

| Feature | Shamir's SSS | Threshold Crypto |
|---------|--------------|------------------|
| **Private Key** | Reconstructed temporarily | NEVER reconstructed |
| **Address Generation** | Needs reconstruction | xpub only (public) |
| **Signing** | Needs reconstruction | MPC protocol |
| **Threshold Type** | K-of-N (flexible) | t-of-t (all parties) |
| **Security Level** | High | Maximum |
| **Complexity** | Simple | Moderate |
| **Best For** | Cold storage backups | Active wallets, exchanges |

## 🔒 Security Considerations

### Critical Security Rules

**For Shamir's Secret Sharing:**
1. **Never Store Master Seed**: After splitting into shares, DESTROY the original master seed
2. **Separate Share Storage**: Never store threshold or more shares in the same location
3. **Secure Share Storage**: Use HSMs, encrypted storage, or secure enclaves
4. **Geographic Distribution**: Consider distributing shares across different physical locations
5. **Secure Reconstruction**: Only reconstruct seed in secure, isolated environments
6. **Memory Clearing**: Clear sensitive data from memory immediately after use

**For Threshold Cryptography:**
1. **Private Key Never Exists**: Key shares never combined - not even temporarily
2. **Secure Share Storage**: Each party stores their share in HSM
3. **Nonce Uniqueness**: CRITICAL - Never reuse nonces in signing (leads to key recovery!)
4. **xpub is Public**: Account xpub can be freely shared for address generation
5. **Encrypted Communication**: Use encrypted channels for MPC protocol rounds
6. **Verify R Points**: Each party should verify the combined R point before round 3

### Threat Model

**Shamir's SSS - Protected Against:**
- ✅ Single point compromise (need K shares)
- ✅ Insider threats (no single party has control)
- ✅ Physical theft (shares distributed)
- ✅ Partial information leakage (K-1 shares reveal nothing)

**Shamir's SSS - Not Protected Against:**
- ❌ Compromise of K or more share locations
- ❌ Malware during reconstruction
- ❌ Side-channel attacks during cryptographic operations
- ❌ Social engineering to gather shares

**Threshold Crypto - Protected Against:**
- ✅✅ Key reconstruction attacks (key NEVER exists!)
- ✅ Single party compromise (all parties needed)
- ✅ Malware on individual machines (only sees one share)
- ✅ Memory dump attacks (no complete key anywhere)
- ✅ Insider threats (distributed trust)

**Threshold Crypto - Not Protected Against:**
- ❌ Compromise of ALL parties simultaneously
- ❌ Nonce reuse attacks (implementation must prevent)
- ❌ Network interception (use encrypted channels)
- ❌ Social engineering for malicious signatures

### Production Recommendations

1. **Hardware Security Modules (HSMs)**
   - Store shares in FIPS 140-2 Level 3+ HSMs
   - Use tamper-evident storage

2. **Multi-Signature Schemes**
   - Combine with multi-sig wallets for additional security
   - Implement time-locks for high-value operations

3. **Operational Security**
   - Air-gapped devices for seed generation and reconstruction
   - Secure boot and encrypted storage
   - Regular security audits
   - Incident response procedures

4. **Key Rotation**
   - Periodically generate new master seeds
   - Transfer funds to new addresses
   - Destroy old shares securely

5. **Backup & Recovery**
   - Maintain encrypted backups of shares
   - Test recovery procedures regularly
   - Document share locations securely

## 📊 Example Workflow

### Initial Setup (One-Time)

```python
# 1. Generate master seed on air-gapped device
manager = EnhancedDistributedKeyManager()
master_seed = manager.generate_master_seed()

# 2. Split into shares (e.g., 3-of-5)
shares = manager.split_master_seed(master_seed, threshold=3, num_shares=5)

# 3. Save shares to separate secure locations
for i, share in enumerate(shares):
    manager.save_share_to_file(share, f"share_{i+1}.json")
    # Transfer to HSM or encrypted storage

# 4. DESTROY master_seed (securely wipe from memory and storage)
del master_seed
```

### Generating New Addresses (Regular Operation)

```python
# 1. Gather K shares from distributed parties
share1 = manager.load_share_from_file("location1/share_1.json")
share2 = manager.load_share_from_file("location2/share_2.json")
share3 = manager.load_share_from_file("location3/share_3.json")

# 2. Generate addresses (temporarily reconstructs seed)
addresses = manager.generate_addresses_from_shares(
    [share1, share2, share3],
    'bitcoin',
    account=0,
    num_addresses=10
)

# 3. Seed is automatically cleared after generation
# Shares are returned to distributed storage
```

## 🧪 Testing

Run the examples:

```bash
# Basic implementation
python crypto_mpc_keymanager.py

# Enhanced with address generation
python enhanced_crypto_mpc.py
```

## 📚 Technical Details

### Shamir's Secret Sharing Parameters

- **Prime Field**: 2^256 - 189 (256-bit prime)
- **Secret Size**: 256 bits (32 bytes)
- **Share Size**: 256 bits (32 bytes)
- **Threshold**: User-defined (recommended: 3-of-5 or 5-of-7)

### HD Wallet Derivation

- **Master Key Derivation**: HMAC-SHA512(key="Bitcoin seed", data=seed)
- **Child Key Derivation**: HMAC-SHA512(key=parent_chain_code, data=parent_key || index)
- **Curve**: secp256k1 (Bitcoin and Ethereum)
- **Hardened Indices**: Use indices ≥ 0x80000000

### Supported Cryptocurrencies

- **Bitcoin**: BIP44 path m/44'/0'/account'/change/index
- **Ethereum**: BIP44 path m/44'/60'/account'/change/index

Easy to extend for other coins by changing coin_type:
- Bitcoin: 0
- Bitcoin Testnet: 1
- Litecoin: 2
- Ethereum: 60
- [See SLIP-0044 for full list](https://github.com/satoshilabs/slips/blob/master/slip-0044.md)

## ⚠️ Disclaimer

**FOR EDUCATIONAL AND RESEARCH PURPOSES**

This implementation is provided for educational purposes to demonstrate cryptographic concepts. Before using in production:

1. **Security Audit**: Have the code professionally audited
2. **Compliance**: Ensure compliance with local regulations
3. **Testing**: Extensively test with small amounts first
4. **Best Practices**: Follow industry best practices for key management
5. **Liability**: Users are responsible for their own security

The authors assume no liability for loss of funds or security breaches.

## 📖 References

- [BIP32: Hierarchical Deterministic Wallets](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki)
- [BIP39: Mnemonic code for generating deterministic keys](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)
- [BIP44: Multi-Account Hierarchy for Deterministic Wallets](https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki)
- [Shamir's Secret Sharing](https://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing)
- [EIP-55: Mixed-case checksum address encoding](https://eips.ethereum.org/EIPS/eip-55)

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Add BIP39 mnemonic phrase support
- [ ] Implement threshold signature schemes (TSS)
- [ ] Add support for more cryptocurrencies
- [ ] Hardware wallet integration
- [ ] GUI for easier use
- [ ] Comprehensive test suite
- [ ] Performance optimizations

## 📄 License

**Non-Commercial Open Source License**

This software is licensed under a custom non-commercial license:
- ✅ Free for personal, educational, and research use
- ✅ Modify and redistribute (non-commercial)
- ✅ Full source code access
- ❌ Commercial use or sale prohibited without separate license

See [LICENSE](LICENSE) file for full terms.

For commercial licensing inquiries, contact: ioudkerk@gmail.com

## 🔗 Related Projects

- [bitcoin/bips](https://github.com/bitcoin/bips) - Bitcoin Improvement Proposals
- [ethereum/EIPs](https://github.com/ethereum/EIPs) - Ethereum Improvement Proposals
- [BlockchainCommons](https://github.com/BlockchainCommons) - Blockchain security standards

---

**Remember**: With great cryptographic power comes great responsibility. Always prioritize security! 🔐
