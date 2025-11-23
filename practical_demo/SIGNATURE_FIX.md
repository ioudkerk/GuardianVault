# MPC Signature Fix - Root Cause and Solution

## Problem Summary

Bitcoin transaction signatures were failing verification with the error:
```
mandatory-script-verify-flag-failed (Signature must be zero for failed CHECK(MULTI)SIG operation)
```

## Root Cause

The issue was in how **hardened BIP32 key derivation** works with **additive secret sharing** in a distributed/threshold setting.

### The Fundamental Issue

In the original implementation:
1. **Master-level shares** were saved to disk
2. Each guardian **independently** tried to derive account-level shares (m/44'/0'/0') by calling `derive_hardened_child_threshold([their_share], ...)`
3. For hardened derivation, the HMAC computation uses the private key: `HMAC(chain_code, 0x00 || private_key || index)`

### Why This Failed

When each guardian computed hardened derivation independently:

**Guardian 1**: `tweak_1 = HMAC(chain, 0x00 || share_1 || index)` → `child_1 = share_1 + tweak_1`
**Guardian 2**: `tweak_2 = HMAC(chain, 0x00 || share_2 || index)` → `child_2 = share_2 + tweak_2`
**Guardian 3**: `tweak_3 = HMAC(chain, 0x00 || share_3 || index)` → `child_3 = share_3 + tweak_3`

Sum of derived shares: `(share_1 + share_2 + share_3) + (tweak_1 + tweak_2 + tweak_3)` ❌

But BIP32 requires: `parent_key + HMAC(chain, 0x00 || parent_key || index)` ✅

Since each guardian uses a **different share** in the HMAC, they get **different tweaks**, causing the sum to be incorrect!

### Why Non-Hardened Derivation Works

Non-hardened derivation uses the **public key** for HMAC:
```
tweak = HMAC(chain_code, public_key || index)
```

All guardians see the **same public key**, so they compute the **same tweak**. Each guardian adds `tweak/n` to their share:

```
child_share_i = parent_share_i + (tweak / n)
```

Sum: `(share_1 + share_2 + share_3) + 3×(tweak/3) = parent_key + tweak` ✅

## Solution

The fix involves two key changes:

### 1. Pre-Compute Hardened Derivations During Setup

**Before** (`cli_share_generator.py`):
```python
# Saved master-level shares
for i, share in enumerate(master_shares, 1):
    share_data = {
        "share": master_share.to_dict()  # Master level (m)
    }
```

**After**:
```python
# Derive account shares with ALL guardians together
btc_account_shares, btc_account_pubkey, btc_account_chain = \
    ThresholdBIP32.derive_hardened_child_threshold(
        master_shares,  # All shares together!
        None, chain_code, ...
    )

# Save account-level shares
for i, btc_share in enumerate(btc_account_shares, 1):
    share_data = {
        "bitcoin_account_share": btc_share.to_dict()  # Account level (m/44'/0'/0')
    }
```

### 2. Guardian Client Uses Pre-Computed Account Shares

**Before** (`cli_guardian_client.py`):
```python
# WRONG: Each guardian tried to derive independently
def _derive_bitcoin_account_share(self, master_share, chain_code):
    purpose_shares, _, _ = ThresholdBIP32.derive_hardened_child_threshold(
        [master_share], ...  # Single share!
    )
    # ... produces incorrect shares
```

**After**:
```python
# RIGHT: Load pre-computed account share
def __init__(...):
    self.bitcoin_account_share = KeyShare.from_dict(
        share_data['bitcoin_account_share']  # Already at m/44'/0'/0'
    )

# Then derive addresses using non-hardened derivation
change_share = self._derive_non_hardened_child_share(
    self.bitcoin_account_share,  # From m/44'/0'/0'
    account_xpub.public_key,
    account_xpub.chain_code,
    0  # Change index
)
```

## Architecture Overview

```
Setup Phase (All Guardians Together):
┌─────────────────────────────────────┐
│ Generate master shares (m)          │
│   ↓ (hardened, all together)        │
│ Derive account shares (m/44'/0'/0') │
│   ↓ SAVE TO DISK                    │
└─────────────────────────────────────┘

Signing Phase (Each Guardian Independently):
┌─────────────────────────────────────┐
│ Load account share (m/44'/0'/0')    │
│   ↓ (non-hardened, independent)     │
│ Derive change share (m/44'/0'/0'/0) │
│   ↓ (non-hardened, independent)     │
│ Derive address (m/44'/0'/0'/0/i)    │
│   ↓ MPC SIGNING                      │
│ Create valid signature               │
└─────────────────────────────────────┘
```

## Files Modified

1. **`cli_share_generator.py`**:
   - Now derives and saves account-level shares for both Bitcoin and Ethereum
   - Uses `bitcoin_account_share` and `ethereum_account_share` fields

2. **`cli_guardian_client.py`**:
   - Loads account-level shares directly
   - Removed `_derive_bitcoin_account_share()` method
   - Only performs non-hardened derivation from account level

3. **`test_signature_flow.py`**:
   - Updated to load account-level shares
   - Simplified derivation logic

## Verification

Run the test to verify correct operation:

```bash
cd practical_demo

# Test signature flow
python3 test_signature_flow.py \
    --vault-config demo_output/vault_config.json \
    --shares demo_output/guardian_*_share.json \
    --address-index 0
```

Expected output:
```
✅ SUCCESS! MPC SIGNATURE IS VALID!

All steps:
  ✅ Key derivation correct (shares sum to private key)
  ✅ Nonce generation correct
  ✅ R point combination correct
  ✅ Signature shares correct
  ✅ Final signature valid
```

## Key Takeaways

1. **Hardened derivation in MPC requires coordination** - all parties must participate together
2. **Pre-compute hardened paths during setup** - save derived shares at the account level
3. **Use non-hardened derivation for addresses** - each guardian can derive independently
4. **Share format matters** - clearly document what level shares are at (master vs account vs address)

This design pattern is common in threshold wallet implementations:
- **One-time ceremony**: DKG + hardened derivation to account level
- **Runtime operations**: Non-hardened derivation + MPC signing
