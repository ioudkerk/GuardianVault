# Address Generation Guide

## Overview

The `cli_generate_address.py` tool generates deposit addresses for your GuardianVault without requiring guardian coordination. It uses the account-level xpub to derive unlimited addresses via non-hardened BIP32 derivation.

## How It Works

### Derivation Path

**Bitcoin:** `m/44'/0'/0'/0/{index}`
- `m/44'/0'/0'` - Account level (stored in vault config xpub)
- `0` - Change level (0=receive, 1=change)
- `{index}` - Address index (0, 1, 2, 3, ...)

**Ethereum:** `m/44'/60'/0'/0/{index}`
- `m/44'/60'/0'` - Account level (stored in vault config xpub)
- `0` - Change level (always 0 for Ethereum)
- `{index}` - Address index

### Security Model

✅ **Safe for public use:**
- Derives addresses from **extended public key** (xpub)
- Cannot derive private keys
- Cannot spend funds
- No guardian coordination needed

⚠️ **Privacy consideration:**
- Anyone with the xpub can see all derived addresses
- Keep vault config secure for privacy

## Usage

### Basic Commands

```bash
# Generate next Bitcoin deposit address
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin

# Generate next Ethereum deposit address
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin ethereum
```

### Generate Multiple Addresses

```bash
# Generate 10 Bitcoin addresses
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin \
    --count 10

# Generate 5 Ethereum addresses
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin ethereum \
    --count 5
```

### Generate at Specific Index

```bash
# Generate Bitcoin address at index 100
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin \
    --index 100

# Useful for address recovery or specific derivation paths
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin \
    --index 0  # Regenerate first address
```

### List All Generated Addresses

```bash
# List Bitcoin addresses
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin \
    --list

# List Ethereum addresses
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin ethereum \
    --list
```

### Advanced Options

```bash
# Generate change addresses (index 1)
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin \
    --change 1

# Generate without saving to tracking file
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin \
    --no-save
```

## Address Tracking

### Tracking Files

Generated addresses are automatically saved to:
- `{vault_dir}/bitcoin_addresses.json`
- `{vault_dir}/ethereum_addresses.json`

### Tracking File Format

```json
{
  "addresses": [
    {
      "index": 0,
      "address": "mkv9LaRbvVomNskd63v3UkLvY4q1dXu9tE",
      "public_key": "03e6555f9a709cb3413ad96eb252e491...",
      "path": "m/44'/0'/0'/0/0",
      "used": false
    },
    {
      "index": 1,
      "address": "mmcZAvzQxX29J5yzb6EAgcepRgZb7wi8V3",
      "public_key": "0292c9e4b6870b868b259d64e6e2e8ef...",
      "path": "m/44'/0'/0'/0/1",
      "used": false
    }
  ],
  "next_index": 2
}
```

### Fields

- **index:** Address index in the derivation path
- **address:** Full blockchain address
- **public_key:** Compressed public key (hex)
- **path:** Full BIP32 derivation path
- **used:** Whether address has received funds (manual tracking)

## Example Output

### Generate Address

```
======================================================================
GENERATING BITCOIN ADDRESS(ES)
======================================================================
Vault: Demo Vault
Network: regtest
======================================================================

Address #0:
  Path:       m/44'/0'/0'/0/0
  Address:    mkv9LaRbvVomNskd63v3UkLvY4q1dXu9tE
  Public Key: 03e6555f9a709cb3413ad96eb252e491...1ec8367134f615c78f6ff05a29fcbff8
  ✓ Saved to tracking file

======================================================================
✅ Generated 1 bitcoin address(es)
======================================================================

💡 Tip: Use --list to see all generated addresses
   python3 cli_generate_address.py --config demo_output/vault_config.json --coin bitcoin --list
```

### List Addresses

```
======================================================================
BITCOIN ADDRESSES
======================================================================
Total addresses: 5
Next index: 5

Index    Address                                       Used   Path
----------------------------------------------------------------------
0        mkv9LaRbvVomNskd63v3UkLvY4q1dXu9tE                   m/44'/0'/0'/0/0
1        mmcZAvzQxX29J5yzb6EAgcepRgZb7wi8V3                   m/44'/0'/0'/0/1
2        mqPqfvhGA284b2y6i6LNtutZXvgs4AWxcf                   m/44'/0'/0'/0/2
3        n2KSNjQ4UMLHiNLSaB5Y8C3i8z6Tqmz51N                   m/44'/0'/0'/0/3
4        mgrfN3MhL1TRRAVXTUpR47SniEbqk2sjGe                   m/44'/0'/0'/0/4
======================================================================
```

## Integration Example

### Python Script

```python
import subprocess
import json

def generate_deposit_address(vault_config: str, coin: str = "bitcoin"):
    """Generate new deposit address"""
    result = subprocess.run([
        "python3", "cli_generate_address.py",
        "--config", vault_config,
        "--coin", coin,
        "--no-save"  # Generate without tracking
    ], capture_output=True, text=True)

    # Parse output to extract address
    # (implement parsing based on your needs)
    return result.stdout

# Usage
address = generate_deposit_address("demo_output/vault_config.json", "bitcoin")
print(f"New deposit address: {address}")
```

