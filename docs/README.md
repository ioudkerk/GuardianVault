# GuardianVault Documentation

> **Multiple Guardians, One Secure Vault**

Complete documentation for GuardianVault - Enterprise-Grade Cryptocurrency Custody with Multi-Party Security.

## 📚 Documentation Structure

### For Users

1. **[QUICKSTART.md](QUICKSTART.md)** - Start here!
   - Installation instructions
   - Quick examples for both implementations
   - Basic usage patterns
   - Common operations

2. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Project overview
   - What was requested vs what was delivered
   - High-level feature comparison
   - Component overview
   - Use case examples

### For Developers

3. **[CLAUDE.md](CLAUDE.md)** - Developer guide for Claude Code
   - Development commands and workflows
   - Code architecture and structure
   - Testing approaches
   - Common patterns for extending functionality
   - Security considerations

4. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Shamir's Secret Sharing architecture
   - System flow diagrams
   - Mathematical foundations
   - Security properties
   - Implementation details
   - Deployment topologies

5. **[ARCHITECTURE_THRESHOLD.md](ARCHITECTURE_THRESHOLD.md)** - Threshold Cryptography architecture
   - Complete MPC architecture where key is NEVER reconstructed
   - Additive secret sharing explained
   - Threshold BIP32 derivation
   - 4-round ECDSA signing protocol
   - Security analysis and attack vectors
   - Mathematical proofs and examples

### Security Analysis

