# Quick Start Guide - Fixed MPC Signature System

## What Was Fixed

The MPC signature system had a critical bug in hardened BIP32 key derivation. The fix changes how guardian shares are generated and stored:

### Before (❌ Broken):
- Saved **master-level** shares (path: `m`)
- Each guardian tried to derive account shares independently
- Hardened derivation with different private key shares produced different tweaks
- Resulted in incorrect signatures

### After (✅ Fixed):
- Save **account-level** shares (path: `m/44'/0'/0'` for Bitcoin)
- All hardened derivation happens ONCE during setup
- Guardians only perform non-hardened derivation independently
- Produces valid Bitcoin signatures

## Quick Command Reference

```bash
# Generate shares
python3 cli_share_generator.py --guardians 3 --threshold 3 --vault "My Vault" --output demo_output

# Generate new deposit address
python3 cli_generate_address.py --config demo_output/vault_config.json --coin bitcoin

# List all addresses
python3 cli_generate_address.py --config demo_output/vault_config.json --coin bitcoin --list

# Run complete demo
python3 demo_orchestrator.py auto
```

## Getting Started

### 1. Generate New Shares

**Important**: Old shares from before this fix will NOT work! You must regenerate them.

```bash
cd practical_demo

# Generate shares for 3 guardians
python3 cli_share_generator.py \
    --guardians 3 \
    --threshold 3 \
    --vault "My Vault" \
    --output demo_output
```

This creates:
- `demo_output/guardian_1_share.json` - Guardian 1's account-level share
- `demo_output/guardian_2_share.json` - Guardian 2's account-level share
- `demo_output/guardian_3_share.json` - Guardian 3's account-level share
- `demo_output/vault_config.json` - Vault configuration with xpubs

### 2. Verify Shares Are Correct

```bash
# Test 1: Verify account shares sum correctly
python3 verify_account_shares.py \
    --vault-config demo_output/vault_config.json \
    --shares demo_output/guardian_*_share.json

# Test 2: Verify key derivation works
python3 verify_key_derivation.py \
    --vault-config demo_output/vault_config.json \
    --shares demo_output/guardian_*_share.json \
    --address-index 0

# Test 3: Test complete signature flow
python3 test_signature_flow.py \
    --vault-config demo_output/vault_config.json \
    --shares demo_output/guardian_*_share.json \
    --address-index 0
```

All tests should show: ✅ **ALL TESTS PASSED!**

### 3. Generate Deposit Addresses

The vault can generate unlimited deposit addresses without guardian coordination:

```bash
# Generate next Bitcoin address
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin

# Generate multiple addresses at once
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin \
    --count 10

# Generate Ethereum address
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin ethereum

# List all generated addresses
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin \
    --list

# Generate address at specific index
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin \
    --index 100
```

**Features:**
- ✅ Derives addresses from account xpub (no guardian coordination needed)
- ✅ Automatic index tracking
- ✅ Address history saved to `{coin}_addresses.json`
- ✅ Supports both Bitcoin and Ethereum
- ✅ HD derivation path: `m/44'/0'/0'/0/{index}` for Bitcoin

**Address Tracking:**

The tool automatically tracks generated addresses in:
- `demo_output/bitcoin_addresses.json`
- `demo_output/ethereum_addresses.json`

Each entry includes:
- Address index
- Full address
- Public key
- Derivation path
- Usage status

### 4. Run the Complete Demo

```bash
# Start Bitcoin regtest (in one terminal)
cd ../bitcoin-regtest-box
./start.sh

# Start coordination server (in another terminal)
cd ../coordination-server
poetry install
poetry run uvicorn app.main:app --reload

# Run the orchestrator (in a third terminal)
cd ../practical_demo
python3 demo_orchestrator.py auto
```

## Share File Format

### New Format (Current)

```json
{
  "vault_name": "My Vault",
  "guardian_id": 1,
  "total_guardians": 3,
  "threshold": 3,
  "bitcoin_account_share": {
    "party_id": 1,
    "share_value": "4518bde19b864d36...",
    "total_parties": 3,
    "threshold": 3,
    "metadata": {
      "type": "hardened_child",
      "parent_path": "m",
      "index": 2147483648
    }
  },
  "ethereum_account_share": {
    "party_id": 1,
    "share_value": "27a03d1e0b7c55ac...",
    "total_parties": 3,
    "threshold": 3
  },
  "metadata": {
    "share_level": "account",
    "note": "These are account-level shares (m/44'/coin'/0'), not master shares",
    "derivation_paths": {
      "bitcoin": "m/44'/0'/0'",
      "ethereum": "m/44'/60'/0'"
    }
  }
}
```