### Web API Integration

```python
from flask import Flask, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/api/addresses/bitcoin/new', methods=['POST'])
def new_bitcoin_address():
    """Generate new Bitcoin deposit address"""
    # Generate address
    subprocess.run([
        "python3", "cli_generate_address.py",
        "--config", "vault_config.json",
        "--coin", "bitcoin"
    ])

    # Load tracking file
    with open('bitcoin_addresses.json', 'r') as f:
        data = json.load(f)

    # Return latest address
    latest = data['addresses'][-1]
    return jsonify({
        'address': latest['address'],
        'index': latest['index'],
        'path': latest['path']
    })

@app.route('/api/addresses/bitcoin', methods=['GET'])
def list_bitcoin_addresses():
    """List all Bitcoin addresses"""
    with open('bitcoin_addresses.json', 'r') as f:
        data = json.load(f)
    return jsonify(data)
```

## Best Practices

### Address Reuse

❌ **Don't reuse addresses:**
```bash
# Bad: Always using index 0
cli_generate_address.py --coin bitcoin --index 0
```

✅ **Generate new address for each deposit:**
```bash
# Good: Use next available index
cli_generate_address.py --coin bitcoin
```

### Gap Limit

BIP44 defines a **gap limit of 20** - if 20 consecutive addresses are unused, wallet recovery stops scanning.

**Recommendation:**
- Generate addresses sequentially
- Don't skip large index ranges
- Keep gap under 20 unused addresses

### Address Monitoring

Track which addresses have been used:

```python
import json

def mark_address_used(coin: str, address: str):
    """Mark address as used when funds received"""
    tracking_file = f"{coin}_addresses.json"

    with open(tracking_file, 'r') as f:
        data = json.load(f)

    for addr in data['addresses']:
        if addr['address'] == address:
            addr['used'] = True
            break

    with open(tracking_file, 'w') as f:
        json.dump(data, f, indent=2)
```

### Backup

Always backup tracking files:
```bash
# Backup address tracking
cp bitcoin_addresses.json bitcoin_addresses.backup.json
cp ethereum_addresses.json ethereum_addresses.backup.json
```

## Troubleshooting

### Error: File not found

**Symptom:** `❌ Error: File not found - vault_config.json`

**Solution:** Provide correct path to vault config:
```bash
python3 cli_generate_address.py --config demo_output/vault_config.json --coin bitcoin
```

### Error: Invalid vault config

**Symptom:** `❌ Error: Invalid vault config - missing key 'bitcoin'`

**Solution:** Regenerate vault config with latest share generator:
```bash
python3 cli_share_generator.py --guardians 3 --threshold 3 --vault "New Vault" --output new_vault
```

### Addresses don't match expected

**Symptom:** Generated addresses don't match blockchain explorer

**Possible causes:**
1. Wrong network (mainnet vs testnet vs regtest)
2. Wrong derivation path
3. Different xpub used

**Solution:** Verify vault config matches expected parameters

## FAQ

### Can I generate addresses offline?

✅ **Yes!** Address generation only needs the vault config (xpub), no network connection required.

### Do I need guardians online to generate addresses?

❌ **No!** Guardians are only needed for **signing transactions**, not generating addresses.

### How many addresses can I generate?

✅ **2^31 (2.1 billion)** - BIP32 allows indices from 0 to 2,147,483,647 for non-hardened derivation.

### Can someone steal funds with the xpub?

❌ **No!** The xpub can only **derive addresses and view balances**, it cannot:
- Derive private keys
- Sign transactions
- Spend funds

⚠️ **Privacy risk:** Anyone with xpub can see all your addresses and balances.

### What if I lose the tracking file?

✅ **Addresses can be regenerated** using the same index:
```bash
# Regenerate specific address
python3 cli_generate_address.py --config vault_config.json --coin bitcoin --index 5
```

The blockchain doesn't know about your tracking file - addresses are deterministically derived from xpub + index.

## Security Considerations

### What to Keep Secret

🔒 **Highly Secret (Never Share):**
- Guardian key shares
- Master private key (never exists!)
- Account private keys (never reconstructed!)

🔐 **Private (Limit Access):**
- Vault configuration file (contains xpub)
- Address tracking files
- Share files

✅ **Safe to Share:**
- Individual addresses for receiving funds

### Secure Storage

```bash
# Set proper permissions
chmod 600 demo_output/vault_config.json
chmod 600 demo_output/guardian_*_share.json
chmod 600 demo_output/bitcoin_addresses.json

# Backup securely
gpg --encrypt --recipient your@email.com vault_config.json
```

## Summary

The address generation tool provides:

✅ **Unlimited addresses** from a single xpub
✅ **No guardian coordination** required
✅ **Automatic tracking** of generated addresses
✅ **BIP32/BIP44 compliant** derivation
✅ **Privacy-preserving** (xpub stays local)
✅ **Multi-currency** support (Bitcoin, Ethereum)

Use it to generate deposit addresses for your GuardianVault without needing to wake up the guardians!
