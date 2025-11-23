# Ethereum Implementation for GuardianVault

## Overview

This document describes the complete Ethereum support implementation for GuardianVault, enabling threshold MPC signing for Ethereum transactions. The implementation supports both modern EIP-1559 (Type 2) and legacy (Type 0) transaction formats.

## Architecture

### Key Components

1. **RLP Encoding** (`guardianvault/rlp_encoding.py`)
   - Recursive Length Prefix encoding/decoding
   - Required for Ethereum transaction serialization
   - ~210 lines

2. **Ethereum Transactions** (`guardianvault/ethereum_transaction.py`)
   - `EthereumTransaction`: EIP-1559 transactions with dynamic fees
   - `LegacyEthereumTransaction`: Type 0 transactions with single gas price
   - `EthereumTransactionBuilder`: Factory for building transactions
   - ~450 lines

3. **Ethereum RPC Client** (`guardianvault/ethereum_rpc.py`)
   - JSON-RPC client for Ethereum nodes
   - Methods: balance, nonce, fee data, transaction broadcasting
   - ~340 lines

4. **Threshold Signing Extensions** (`guardianvault/threshold_signing.py`)
   - Added `recover_ethereum_v()` method
   - Recovers v parameter (0 or 1) from ECDSA signature
   - ~80 lines added

5. **CLI Tool** (`practical_demo/cli_create_ethereum_transaction.py`)
   - Complete transaction workflow: create, sign, broadcast
   - ~415 lines

