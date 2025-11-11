# GuardianVault Examples

This directory contains example scripts demonstrating various features of GuardianVault's MPC cryptocurrency key management.

## 🚀 Quick Start - Bitcoin Regtest Test

**The fastest way to see GuardianVault in action:**

```bash
# Start Bitcoin regtest node
docker compose -f ../docker-compose.regtest.yml up -d

# Run automated test (30 seconds)
python3 bitcoin_regtest_test_auto.py
```

This will demonstrate the complete flow: MPC key generation → Bitcoin address → fund address → sign transaction → broadcast → verify balances.

## 📁 Available Examples

### Bitcoin Regtest Integration (Production-Ready) ⭐

#### `bitcoin_regtest_test_auto.py`
**Automated Bitcoin regtest integration test - CI/CD ready**

**What it does:**
- ✅ Generates MPC key shares (3 parties)
- ✅ Derives Bitcoin regtest address
- ✅ Funds address from regtest node
- ✅ Creates and signs Bitcoin transaction using MPC
- ✅ Broadcasts transaction to network
- ✅ Verifies balances (0.5 BTC sent, 0.4999 BTC change, 0.0001 BTC fee)

**Returns**: Exit code 0 on success, 1 on failure

**Usage:**
```bash
python3 bitcoin_regtest_test_auto.py
```

**Documentation**: See [../docs/BITCOIN_REGTEST_INTEGRATION.md](../docs/BITCOIN_REGTEST_INTEGRATION.md)

---

#### `bitcoin_regtest_test.py`
**Interactive Bitcoin regtest integration test - Educational**

Same as automated version but with:
- Step-by-step explanations
- User prompts between phases
- Detailed output for learning

**Usage:**
```bash
python3 bitcoin_regtest_test.py
```

---

#### `bitcoin_networks_demo.py`
**Network support demonstration**

**What it shows:**
- Address generation for mainnet, testnet, and regtest
- Address format differences (mainnet starts with '1', testnet/regtest with 'm'/'n')
- Network parameter usage

**Usage:**
```bash
python3 bitcoin_networks_demo.py
```

**Output:**
```
MAINNET ADDRESSES
  Address: 19dyWyNo1eEoND5G25uruqduZwE6E9STho
  Format: Starts with '1' (P2PKH mainnet)

TESTNET ADDRESSES
  Address: mp9vp2Tmpfg49KYsjetEjkrERvpo91zkWD
  Format: Starts with 'm' or 'n' (P2PKH testnet)

REGTEST ADDRESSES
  Address: mp9vp2Tmpfg49KYsjetEjkrERvpo91zkWD
  Format: Starts with 'm' or 'n' (P2PKH regtest)
```

---

### MPC Workflow Examples

#### `complete_mpc_workflow.py`
**Complete MPC workflow demonstration**

**What it demonstrates:**
- Key share generation (3 parties, threshold cryptography)
- BIP32 hierarchical key derivation (m/44'/0'/0', m/44'/60'/0')
- Bitcoin address generation (5 addresses)
- Ethereum address generation (5 addresses)
- Message signing with threshold protocol

**Key Feature:** Private key is NEVER reconstructed at any point!

**Usage:**
```bash
python3 complete_mpc_workflow.py
```

**Output:**
```
ONE-TIME SETUP: Deriving account xpubs (threshold computation)
✓ Bitcoin xpub: 034d394e263906514cd101e15...
✓ Ethereum xpub: 0327f07322a21b6ab4906c9fb2...

BITCOIN ADDRESSES (No threshold computation!)
  m/44'/0'/0'/0/0
    Address: 19dyWyNo1eEoND5G25uruqduZwE6E9STho

ETHEREUM ADDRESSES (No threshold computation!)
  m/44'/60'/0'/0/0
    Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb2
```

---

#### `mpc_cli.py`
**Command-line interface for MPC operations**

**Features:**
- Interactive CLI for testing MPC features
- Key generation, address creation, signing
- Useful for manual testing and experimentation

**Usage:**
```bash
# Generate key shares
python3 mpc_cli.py generate --num-shares 5 --threshold 3

# Derive BIP32 keys
python3 mpc_cli.py derive --shares share1.json share2.json share3.json

# Sign a transaction
python3 mpc_cli.py sign --shares share1.json share2.json share3.json --message "tx_hash"
```

---

#### `mpc_workflow_example.py`
**Basic MPC workflow example - Good for beginners**

**What it shows:**
- Simplified example for learning MPC concepts
- Company managing crypto treasury scenario (3-of-5 multisig)
- Demonstrates party interactions
- Shows secure share management principles

**Usage:**
```bash
python3 mpc_workflow_example.py
```

---

## 📊 Feature Comparison Matrix

| Example | Key Gen | BIP32 | Addresses | Bitcoin TX | Signing | Networks | Production Ready |
|---------|---------|-------|-----------|------------|---------|----------|------------------|
| `bitcoin_regtest_test_auto.py` | ✅ | ✅ | ✅ | ✅ | ✅ | Regtest | ✅ |
| `bitcoin_regtest_test.py` | ✅ | ✅ | ✅ | ✅ | ✅ | Regtest | ✅ |
| `bitcoin_networks_demo.py` | ✅ | ✅ | ✅ | ❌ | ❌ | All | ✅ |
| `complete_mpc_workflow.py` | ✅ | ✅ | ✅ | ❌ | ✅ | N/A | 🚧 |
| `mpc_cli.py` | ✅ | ✅ | ✅ | ❌ | ✅ | N/A | 🚧 |
| `mpc_workflow_example.py` | ✅ | ❌ | ❌ | ❌ | ✅ | N/A | ❌ |

