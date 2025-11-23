# Development Guide

This guide helps you (or Claude) continue working on the GuardianVault project.

## Project Overview

**GuardianVault** is a threshold MPC wallet system using additive secret sharing for Bitcoin and Ethereum. The system enables multiple guardians to collaboratively sign transactions without ever reconstructing the private key.

### Key Components

```
GuardianVault/
├── guardianvault/              # Core cryptographic library
│   ├── threshold_mpc_keymanager.py  # Key generation, BIP32 derivation
│   ├── threshold_signing.py         # MPC ECDSA signing protocol
│   ├── threshold_addresses.py       # Address generation
│   └── bitcoin_transaction.py       # Bitcoin transaction building
├── coordination-server/        # FastAPI + Socket.IO server
│   ├── app/
│   │   ├── routers/            # REST API endpoints
│   │   ├── websocket/          # Socket.IO handlers
│   │   ├── services/           # MPC coordination logic
│   │   └── models/             # Data models
│   └── run_server.sh           # Start script
├── practical_demo/             # Complete demo system
│   ├── cli_*.py                # CLI tools
│   ├── demo_orchestrator.py    # Automated workflow
│   └── *.md                    # Documentation
└── bitcoin-regtest-box/        # Local Bitcoin regtest environment
```

## Architecture

### Critical Concepts

1. **Additive Secret Sharing**: Private key = share_1 + share_2 + ... + share_n (mod N)
2. **Account-Level Shares**: Shares are stored at m/44'/coin'/0', NOT at master level
3. **Non-Hardened Derivation**: Addresses derived independently using public keys
4. **Threshold Signing**: 4-round MPC protocol for ECDSA signatures

### Key Derivation Hierarchy

```
Setup Phase (All Guardians Together):
  Master Shares (m)
    ↓ Hardened derivation (requires coordination)
  Purpose Shares (m/44')
    ↓ Hardened derivation
  Coin Shares (m/44'/0')
    ↓ Hardened derivation
  Account Shares (m/44'/0'/0') [SAVED TO DISK]

Runtime (Each Guardian Independent):
  Account Shares (m/44'/0'/0')
    ↓ Non-hardened derivation (independent)
  Change Shares (m/44'/0'/0'/0)
    ↓ Non-hardened derivation
  Address Shares (m/44'/0'/0'/0/i) [USED FOR SIGNING]
```

## Development Setup

### Prerequisites

```bash
# Install Poetry (Python dependency manager)
curl -sSL https://install.python-poetry.org | python3 -

# Install system dependencies (macOS)
brew install bitcoin

# Or use Docker for Bitcoin regtest
cd bitcoin-regtest-box
./start.sh
```

### Initial Setup

```bash
# Clone and enter project
cd /Users/ivan/projects/personal/GuardianVault

# Install guardianvault package
poetry install

# Install coordination server dependencies
cd coordination-server
poetry install
cd ..

# Install demo dependencies
cd practical_demo
pip3 install -r requirements.txt
cd ..
```

## Working on the Project

### Branch Strategy

```bash
# Always work on feature branches
git checkout main
git pull origin main
git checkout -b feat/your-feature-name

# Make changes...

# Commit with descriptive message
git add .
git commit -m "feat: Your feature description"

# Push to remote
git push -u origin feat/your-feature-name

# Create PR on GitHub
```

### Commit Message Convention

```
<type>: <subject>

<body>

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`

### Current Branch

You are currently on: `feat/fix-mpc-signature-and-address-generation`

## Testing

### Run All Tests

```bash
cd practical_demo

# Test 1: Verify account shares
python3 verify_account_shares.py \
    --vault-config demo_output/vault_config.json \
    --shares demo_output/guardian_*_share.json

# Test 2: Verify key derivation
python3 verify_key_derivation.py \
    --vault-config demo_output/vault_config.json \
    --shares demo_output/guardian_*_share.json \
    --address-index 0

# Test 3: Complete signature flow
python3 test_signature_flow.py \
    --vault-config demo_output/vault_config.json \
    --shares demo_output/guardian_*_share.json \
    --address-index 0
```

All tests should show: **✅ ALL TESTS PASSED!**

### Manual Testing

```bash
# Start Bitcoin regtest
cd bitcoin-regtest-box
./start.sh

# Start coordination server (in another terminal)
cd coordination-server
./run_server.sh

# Run demo orchestrator (in another terminal)
cd practical_demo
python3 demo_orchestrator.py auto
```

## Common Tasks

### 1. Add New Feature to Signing Protocol

```bash
# File to modify:
coordination-server/app/websocket/signing_protocol.py

# Add event handler:
@sio.on('your_new_event')
async def handle_new_event(sid, data):
    # Implementation
    pass

# Test with:
cd practical_demo
python3 cli_guardian_client.py run --server http://localhost:8000 ...
```

### 2. Add New CLI Tool

```bash
# Create in practical_demo/
cd practical_demo

# Copy template from existing CLI
cp cli_generate_address.py cli_your_tool.py

# Make executable
chmod +x cli_your_tool.py

# Test
python3 cli_your_tool.py --help
```