6. **Guardian Client Updates** (`practical_demo/cli_guardian_client.py`)
   - Added Ethereum account share support
   - Derives Ethereum address-level shares (m/44'/60'/0'/0/index)
   - ~60 lines added

7. **Coordination Server Updates** (`coordination-server/app/`)
   - Modified `routers/transactions.py` to support Ethereum message hashes
   - Added Ethereum-specific fields to `models/transaction.py`

## Transaction Types

### EIP-1559 Transactions (Type 2)

Modern Ethereum transactions with dynamic fee market:

```python
tx = EthereumTransactionBuilder.build_transfer_transaction(
    sender_address="0x...",
    recipient_address="0x...",
    amount_eth=0.1,
    nonce=0,
    chain_id=1,
    max_priority_fee_gwei=2.0,  # Tip to miners
    max_fee_gwei=20.0,           # Maximum total fee
    gas_limit=21000,
    legacy=False  # EIP-1559
)
```

**RLP Structure:**
```
0x02 || rlp([chain_id, nonce, max_priority_fee, max_fee, gas_limit, to, value, data, access_list, v, r, s])
```

### Legacy Transactions (Type 0)

Original Ethereum transaction format with EIP-155 replay protection:

```python
tx = EthereumTransactionBuilder.build_transfer_transaction(
    sender_address="0x...",
    recipient_address="0x...",
    amount_eth=0.1,
    nonce=0,
    chain_id=1337,
    max_fee_gwei=2.0,  # Used as gas_price
    gas_limit=21000,
    legacy=True  # Legacy Type 0
)
```

**RLP Structure:**
```
rlp([nonce, gas_price, gas_limit, to, value, data, v, r, s])
```

**EIP-155 Replay Protection:**
- Signing: Include `[chain_id, 0, 0]` in signing hash
- Final v value: `v = chain_id * 2 + 35 + recovery_id`

## Usage

### 1. Generate Ethereum Addresses

```bash
python cli_generate_ethereum_addresses.py \
  --config clovr_output/vault_config.json \
  --num-addresses 5
```

### 2. Fund Address

Transfer ETH to the generated address using your Ethereum wallet or test faucet.

For local testing with Ganache:
```bash
python fund_ethereum_address.py \
  --recipient 0x370d8606D865F830478C139C9BF8aAC7171e8e0F \
  --amount 10.0 \
  --rpc-port 8545
```

### 3. Start Guardian Clients

Start 3 guardian clients in separate terminals:

```bash
# Terminal 1
./start_guardians.sh 1

# Terminal 2
./start_guardians.sh 2

# Terminal 3
./start_guardians.sh 3
```

### 4. Create and Broadcast Transaction

**For modern networks (Hardhat, Geth, etc.):**
```bash
python cli_create_ethereum_transaction.py \
  --vault-id vault_hHnn9VMkv7TX \
  --config clovr_output/vault_config.json \
  --recipient 0xF972d2FC6714fCaF41D5D0008A320fC0f8F00FC8 \
  --amount 0.1 \
  --memo "MPC transaction"
```

**For Ganache CLI v6 (requires legacy transactions):**
```bash
python cli_create_ethereum_transaction.py \
  --vault-id vault_hHnn9VMkv7TX \
  --config clovr_output/vault_config.json \
  --recipient 0xF972d2FC6714fCaF41D5D0008A320fC0f8F00FC8 \
  --amount 0.1 \
  --memo "MPC transaction" \
  --legacy
```

## Implementation Details

### Address Derivation

Ethereum addresses follow BIP44 path: `m/44'/60'/0'/0/index`

```python
# Account level (shared among guardians)
account_path = "m/44'/60'/0'"

# Address level (per transaction)
address_path = f"m/44'/60'/0'/0/{index}"
```

### Signature Process

1. **Build Transaction**: Create transaction object with all parameters
2. **Compute Signing Hash**:
   - EIP-1559: `keccak256(0x02 || rlp([chain_id, nonce, ...]))`
   - Legacy: `keccak256(rlp([nonce, gas_price, ..., chain_id, 0, 0]))`
3. **MPC Signing**: 4-round threshold ECDSA protocol produces (r, s)
4. **Recover v**: Try both v=0 and v=1, verify against public key
5. **Set Signature**: Apply correct v value
   - EIP-1559: v ∈ {0, 1}
   - Legacy: v = chain_id * 2 + 35 + recovery_id
6. **Serialize**: RLP encode with signature
7. **Broadcast**: Send to Ethereum node via RPC

### V-Parameter Recovery

The v parameter allows public key recovery from signature. Algorithm:

```python
def recover_ethereum_v(public_key: bytes, message_hash: bytes, signature: ThresholdSignature) -> int:
    """Try both v=0 and v=1, return the one that recovers correct public key"""
    for v in [0, 1]:
        # Reconstruct R point from r coordinate
        R = Point(r, y_from_x(r, v))

        # Recover public key: Q = r^(-1) * (s*R - z*G)
        Q = (R * s - G * z) * r_inv

        if Q matches expected public key:
            return v

    raise Exception("Could not recover v parameter")
```

## Testing

### Unit Tests

Run the comprehensive test suite:

```bash
cd practical_demo
python test_ethereum_implementation.py
```

Tests cover:
- RLP encoding/decoding
- Transaction building (EIP-1559 and Legacy)
- Signing hash computation
- V-parameter recovery
- Full MPC signing workflow

### Local Testing Setup

**Option 1: Ganache CLI v6 (Legacy transactions only)**
```bash
ganache-cli --port 8545 --networkId 1337
```

**Option 2: Hardhat (EIP-1559 support)**
```bash
npx hardhat node
```

## Compatibility

### Network Compatibility

| Network | EIP-1559 | Legacy | Notes |
|---------|----------|--------|-------|
| Ethereum Mainnet | ✅ | ✅ | EIP-1559 since London fork |
| Polygon | ✅ | ✅ | EIP-1559 since London fork |
| BSC | ❌ | ✅ | Use --legacy flag |
| Avalanche C-Chain | ✅ | ✅ | Full support |
| Arbitrum | ✅ | ✅ | Full support |
| Optimism | ✅ | ✅ | Full support |
| Ganache CLI v6 | ❌ | ✅ | Use --legacy flag |
| Hardhat | ✅ | ✅ | Full support |
| Geth | ✅ | ✅ | Full support |

### Transaction Type Selection

Use `--legacy` flag when:
- Network doesn't support EIP-1559
- Testing with Ganache CLI v6.x
- Network explicitly requires Type 0 transactions

Use EIP-1559 (default) when:
- Network supports EIP-1559
- Want to optimize gas fees with dynamic pricing
- Testing with Hardhat or modern nodes

## Key Differences from Bitcoin

| Aspect | Bitcoin | Ethereum |
|--------|---------|----------|
| **Model** | UTXO-based | Account-based |
| **Encoding** | DER/ASN.1 | RLP |
| **Hashing** | SHA256 (double) | Keccak256 |
| **Address** | Base58Check/Bech32 | Hex with 0x prefix |
| **Fees** | sat/vB | Gwei (gas price × gas used) |
| **Nonce** | N/A | Sequential per account |
| **Signature Format** | DER-encoded | (v, r, s) tuple |
| **BIP44 Path** | m/44'/0'/0'/0/index | m/44'/60'/0'/0/index |

## Security Considerations

1. **Replay Protection**:
   - EIP-1559: chain_id embedded in transaction
   - Legacy: EIP-155 formula (v = chain_id * 2 + 35 + recovery_id)

2. **Nonce Management**:
   - Must be sequential per account
   - Gap in nonces blocks subsequent transactions
   - Fetched from RPC before each transaction

3. **Gas Estimation**:
   - Simple transfers: 21,000 gas
   - Contract calls: Estimate via `eth_estimateGas`
   - Set gas limit 10-20% above estimate

4. **Fee Market**:
   - EIP-1559: Set reasonable max_fee to avoid overpaying
   - Legacy: Monitor gas price, may need to increase for stuck transactions

5. **Public Key Compression**:
   - Ethereum uses uncompressed public keys internally
   - Keccak256(uncompressed_pubkey)[12:] = address

## Troubleshooting

### "invalid remainder" Error
- **Cause**: Ganache CLI v6 doesn't support EIP-1559
- **Solution**: Add `--legacy` flag

### "nonce too low" Error
- **Cause**: Nonce already used
- **Solution**: Wait for pending transaction or use next nonce

### "insufficient funds" Error
- **Cause**: Account balance < amount + gas
- **Solution**: Fund account with more ETH

### "invalid signature" Error
- **Cause**: Wrong v parameter or signature verification failed
- **Solution**: Check public key derivation and message hash

## Files Modified/Created

### New Files
- `guardianvault/rlp_encoding.py`
- `guardianvault/ethereum_transaction.py`
- `guardianvault/ethereum_rpc.py`
- `practical_demo/cli_create_ethereum_transaction.py`
- `practical_demo/cli_generate_ethereum_addresses.py`
- `practical_demo/test_ethereum_implementation.py`
- `practical_demo/fund_ethereum_address.py`

### Modified Files
- `guardianvault/threshold_signing.py` (+80 lines)
- `practical_demo/cli_guardian_client.py` (+60 lines)
- `coordination-server/app/routers/transactions.py`
- `coordination-server/app/models/transaction.py`

## Total Implementation

- **Lines Added**: ~2,200 lines
- **New Modules**: 7
- **Modified Modules**: 4
- **Test Coverage**: Comprehensive unit and integration tests

## Future Enhancements

Potential improvements:
1. EIP-712 typed data signing
2. Contract interaction support
3. Multi-token support (ERC-20, ERC-721)
4. Gas estimation improvements
5. Transaction batching
6. MEV protection
7. Layer 2 optimizations

## References

- [EIP-1559: Fee Market](https://eips.ethereum.org/EIPS/eip-1559)
- [EIP-155: Replay Protection](https://eips.ethereum.org/EIPS/eip-155)
- [EIP-2718: Typed Transaction Envelope](https://eips.ethereum.org/EIPS/eip-2718)
- [RLP Encoding Specification](https://ethereum.org/en/developers/docs/data-structures-and-encoding/rlp/)
- [Ethereum Yellow Paper](https://ethereum.github.io/yellowpaper/paper.pdf)