Legend: ✅ Implemented | 🚧 Partial | ❌ Not included

---

## 🔧 Prerequisites

### Required Software

1. **Python 3.9+**
   ```bash
   python3 --version
   ```

2. **Docker Desktop** (for Bitcoin regtest examples)
   ```bash
   docker --version
   docker compose version
   ```

3. **Dependencies**
   ```bash
   # Using poetry
   poetry install

   # Or using pip
   pip3 install -r ../requirements.txt base58
   ```

---

## 📖 Documentation

### Comprehensive Guides
- **[Bitcoin Regtest Integration](../docs/BITCOIN_REGTEST_INTEGRATION.md)** - Complete guide with troubleshooting
- **[Project Architecture](../docs/PROJECT_ARCHITECTURE.md)** - System overview and API reference
- **[Quick Start](../docs/QUICKSTART.md)** - Basic setup and usage

### Quick References
- [Test Results](../TESTING_SUMMARY.md) - Latest test results
- [Installation Guide](../INSTALL.md) - Setup instructions

---

## 🐛 Troubleshooting

### Bitcoin RPC Connection Failed

**Error:** `❌ Cannot connect to Bitcoin regtest node!`

**Solution:**
```bash
# Check if container is running
docker compose -f ../docker-compose.regtest.yml ps

# Check logs
docker compose -f ../docker-compose.regtest.yml logs bitcoin-regtest

# Restart the node
docker compose -f ../docker-compose.regtest.yml restart bitcoin-regtest

# Wait for startup
sleep 15

# Try again
python3 bitcoin_regtest_test_auto.py
```

### Module Not Found Errors

**Error:** `ModuleNotFoundError: No module named 'base58'`

**Solution:**
```bash
# Install missing dependencies
pip3 install base58

# Or install all dependencies
pip3 install -r ../requirements.txt base58

# Or use poetry
poetry install
```

### Invalid Signature Error

**Error:** `mandatory-script-verify-flag-failed (Signature must be zero...)`

**Possible causes:**
- Key share mismatch between address and signing
- Incorrect sighash calculation
- Wrong public key used

**Debug:**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Verify address matches signing key
print(f"Address public key: {address_info['public_key']}")
print(f"Signing public key: {signing_public_key.hex()}")
```

### Permission Denied on Script

```bash
chmod +x ../scripts/run_bitcoin_regtest.sh
```

---

## 🎯 What to Run

### I want to...

**See GuardianVault work with real Bitcoin:**
```bash
./scripts/run_bitcoin_regtest.sh
# or
python3 bitcoin_regtest_test_auto.py
```

**Learn how MPC works step-by-step:**
```bash
python3 bitcoin_regtest_test.py  # Interactive with explanations
```

**Understand address generation for different networks:**
```bash
python3 bitcoin_networks_demo.py
```

**See the complete MPC workflow (Bitcoin + Ethereum):**
```bash
python3 complete_mpc_workflow.py
```

**Experiment with MPC operations manually:**
```bash
python3 mpc_cli.py
```

**Learn MPC basics:**
```bash
python3 mpc_workflow_example.py
```

---

## 🔒 Security Notes

### ⚠️ These Are Examples

- Examples are for **demonstration and testing** purposes
- **DO NOT** use example code directly in production without modifications
- **DO NOT** store key shares in plain text files in production

### ✅ Production Requirements

For production use, you must:

1. **Secure Storage**: Use encrypted storage for key shares
   - Hardware Security Modules (HSMs)
   - Secure Enclaves (TPM, TEE)
   - Encrypted databases with access controls

2. **Secure Communication**: Encrypt all network communication
   - TLS 1.3 for transport security
   - End-to-end encryption for sensitive data
   - Authenticated channels between guardians

3. **Access Control**: Implement proper authentication
   - Multi-factor authentication (MFA)
   - Biometric authentication
   - Hardware tokens

4. **Audit Logging**: Track all operations
   - Who accessed what and when
   - All signing operations
   - Failed authentication attempts

5. **Key Management**: Follow best practices
   - Regular key rotation
   - Backup and recovery procedures
   - Geographic distribution of guardians
   - Clear policies and procedures

---

## 🚀 Next Steps

1. **Run the Bitcoin regtest test** to verify your setup works
2. **Read the integration guide** for detailed explanations
3. **Explore the project architecture** to understand the system
4. **Try modifying examples** to experiment with different scenarios
5. **Join the development** by checking [../todo/README.md](../todo/README.md)

---

## 📞 Support

For issues or questions:
- **Troubleshooting**: [../docs/BITCOIN_REGTEST_INTEGRATION.md#troubleshooting](../docs/BITCOIN_REGTEST_INTEGRATION.md#troubleshooting)
- **Architecture**: [../docs/PROJECT_ARCHITECTURE.md](../docs/PROJECT_ARCHITECTURE.md)
- **Main README**: [../README.md](../README.md)
- **GitHub Issues**: <repository-url>/issues

---

**Last Updated**: 2025-11-11
**Version**: 1.0.0