### 3. Modify Key Derivation

**⚠️ CRITICAL**: Never modify hardened derivation logic without understanding implications!

```bash
# Files to check:
guardianvault/threshold_mpc_keymanager.py  # Core derivation logic
practical_demo/cli_share_generator.py       # Account share generation
practical_demo/cli_guardian_client.py       # Non-hardened derivation

# Always run tests after modifications:
cd practical_demo
python3 verify_account_shares.py --vault-config ... --shares ...
python3 verify_key_derivation.py --vault-config ... --shares ...
python3 test_signature_flow.py --vault-config ... --shares ...
```

### 4. Add New Cryptocurrency Support

```bash
# 1. Add coin type constant
# guardianvault/threshold_mpc_keymanager.py
COIN_TYPE_LITECOIN = 2

# 2. Add address generator
# guardianvault/threshold_addresses.py
class LitecoinAddressGenerator:
    @staticmethod
    def pubkey_to_address(pubkey: bytes, network: str = "mainnet") -> str:
        # Implementation
        pass

# 3. Update share generator
# practical_demo/cli_share_generator.py
# Add Litecoin xpub derivation

# 4. Update address generator CLI
# practical_demo/cli_generate_address.py
# Add 'litecoin' to coin choices

# 5. Test
python3 cli_share_generator.py --guardians 3 --threshold 3 ...
python3 cli_generate_address.py --coin litecoin ...
```

### 5. Regenerate Shares After Changes

```bash
cd practical_demo

# Remove old shares
rm -rf demo_output

# Generate new shares
python3 cli_share_generator.py \
    --guardians 3 \
    --threshold 3 \
    --vault "Test Vault" \
    --output demo_output

# Verify
python3 verify_account_shares.py \
    --vault-config demo_output/vault_config.json \
    --shares demo_output/guardian_*_share.json
```

## Critical Files

### Never Modify Without Understanding

1. **guardianvault/threshold_mpc_keymanager.py**
   - Core cryptography
   - BIP32 derivation (especially `derive_hardened_child_threshold`)
   - Any changes require extensive testing

2. **guardianvault/threshold_signing.py**
   - ECDSA signing protocol
   - Changes can break signature validity
   - Must maintain compatibility with Bitcoin/Ethereum

3. **practical_demo/cli_share_generator.py**
   - Account share generation
   - Changes affect all guardians
   - Breaking changes require share regeneration

### Safe to Modify

1. **practical_demo/cli_*.py** (CLI tools)
   - User interface changes
   - New commands/options
   - Error handling improvements

