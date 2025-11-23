# Bitcoin Address Types Support

GuardianVault now supports all three major Bitcoin address formats for generating deposit addresses.

## Address Types

### 1. P2PKH (Pay-to-Public-Key-Hash) - Legacy
**Format**: Base58 encoding
**Mainnet**: Starts with `1`
**Testnet/Regtest**: Starts with `m` or `n`
**Example**: `mzeLPxJsJ7dmbnX2unxSQ3Hmi91V2R1FDi`

**When to use**: Maximum compatibility with older wallets and exchanges

### 2. P2WPKH (Pay-to-Witness-Public-Key-Hash) - SegWit
**Format**: Bech32 encoding (BIP 173)
**Witness Version**: 0
**Mainnet**: Starts with `bc1q`
**Testnet**: Starts with `tb1q`
**Regtest**: Starts with `bcrt1q`
**Example**: `bcrt1qks7q08zn2r0jqkt3l0vtx6hnpxmxu3temeuuvn`

**When to use**: Lower transaction fees, better for most modern uses

### 3. P2TR (Pay-to-Taproot) - Taproot
**Format**: Bech32m encoding (BIP 350)
**Witness Version**: 1
**Mainnet**: Starts with `bc1p`
**Testnet**: Starts with `tb1p`
**Regtest**: Starts with `bcrt1p`
**Example**: `bcrt1ppmxxs2c8l7z63e90kddl2m35zuqqlvmnd492djem7rxpp8c4dkgqef8jy6`

**When to use**: Maximum privacy, lowest fees, future-proof

## Important Limitation: P2TR Spending

⚠️ **Taproot (P2TR) spending is not yet supported** because Taproot requires **Schnorr signatures**, while GuardianVault's current MPC implementation uses **ECDSA signatures**.

**What works:**
- ✅ Generate P2TR addresses for receiving funds
- ✅ Send TO P2TR addresses (as recipients)
- ✅ Use P2TR addresses for change outputs

**What doesn't work yet:**
- ❌ Spending FROM P2TR addresses (requires Schnorr MPC implementation)

**Workaround**: Use P2PKH or P2WPKH addresses for spending. These work perfectly with the current ECDSA-based MPC signing protocol.

## Usage

### Generate Different Address Types

```bash
# Legacy P2PKH address (default)
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin

# SegWit P2WPKH address
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin \
    --type p2wpkh

# Taproot P2TR address
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin \
    --type p2tr
```

### Generate Multiple Addresses

```bash
# Generate 10 Taproot addresses
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin \
    --type p2tr \
    --count 10
```

### List Generated Addresses

```bash
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin \
    --list
```

Output shows address type for each entry:
```
Index    Type       Address                                       Used   Path
--------------------------------------------------------------------------------
0        p2tr       bcrt1phl43a8aggpfy2kpw9s9f0u3tvv7d5326...        m/44'/0'/0'/0/0
1        p2pkh      muwtUh7U2dczESzuuxtpjGcvbZfsRBH7V4                m/44'/0'/0'/0/1
2        p2wpkh     bcrt1qwckd2arlvluhxws7g4w7xaymfj2ekg5...         m/44'/0'/0'/0/2
```

### Use Address Types in Transactions

The `cli_create_and_broadcast.py` script automatically detects the address type from the tracking file:

```bash
# Auto-detect address type from bitcoin_addresses.json
python3 cli_create_and_broadcast.py \
    --vault-id vault_123 \
    --vault-config demo_output/vault_config.json \
    --recipient bcrt1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh \
    --amount 0.5 \
    --address-index 5
# If index 5 is P2WPKH in the tracking file, it will be used automatically

# Explicitly specify address type (overrides tracking file)
python3 cli_create_and_broadcast.py \
    --vault-id vault_123 \
    --vault-config demo_output/vault_config.json \
    --recipient bcrt1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh \
    --amount 0.5 \
    --address-index 6 \
    --address-type p2wpkh

# Send TO a Taproot address (as recipient - this works!)
python3 cli_create_and_broadcast.py \
    --vault-id vault_123 \
    --vault-config demo_output/vault_config.json \
    --recipient bcrt1p... \
    --amount 0.5 \
    --address-index 3 \
    --address-type p2pkh
```

**Address Type Detection Logic:**
1. If `--address-type` specified → use it
2. Else if address found in `bitcoin_addresses.json` → use its type
3. Else → default to P2PKH

## Technical Details

### Bech32 vs Bech32m

- **Bech32** (BIP 173): Used for SegWit v0 addresses (P2WPKH, P2WSH)
  - Checksum constant: `1`
  - Character set: `qpzry9x8gf2tvdw0s3jn54khce6mua7l`

- **Bech32m** (BIP 350): Used for SegWit v1+ addresses (Taproot)
  - Checksum constant: `0x2bc830a3`
  - Same character set as Bech32
  - Better mutation detection

### Taproot Public Keys

Taproot uses **x-only public keys** (32 bytes) instead of compressed public keys (33 bytes):
- Compressed: `02` or `03` prefix + 32-byte x-coordinate
- X-only: Just the 32-byte x-coordinate (y-coordinate implied)

## Compatibility

### Network Support

All three address types support:
- ✅ Mainnet
- ✅ Testnet
- ✅ Regtest

### Bitcoin Core Compatibility

- P2PKH: All versions
- P2WPKH: Bitcoin Core 0.16.0+ (SegWit activation)
- P2TR: Bitcoin Core 22.0+ (Taproot activation)

### Exchange/Wallet Compatibility

Most modern exchanges and wallets support:
- ✅ P2PKH (universal support)
- ✅ P2WPKH (wide support, activated 2017)
- ⚠️ P2TR (growing support, activated November 2021)

**Recommendation**: Use P2WPKH for best balance of compatibility and efficiency. Use P2TR for maximum privacy and future-proofing.

## Address Tracking

All generated addresses are tracked in `{coin}_addresses.json` with:
- Address index
- Address type (p2pkh, p2wpkh, p2tr)
- Full address string
- Public key
- Derivation path
- Used flag

Example tracking entry:
```json
{
  "index": 0,
  "address_type": "p2tr",
  "address": "bcrt1phl43a8aggpfy2kpw9s9f0u3tvv7d5326uefrdnrlu80sj4dxq2wqwv984w",
  "public_key": "03bfeb1e9fa8405245582e2c0a97f22b633cda455ae65236cc7fe1df0955a6029c",
  "path": "m/44'/0'/0'/0/0",
  "used": false
}
```

## Implementation Notes

### MPC Compatibility

All address types are fully compatible with GuardianVault's MPC signing:
- Address generation uses only public keys (no private key needed)
- Signing works with any address type
- Guardians don't need to know address type when signing

### Derivation Path

All addresses follow BIP44 path structure:
```
m/44'/0'/0'/0/i
```
Where `i` is the address index.

### Security

- P2PKH: Standard ECDSA security
- P2WPKH: SegWit transaction malleability fix
- P2TR: Enhanced privacy through Schnorr signatures and MAST

## Resources

- [BIP 44](https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki) - Multi-Account Hierarchy
- [BIP 141](https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki) - SegWit
- [BIP 173](https://github.com/bitcoin/bips/blob/master/bip-0173.mediawiki) - Bech32 encoding
- [BIP 341](https://github.com/bitcoin/bips/blob/master/bip-0341.mediawiki) - Taproot
- [BIP 350](https://github.com/bitcoin/bips/blob/master/bip-0350.mediawiki) - Bech32m encoding

---

**Status**: All address types fully implemented and tested ✅
**Last Updated**: 2025-11-18
