# 🚀 GuardianVault - Quick Start Guide

> **Multiple Guardians, One Secure Vault**

## What is GuardianVault?

**GuardianVault** is an enterprise-grade cryptocurrency custody system for SMEs. Assign trusted guardians from your team — no single person controls your crypto assets.

## Two Guardian Models

1. **Shamir's Secret Sharing (SSS)** - For cold storage vaults
2. **Threshold Cryptography (⭐ RECOMMENDED)** - For active treasury accounts

### Core Files

#### Shamir's Secret Sharing Implementation
1. **`crypto_mpc_keymanager.py`** - Core SSS and HD wallet derivation
2. **`enhanced_crypto_mpc.py`** - Bitcoin/Ethereum address generation
3. **`mpc_workflow_example.py`** - Practical demonstration
4. **`mpc_cli.py`** - Command-line interface

#### Threshold Cryptography Implementation (NEW)
5. **`threshold_mpc_keymanager.py`** - Threshold key generation and BIP32
6. **`threshold_addresses.py`** - Address generation from xpub (no private keys!)
7. **`threshold_signing.py`** - Threshold ECDSA signing protocol
8. **`complete_mpc_workflow.py`** - End-to-end demonstration

#### Documentation
9. **`requirements.txt`** - Dependencies
10. **`README.md`** - Comprehensive documentation
11. **`ARCHITECTURE.md`** - System architecture
12. **`ARCHITECTURE_THRESHOLD.md`** - Threshold crypto details

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🎯 What This System Does

### The Problem
- Storing cryptocurrency private keys in one place = single point of failure
- One compromised device = all funds at risk
- One lost key = funds permanently lost

### Solution 1: Shamir's Secret Sharing
1. **Split** one master seed into N shares (e.g., 5 shares)
2. **Distribute** shares to different locations/parties
3. **Reconstruct** temporarily when needed using K shares (e.g., any 3 of 5)
4. **Derive** unlimited Bitcoin/Ethereum addresses from the master seed

**Security Benefits:**
- ✅ No single point of failure
- ✅ Compromise of K-1 shares reveals NOTHING
- ✅ Can lose N-K shares and still recover
- ✅ Master seed never stored permanently

### Solution 2: Threshold Cryptography (⭐ RECOMMENDED)
1. **Generate** distributed key shares where private key **never exists anywhere**
2. **Derive** account xpub using one-time threshold computation
3. **Generate** unlimited addresses from xpub without any threshold computation
4. **Sign** transactions using threshold ECDSA protocol without reconstructing key

**Security Benefits:**
- ✅✅ Private key NEVER reconstructed (not even temporarily!)
- ✅ Unlimited addresses without threshold computation
- ✅ Maximum security - key cannot be stolen because it never exists
- ✅ Each party only uses their secret share
- ✅ Suitable for active wallets and exchanges

## 🏃 Quick Examples

## Approach 1: Shamir's Secret Sharing

### Option 1A: Using the CLI (Easiest)

```bash
# Generate and split a new master seed (3-of-5 scheme)
python mpc_cli.py generate -t 3 -n 5 -o ./my_shares

# Derive 5 Bitcoin addresses using 3 shares
python mpc_cli.py derive -c bitcoin \
  -s ./my_shares/share_1.json \
     ./my_shares/share_2.json \
     ./my_shares/share_3.json \
  --count 5

# Derive 3 Ethereum addresses
python mpc_cli.py derive -c ethereum \
  -s ./my_shares/share_*.json \
  --count 3

# Verify shares work correctly
python mpc_cli.py verify -s ./my_shares/share_*.json

# Show share information
python mpc_cli.py info -s ./my_shares/share_1.json
```

### Option 1B: Python Script

```python
from crypto_mpc_keymanager import DistributedKeyManager

# Initialize
manager = DistributedKeyManager()

# Generate and split (3-of-5)
master_seed = manager.generate_master_seed()
shares = manager.split_master_seed(master_seed, threshold=3, num_shares=5)

# Save shares to different locations
for share in shares:
    manager.save_share_to_file(share, f"share_{share.share_id}.json")

# DESTROY master seed (never store it!)
del master_seed

# Later: Load shares and derive keys
share1 = manager.load_share_from_file("share_1.json")
share2 = manager.load_share_from_file("share_2.json")
share3 = manager.load_share_from_file("share_3.json")

# Reconstruct temporarily
recovered_seed = manager.reconstruct_master_seed([share1, share2, share3])

# Derive Bitcoin address 0
btc_key = manager.derive_bitcoin_address_key(recovered_seed, account=0, address_index=0)
print(f"Bitcoin key: {btc_key.hex()}")

# Derive Ethereum address 0
eth_key = manager.derive_ethereum_address_key(recovered_seed, account=0, address_index=0)
print(f"Ethereum key: {eth_key.hex()}")

# Clear from memory
del recovered_seed
```

### Option 1C: Run Demonstrations

```bash
# Basic demonstration
python crypto_mpc_keymanager.py

# Enhanced with address generation
python enhanced_crypto_mpc.py

# Practical workflow simulation
python mpc_workflow_example.py
```

---

## Approach 2: Threshold Cryptography (⭐ RECOMMENDED)

### Option 2A: Complete Workflow Demo