6. **[SECURITY_ANALYSIS.md](SECURITY_ANALYSIS.md)** - Comprehensive security analysis ⚠️
   - **Implementation classification** (custom vs production-standard protocols)
   - **Security model**: Honest-but-curious vs malicious adversaries
   - **Concrete attack scenarios** with code examples
   - **What zero-knowledge proofs protect against**
   - **When this implementation is suitable** (and when it's not)
   - **Roadmap to production-grade security**
   - **Recommendations by use case**
   - **Required reading before production use**

### For UI/UX and Implementation

7. **[UI_ARCHITECTURE.md](UI_ARCHITECTURE.md)** - Complete UI/UX specification
   - Admin Web Dashboard design
   - Guardian Desktop App design
   - Coordination Server architecture
   - API specifications
   - Implementation roadmap

8. **[GUARDIAN_APP_IMPLEMENTATION.md](GUARDIAN_APP_IMPLEMENTATION.md)** - Guardian Desktop App implementation
   - Complete Electron app structure
   - Security architecture
   - Feature implementation details
   - Development workflow
   - Deployment guide

## 🎯 Quick Navigation

### By Use Case

**I want to understand the project:**
→ Start with [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

**I want to use the software:**
→ Go to [QUICKSTART.md](QUICKSTART.md)

**I want to develop/extend the software:**
→ Read [CLAUDE.md](CLAUDE.md)

**I want to understand Shamir's Secret Sharing:**
→ See [ARCHITECTURE.md](ARCHITECTURE.md)

**I want to understand Threshold Cryptography:**
→ See [ARCHITECTURE_THRESHOLD.md](ARCHITECTURE_THRESHOLD.md)

**I want to build the UI:**
→ Start with [UI_ARCHITECTURE.md](UI_ARCHITECTURE.md)

**I want to understand the Guardian App:**
→ See [GUARDIAN_APP_IMPLEMENTATION.md](GUARDIAN_APP_IMPLEMENTATION.md)

**I want to understand security implications and limitations:**
→ **MUST READ**: [SECURITY_ANALYSIS.md](SECURITY_ANALYSIS.md)

### By Implementation

**Shamir's Secret Sharing (Traditional):**
- Quick Start: [QUICKSTART.md - Approach 1](QUICKSTART.md#approach-1-shamirs-secret-sharing)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Code: `crypto_mpc_keymanager.py`, `enhanced_crypto_mpc.py`

**Threshold Cryptography (Recommended):**
- Quick Start: [QUICKSTART.md - Approach 2](QUICKSTART.md#approach-2-threshold-cryptography--recommended)
- Architecture: [ARCHITECTURE_THRESHOLD.md](ARCHITECTURE_THRESHOLD.md)
- Code: `threshold_mpc_keymanager.py`, `threshold_addresses.py`, `threshold_signing.py`

## 📖 Documentation Map

```
docs/
├── README.md (this file)                   # Navigation and index
├── QUICKSTART.md                           # Quick start guide
├── PROJECT_SUMMARY.md                      # Project overview
├── CLAUDE.md                               # Developer guide
├── ARCHITECTURE.md                         # Shamir's SSS architecture
├── ARCHITECTURE_THRESHOLD.md               # Threshold crypto architecture
├── UI_ARCHITECTURE.md                      # UI/UX specification (NEW)
└── GUARDIAN_APP_IMPLEMENTATION.md          # Guardian App details (NEW)

../ (root directory)
├── README.md                               # Main project README
├── LICENSE                                 # Non-commercial license
├── requirements.txt                        # Python dependencies
├── crypto_mpc_keymanager.py               # Shamir's SSS implementation
├── enhanced_crypto_mpc.py                 # Shamir's address generation
├── mpc_cli.py                             # CLI tool for Shamir's
├── mpc_workflow_example.py                # Shamir's demo
├── threshold_mpc_keymanager.py            # Threshold MPC implementation
├── threshold_addresses.py                 # Threshold address generation
├── threshold_signing.py                   # Threshold ECDSA signing
├── complete_mpc_workflow.py               # Complete threshold demo
└── guardian-app/                          # Guardian Desktop App (NEW)
    ├── src/main/                          # Electron main process
    ├── src/renderer/                      # React UI
    ├── package.json                       # Dependencies
    └── README.md                          # App documentation
```

## 🤖 For AI/LLM Developers

If you're an AI assistant (like Claude Code, GPT, etc.) helping develop this project:

### Essential Reading
1. **[CLAUDE.md](CLAUDE.md)** - Your primary guide
   - Contains development commands
   - Architectural patterns
   - Testing strategies
   - Security rules

2. **[ARCHITECTURE_THRESHOLD.md](ARCHITECTURE_THRESHOLD.md)** - For threshold crypto work
   - Mathematical foundations
   - Implementation details
   - Security considerations

### Key Information

**Project Type:** Cryptocurrency key management using MPC

**Languages:** Python 3.8+

**Key Dependencies:**
- `ecdsa` - ECDSA signatures
- `base58` - Bitcoin address encoding
- `eth-hash[pycryptodome]` - Ethereum Keccak256

**Security Critical:**
- Never log full private keys or shares
- Memory clearing is essential
- Nonce reuse in ECDSA = private key recovery
- Test thoroughly before production

**Two Implementations:**
1. Shamir's SSS - Key reconstructed temporarily
2. Threshold Crypto - Key NEVER reconstructed (recommended)

**Code Structure:**
- Pure Python for core cryptography
- No external crypto libs for Shamir's SSS
- secp256k1 implemented from scratch
- BIP32/BIP44 HD wallet derivation

**Testing:**
```bash
# Run demos
python threshold_mpc_keymanager.py
python complete_mpc_workflow.py

# Test coordination server (NEW - WORKING!)
python test_coordination_server.py

# Debug transactions
python debug_transaction.py

# Use correct Python path
/Users/ivan/.virtualenvs/claude-mcp/bin/python <script>
```

**Coordination Server:**
```bash
# Start MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Start coordination server
cd coordination-server
/Users/ivan/.virtualenvs/claude-mcp/bin/python -m app.main

# Server runs at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

## 🔧 Extending the Project

### Adding New Cryptocurrencies

1. Add coin type to BIP44 constants
2. Implement address generation for that coin
3. Test with known test vectors
4. Update documentation

See [CLAUDE.md - Adding Support for New Cryptocurrencies](CLAUDE.md#adding-support-for-new-cryptocurrencies)

### Improving Threshold Protocol

1. Review [ARCHITECTURE_THRESHOLD.md](ARCHITECTURE_THRESHOLD.md)
2. Understand current 4-round protocol
3. Consider optimizations (fewer rounds, batching)
4. Maintain security properties
5. Add tests

### Security Enhancements

1. HSM integration
2. Hardware wallet support
3. Secure enclaves
4. Proactive secret sharing
5. Verifiable secret sharing with ZK proofs

See future enhancements in [ARCHITECTURE_THRESHOLD.md](ARCHITECTURE_THRESHOLD.md#future-enhancements)

## 📝 Documentation Standards

When contributing documentation:

1. **Use clear headers** - H1 for major sections, H2 for subsections
2. **Include code examples** - With proper syntax highlighting
3. **Add diagrams** - ASCII art or mermaid for complex flows
4. **Security notes** - Always highlight security considerations
5. **Cross-reference** - Link to related sections
6. **Keep updated** - Update docs when code changes

## 🔗 External Resources

### Standards
- [BIP32: HD Wallets](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki)
- [BIP44: Multi-Account Hierarchy](https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki)
- [BIP39: Mnemonic Phrases](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)
- [EIP-55: Ethereum Checksum](https://eips.ethereum.org/EIPS/eip-55)

### Cryptography
- [Shamir's Secret Sharing](https://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing)
- [ECDSA](https://en.wikipedia.org/wiki/Elliptic_Curve_Digital_Signature_Algorithm)
- [secp256k1 Curve](https://en.bitcoin.it/wiki/Secp256k1)
- [Threshold Cryptography](https://en.wikipedia.org/wiki/Threshold_cryptosystem)

## 💡 Support

For questions:
- Check the documentation in order: QUICKSTART → PROJECT_SUMMARY → ARCHITECTURE
- Review code comments in implementation files
- See examples in demo scripts

For commercial licensing: ioudkerk@gmail.com

---

**Remember:** This software handles cryptographic keys. Always prioritize security and conduct thorough audits before production use!