**Key Differences**:
- ✅ Has `bitcoin_account_share` field (not `share`)
- ✅ Has `ethereum_account_share` field
- ✅ Metadata indicates `"share_level": "account"`
- ✅ Each coin has separate account-level shares

### Legacy Format (Broken - Don't Use)

```json
{
  "share": {
    "party_id": 1,
    "share_value": "...",
    ...
  }
}
```

If you see this format, regenerate your shares!

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        SETUP PHASE                          │
│                  (All Guardians Together)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Generate Master Key Shares (m)                          │
│     share_1 + share_2 + share_3 = master_key                │
│                                                             │
│  2. Derive Bitcoin Account Shares (m/44'/0'/0') - Hardened  │
│     ├─ Compute m/44' (all shares together)                  │
│     ├─ Compute m/44'/0' (all shares together)               │
│     └─ Compute m/44'/0'/0' (all shares together)            │
│                                                             │
│  3. Save Account Shares to Disk                             │
│     └─ Each guardian gets their account-level share         │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       SIGNING PHASE                         │
│                 (Each Guardian Independent)                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Load Account Share (m/44'/0'/0')                        │
│                                                             │
│  2. Derive Change Share (m/44'/0'/0'/0) - Non-hardened      │
│     ├─ Compute tweak from PUBLIC key                        │
│     └─ Each guardian adds tweak/n to their share            │
│                                                             │
│  3. Derive Address Share (m/44'/0'/0'/0/i) - Non-hardened   │
│     ├─ Compute tweak from PUBLIC key                        │
│     └─ Each guardian adds tweak/n to their share            │
│                                                             │
│  4. MPC Signature Protocol (4 rounds)                       │
│     ├─ Round 1: Generate nonce shares                       │
│     ├─ Round 2: Combine R points                            │
│     ├─ Round 3: Compute signature shares                    │
│     └─ Round 4: Combine final signature                     │
│                                                             │
│  5. Valid Bitcoin Signature! ✅                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Concepts

### Hardened vs Non-Hardened Derivation

**Hardened Derivation** (requires coordination):
- Uses **private key** in HMAC: `HMAC(chain, 0x00 || private_key || index)`
- Each guardian has different private key share → different tweaks
- Must derive with ALL guardians together
- Paths: `m/44'`, `m/44'/0'`, `m/44'/0'/0'`

**Non-Hardened Derivation** (independent):
- Uses **public key** in HMAC: `HMAC(chain, public_key || index)`
- All guardians see same public key → same tweak
- Each guardian adds `tweak/n` to their share
- Can derive independently
- Paths: `m/44'/0'/0'/0`, `m/44'/0'/0'/0/0`, `m/44'/0'/0'/0/1`, ...

### Why This Works

For non-hardened derivation with additive secret sharing:

```
Guardian 1: child_1 = parent_1 + (tweak/3)
Guardian 2: child_2 = parent_2 + (tweak/3)
Guardian 3: child_3 = parent_3 + (tweak/3)

Sum: child_1 + child_2 + child_3
   = (parent_1 + parent_2 + parent_3) + 3×(tweak/3)
   = parent_key + tweak  ✅

Which matches BIP32: child_key = parent_key + tweak
```

## Troubleshooting

### Signature verification fails

**Symptom**: `mandatory-script-verify-flag-failed`

**Solution**: Regenerate shares with the new format:
```bash
python3 cli_share_generator.py --guardians 3 --threshold 3 --vault "New Vault" --output new_shares
```

### Old share format error

**Symptom**: `Old share format detected. Please regenerate shares!`

**Solution**: The share file uses the old `"share"` field instead of `"bitcoin_account_share"`. Regenerate shares.

### Shares don't sum to correct public key

**Symptom**: Test shows "❌ KEY DERIVATION MISMATCH!"

**Solution**: This indicates a bug in the derivation logic or incorrect share generation. Check that:
1. All guardians use the same vault config
2. Shares were generated together in one command
3. You're using the latest code

## Additional Resources

- `SIGNATURE_FIX.md` - Detailed explanation of the bug and fix
- `test_signature_flow.py` - Complete end-to-end signature test
- `verify_account_shares.py` - Verify account-level shares
- `verify_key_derivation.py` - Verify address-level derivation

## Summary

✅ **The signature issue is now fixed!**

Key changes:
1. Save account-level shares (not master shares)
2. Guardians load pre-computed account shares
3. Only non-hardened derivation during signing
4. Valid Bitcoin signatures produced

Next steps:
1. Regenerate all shares with new format
2. Run verification tests
3. Test complete transaction flow
4. Deploy to production