```bash
# Run the complete end-to-end demo (interactive)
python complete_mpc_workflow.py

# This will show:
# - Phase 1: One-time setup with threshold computation
# - Phase 2: Unlimited address generation (no threshold!)
# - Phase 3: Transaction signing with MPC protocol
```

### Option 2B: Python Script

```python
import secrets
from threshold_mpc_keymanager import (
    ThresholdKeyGeneration, ThresholdBIP32
)
from threshold_addresses import BitcoinAddressGenerator
from threshold_signing import ThresholdSigningWorkflow

# PHASE 1: Setup (ONE-TIME threshold computation)
print("Phase 1: Setting up with 3 parties...")

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

print(f"✓ xpub: {btc_xpub.public_key.hex()[:32]}...")
# Each party saves their master_shares[party_id] securely

# PHASE 2: Generate unlimited addresses (NO threshold computation!)
print("\nPhase 2: Generating addresses (no threshold needed)...")

btc_addresses = BitcoinAddressGenerator.generate_addresses_from_xpub(
    btc_xpub, change=0, start_index=0, count=10
)

for addr in btc_addresses:
    print(f"  {addr['path']}: {addr['address']}")

print(f"✓ Generated {len(btc_addresses)} addresses WITHOUT threshold computation!")
print("✓ Can generate UNLIMITED more addresses!")

# PHASE 3: Sign transaction (threshold computation, key NEVER reconstructed)
print("\nPhase 3: Signing transaction...")

message = b"Send 0.5 BTC to recipient"
signature = ThresholdSigningWorkflow.sign_message(
    master_shares,  # Each party uses their share
    message,
    master_pubkey
)

print(f"✓ Signature: {signature.to_compact().hex()[:64]}...")
print("✓ Private key was NEVER reconstructed!")
```

### Option 2C: Run Individual Demos

```bash
# Threshold key generation and BIP32 derivation
python threshold_mpc_keymanager.py

# Address generation from xpub (no private keys!)
python threshold_addresses.py

# Threshold ECDSA signing protocol
python threshold_signing.py
```

## 🔑 Key Concepts

### Threshold Scheme (K-of-N)

**Example: 3-of-5 scheme**
- Create 5 shares
- Need any 3 to reconstruct
- Can lose up to 2 shares safely

**Security:**
- 2 shares → ZERO information
- 3 shares → Full reconstruction

### BIP44 Derivation Paths

**Bitcoin:** `m/44'/0'/account'/change/address_index`
**Ethereum:** `m/44'/60'/account'/change/address_index`

This means one master seed can generate unlimited addresses:
- Account 0, Address 0: `m/44'/0'/0'/0/0`
- Account 0, Address 1: `m/44'/0'/0'/0/1`
- Account 1, Address 0: `m/44'/0'/1'/0/0`
- etc.

## 🔒 Security Best Practices

### ⚠️ CRITICAL RULES

1. **Never store the master seed** - Only store shares
2. **Never store K+ shares together** - Distribute them
3. **Use secure storage** - HSMs, encrypted drives, different locations
4. **Test recovery** - Verify shares work before depositing funds
5. **Backup shares** - Encrypted backups in different locations

### Recommended Setup

**For Personal Use (3-of-5):**
- Share 1: Home safe
- Share 2: Bank safety deposit box
- Share 3: Trusted family member
- Share 4: Second location (office, second home)
- Share 5: Encrypted cloud backup

**For Organizations (5-of-7):**
- Share 1-5: Different executives/board members
- Share 6-7: Escrow/backup locations

## 🛡️ Threat Model

### Protected Against ✅
- Single device compromise
- Loss/theft of individual shares
- Insider threats (no one person has control)
- Physical disasters (distributed storage)

### Still Need Protection Against ⚠️
- Malware during reconstruction
- Social engineering to gather shares
- Compromise of K+ share locations
- Poor operational security

## 📊 Typical Workflow

### Initial Setup (Once)
1. Generate master seed on air-gapped device
2. Split into shares
3. Distribute shares to secure locations
4. **DESTROY master seed**
5. Test recovery with subset of shares

### Regular Operations
1. Gather K shares from distributed locations
2. Temporarily reconstruct seed in secure environment
3. Derive needed addresses/keys
4. Clear seed from memory
5. Return shares to storage

### Emergency Recovery
1. Gather K shares
2. Reconstruct seed
3. Transfer funds to new addresses
4. Generate new share set if needed

## 🧪 Testing First!

**Before using with real funds:**

1. Generate test shares
2. Derive test addresses
3. Send small amount to test address
4. Practice recovery with different share combinations
5. Verify you can access funds
6. Only then use for real funds

## 📚 Learn More

- **README.md** - Full documentation
- **crypto_mpc_keymanager.py** - See implementation details
- **mpc_workflow_example.py** - See practical scenarios

## 🤝 Support

For questions or issues:
1. Check the README.md for detailed explanations
2. Review the example scripts
3. Test with small amounts first
4. Consider professional security audit for production use

## ⚠️ Disclaimer

**Educational purposes only.** You are responsible for:
- Proper security practices
- Testing before production use
- Backing up shares securely
- Understanding the risks

No liability is assumed for lost funds or security breaches.

---

**Remember: The security of your funds depends on how you manage and store the shares. Choose your threshold and distribution strategy carefully!**