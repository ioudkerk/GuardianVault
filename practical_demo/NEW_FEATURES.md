# New Feature: Address Generation CLI

## Summary

Added `cli_generate_address.py` - a command-line tool to generate unlimited deposit addresses without requiring guardian coordination.

## Key Features

### ✅ Generate Deposit Addresses

Generate Bitcoin and Ethereum addresses directly from the vault's xpub:

```bash
# Generate Bitcoin address
python3 cli_generate_address.py --config vault_config.json --coin bitcoin

# Generate Ethereum address
python3 cli_generate_address.py --config vault_config.json --coin ethereum

# Generate multiple addresses
python3 cli_generate_address.py --config vault_config.json --coin bitcoin --count 10
```

### ✅ Automatic Address Tracking

Automatically tracks generated addresses in JSON files:
- `bitcoin_addresses.json`
- `ethereum_addresses.json`

Each entry includes:
- Address index
- Full address
- Public key
- Derivation path
- Usage status

### ✅ List All Addresses

View all generated addresses with a simple command:

```bash
python3 cli_generate_address.py --config vault_config.json --coin bitcoin --list
```

Output:
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
...
======================================================================
```

### ✅ Flexible Options

```bash
# Generate at specific index
--index 100

# Generate multiple at once
--count 10

# Specify change level (0=receive, 1=change)
--change 1

# Generate without saving to tracking file
--no-save
```

## How It Works

### Non-Hardened Derivation

The tool uses **non-hardened BIP32 derivation** from the account-level xpub:

```
Vault Config → Account xpub (m/44'/0'/0')
                    ↓ (public derivation)
              Change level (m/44'/0'/0'/0)
                    ↓ (public derivation)
           Address level (m/44'/0'/0'/0/{index})
```

### No Guardian Coordination Needed

✅ **Advantages:**
- Generate addresses instantly
- No network communication required
- No guardian private keys involved
- Works offline
- Unlimited addresses

⚠️ **Security Note:**
- Only derives **public keys** and addresses
- Cannot derive **private keys**
- Cannot **sign transactions** or spend funds
- Guardians still needed for spending

## Use Cases

### 1. Payment Processor Integration

```python
# Generate unique address for each customer
address = generate_deposit_address()
customer_invoice.address = address
```

### 2. Exchange Deposit Addresses

```python
# Generate deposit address for each user
user_address = generate_address_for_user(user_id)
```

### 3. E-commerce Checkout

```python
# Generate unique address for each order
order_address = generate_address()
```

### 4. Address Recovery

```python
# Regenerate address at specific index
old_address = generate_address(index=50)
```

## Documentation

- **`ADDRESS_GENERATION.md`** - Complete guide with examples, best practices, and integration patterns
- **`QUICK_START.md`** - Updated with address generation commands

## Command Help

```bash
python3 cli_generate_address.py --help
```

## Examples

### Basic Usage

```bash
# Generate next Bitcoin address
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin

Output:
======================================================================
GENERATING BITCOIN ADDRESS(ES)
======================================================================
Vault: Demo Vault
Network: regtest
======================================================================

Address #0:
  Path:       m/44'/0'/0'/0/0
  Address:    mkv9LaRbvVomNskd63v3UkLvY4q1dXu9tE
  Public Key: 03e6555f9a709cb3413ad96eb252e491...
  ✓ Saved to tracking file

======================================================================
✅ Generated 1 bitcoin address(es)
======================================================================
```

### Generate Multiple Addresses

```bash
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin \
    --count 5

# Generates addresses at indices 0, 1, 2, 3, 4
```

### List All Addresses

```bash
python3 cli_generate_address.py \
    --config demo_output/vault_config.json \
    --coin bitcoin \
    --list

# Shows table of all generated addresses
```

## Integration with Existing System

The address generation tool integrates seamlessly with the existing GuardianVault architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                      ADDRESS GENERATION                     │
│                     (No Guardians Needed)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Vault Config (xpub) → Generate Address → Give to Customer │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   TRANSACTION SIGNING                       │
│                    (Guardians Required)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Guardian 1 ──┐                                             │
│  Guardian 2 ──┼─→ MPC Signing Protocol → Valid Signature   │
│  Guardian 3 ──┘                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Benefits

1. **Scalability:** Generate thousands of addresses instantly
2. **Privacy:** Each transaction gets a unique address
3. **Convenience:** No guardian coordination for receiving funds
4. **Security:** Guardians only needed for spending
5. **Compliance:** Track all generated addresses for auditing
6. **BIP44 Compatible:** Standard derivation paths

## Files Added

- `cli_generate_address.py` - Main CLI tool
- `ADDRESS_GENERATION.md` - Complete documentation
- `NEW_FEATURES.md` - This file

## Files Modified

- `QUICK_START.md` - Added address generation section

## Testing

Tested and working:
- ✅ Bitcoin address generation (regtest)
- ✅ Ethereum address generation (testnet)
- ✅ Multiple address generation
- ✅ Address tracking
- ✅ List functionality
- ✅ Specific index generation

## Next Steps

This tool is ready for:
1. **Production use** - Generate deposit addresses for your vault
2. **API integration** - Build REST API around the CLI
3. **Web interface** - Create UI for address management
4. **Monitoring** - Track address usage and balances

## Summary

The address generation CLI provides a complete solution for generating and tracking deposit addresses without requiring guardian coordination. It's secure, fast, and integrates seamlessly with the existing GuardianVault MPC signature system.

**Use it to generate unlimited deposit addresses while keeping your guardians offline until you need to spend!**