2. **coordination-server/app/routers/*.py** (API endpoints)
   - REST API changes
   - Validation logic
   - Response formats

3. **Documentation (*.md files)**
   - Always safe to improve
   - Keep technical accuracy

## Debugging

### Common Issues

#### 1. Signature Verification Fails

```bash
# Check key derivation
cd practical_demo
python3 verify_key_derivation.py \
    --vault-config demo_output/vault_config.json \
    --shares demo_output/guardian_*_share.json

# Debug signature computation
python3 debug_signature.py \
    --server http://localhost:8000 \
    --transaction-id <tx_id> \
    --vault-config demo_output/vault_config.json
```

**Root Cause Checklist**:
- [ ] Are shares at account level (not master level)?
- [ ] Is non-hardened derivation using tweak/n formula?
- [ ] Do all guardians have same vault config?
- [ ] Is address derivation index correct?

#### 2. Guardians Can't Connect

```bash
# Check server status
curl http://localhost:8000/health

# Check guardian authentication
# coordination-server logs should show:
# "Client connected: <sid>"

# Verify guardian is registered
curl http://localhost:8000/api/guardians/<guardian_id>
```

#### 3. Address Generation Fails

```bash
# Verify vault config exists
cat demo_output/vault_config.json

# Check xpub format
python3 -c "
import json
with open('demo_output/vault_config.json') as f:
    config = json.load(f)
    print('Bitcoin xpub:', config['bitcoin']['xpub']['public_key'][:20])
"

# Regenerate if needed
python3 cli_share_generator.py ...
```

## Code Style

### Python

```python
# Use type hints
def derive_address(account_share: KeyShare, index: int) -> tuple[str, bytes]:
    pass

# Document complex functions
def sign_round3_compute_signature_share(...) -> int:
    """
    Compute signature share for round 3.

    For additive secret sharing: s_i = k^(-1) * (z/n + r*x_i) mod n

    Args:
        key_share: This guardian's key share
        nonce_share: This guardian's nonce share
        message_hash: Transaction hash to sign
        r: Combined R point x-coordinate
        k_total: Sum of all nonce shares
        num_parties: Total number of guardians

    Returns:
        Signature share (integer)
    """
    pass

# Use descriptive variable names
tweak_share = (tweak * pow(n, -1, SECP256K1_N)) % SECP256K1_N  # Good
t = (x * pow(n, -1, N)) % N  # Bad
```

### Documentation

```markdown
## Use Clear Headings

### Subsections Should Be Descriptive

- Bullet points for lists
- **Bold** for emphasis
- `code` for commands/code

```bash
# Code blocks with language
python3 script.py
```

✅ Use checkmarks for success
❌ Use X marks for failures
⚠️ Use warnings for important notes
```

## Release Process

### Preparing a Release

```bash
# 1. Ensure all tests pass
cd practical_demo
./run_all_tests.sh  # If you create this

# 2. Update version in pyproject.toml
# coordination-server/pyproject.toml
# guardianvault/pyproject.toml
version = "0.2.0"

# 3. Update CHANGELOG.md (if exists)
# Add release notes

# 4. Commit version bump
git add .
git commit -m "chore: Bump version to 0.2.0"

# 5. Tag release
git tag -a v0.2.0 -m "Release v0.2.0: MPC signature fix and address generation"

# 6. Push
git push origin main --tags
```

## Project Context

### What Was Recently Fixed

**Critical Bug**: MPC signature verification failure
- **Problem**: Hardened BIP32 derivation incompatible with independent guardian derivation
- **Solution**: Pre-compute hardened paths during setup, save account-level shares
- **Files**: See commit `0a68297` and `db624af`

### What Was Recently Added

**Feature**: Address generation CLI
- **Purpose**: Generate unlimited deposit addresses without guardian coordination
- **Tool**: `practical_demo/cli_generate_address.py`
- **Docs**: `practical_demo/ADDRESS_GENERATION.md`

### Current State

✅ **Working**:
- MPC signature generation and verification
- Bitcoin transaction building and broadcasting
- Address generation (Bitcoin and Ethereum)
- Complete demo workflow

⚠️ **Needs Improvement**:
- Error handling in coordination server
- Guardian reconnection logic
- Transaction status monitoring
- Production deployment guide

🔜 **Future Work**:
- Ethereum transaction support
- Hardware wallet integration
- Web interface
- Mobile app

## Getting Help

### Documentation

1. **practical_demo/QUICK_START.md** - User guide
2. **practical_demo/SIGNATURE_FIX.md** - Technical deep-dive on signature fix
3. **practical_demo/ADDRESS_GENERATION.md** - Address generation guide
4. **practical_demo/README.md** - Demo system overview

### Understanding the Codebase

```bash
# Start with these files in order:
1. README.md (project overview)
2. practical_demo/QUICK_START.md (how to use)
3. guardianvault/threshold_mpc_keymanager.py (core crypto)
4. guardianvault/threshold_signing.py (signing protocol)
5. practical_demo/cli_share_generator.py (share generation)
6. practical_demo/cli_guardian_client.py (guardian client)
```

### Running Examples

```bash
# See practical_demo/DEMO_CHEATSHEET.md for quick commands
cd practical_demo
cat DEMO_CHEATSHEET.md
```

## Important Notes

### Security Considerations

1. **Never commit shares**: demo_output/ is in .gitignore
2. **Never commit private keys**: They should never exist!
3. **Test mode only**: This is for testing, not production

### Share File Format

**Current format** (v0.2.0+):
```json
{
  "bitcoin_account_share": {...},
  "ethereum_account_share": {...},
  "metadata": {"share_level": "account"}
}
```

**Legacy format** (v0.1.0):
```json
{
  "share": {...}  // Master level - BROKEN!
}
```

If you see legacy format, regenerate shares!

### Mathematical Formulas

**Non-hardened child derivation** (each guardian independently):
```
tweak = HMAC-SHA512(chain_code, public_key || index)
tweak_share_i = tweak / n (mod SECP256K1_N)
child_share_i = parent_share_i + tweak_share_i (mod SECP256K1_N)

Result: sum(child_shares) = sum(parent_shares) + tweak ✅
```

**Signature share computation** (round 3):
```
s_i = k^(-1) * (z/n + r*x_i) mod n

Where:
- k = sum of nonce shares
- z = message hash
- r = R point x-coordinate
- x_i = this guardian's key share
```

## Quick Reference

### Commands

```bash
# Generate shares
python3 cli_share_generator.py -g 3 -t 3 -v "Vault" -o output

# Generate address
python3 cli_generate_address.py -c vault_config.json --coin bitcoin

# Start server
cd coordination-server && ./run_server.sh

# Run demo
cd practical_demo && python3 demo_orchestrator.py auto

# Run tests
python3 verify_account_shares.py -c config.json --shares *.json
python3 verify_key_derivation.py -c config.json --shares *.json
python3 test_signature_flow.py -c config.json --shares *.json
```

### File Locations

```
Configuration: practical_demo/demo_output/vault_config.json
Shares: practical_demo/demo_output/guardian_*_share.json
Addresses: practical_demo/demo_output/{coin}_addresses.json
Server: coordination-server/
Docs: practical_demo/*.md
```

### Git Workflow

```bash
# Start work
git checkout main && git pull
git checkout -b feat/my-feature

# Make changes, commit
git add . && git commit -m "feat: My feature"

# Push and create PR
git push -u origin feat/my-feature
```

---

**Current Branch**: `feat/fix-mpc-signature-and-address-generation`
**Last Updated**: 2025-11-18
**Maintainer**: Ivan Oudkerk

**Ready to continue working! All systems operational.** 🚀
