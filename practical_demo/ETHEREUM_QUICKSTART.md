# Ethereum Transaction Quick Start Guide

## Prerequisites

1. **Coordination Server Running**
   ```bash
   cd coordination-server
   uvicorn app.main:app --reload
   ```

2. **Ethereum Node Running**

   For Ganache CLI v6 (legacy transactions):
   ```bash
   ganache-cli --port 8545 --networkId 1337
   ```

   Or for Hardhat (EIP-1559 support):
   ```bash
   npx hardhat node
   ```

3. **Vault Created**
   ```bash
   python cli_create_vault.py --threshold 3 --total 3 --name "My Ethereum Vault"
   ```
   This creates `clovr_output/vault_config.json` and share files.

## Step-by-Step Instructions

### 1. Generate Ethereum Addresses

```bash
python cli_generate_ethereum_addresses.py \
  --config clovr_output/vault_config.json \
  --num-addresses 5
```

This creates `ethereum_addresses.json` with your addresses.

### 2. Fund an Address

**Option A: Using fund_ethereum_address.py (for local testing)**
```bash
python fund_ethereum_address.py \
  --recipient 0x370d8606D865F830478C139C9BF8aAC7171e8e0F \
  --amount 10.0 \
  --rpc-port 8545
```

**Option B: Send from your wallet**
Send ETH to the generated address using MetaMask or another wallet.

### 3. Start Guardian Clients

Open **3 separate terminals** and run:

**Terminal 1:**
```bash
cd practical_demo
./start_guardians.sh 1
```

**Terminal 2:**
```bash
cd practical_demo
./start_guardians.sh 2
```

**Terminal 3:**
```bash
cd practical_demo
./start_guardians.sh 3
```

Wait until all guardians show "Connected to server" and "Ready to sign transactions".

### 4. Create and Broadcast Transaction

**For Hardhat/Modern Networks (EIP-1559):**
```bash
python cli_create_ethereum_transaction.py \
  --vault-id vault_hHnn9VMkv7TX \
  --config clovr_output/vault_config.json \
  --recipient 0xF972d2FC6714fCaF41D5D0008A320fC0f8F00FC8 \
  --amount 0.1 \
  --memo "My first MPC transaction"
```

**For Ganache CLI v6 (Legacy):**
```bash
python cli_create_ethereum_transaction.py \
  --vault-id vault_hHnn9VMkv7TX \
  --config clovr_output/vault_config.json \
  --recipient 0xF972d2FC6714fCaF41D5D0008A320fC0f8F00FC8 \
  --amount 0.1 \
  --memo "My first MPC transaction" \
  --legacy
```

## Command Reference

### cli_create_ethereum_transaction.py

```bash
python cli_create_ethereum_transaction.py \
  --vault-id <VAULT_ID> \
  --config <CONFIG_PATH> \
  --recipient <ETH_ADDRESS> \
  --amount <ETH_AMOUNT> \
  [OPTIONS]
```

**Required Arguments:**
- `--vault-id`: Vault identifier
- `--config`: Path to vault_config.json
- `--recipient`: Recipient Ethereum address (0x...)
- `--amount`: Amount in ETH (e.g., 0.1)

**Optional Arguments:**
- `--server`: Coordination server URL (default: http://localhost:8000)
- `--address-index`: Address derivation index (default: 0)
- `--memo`: Transaction memo/description
- `--rpc-host`: Ethereum RPC host (default: localhost)
- `--rpc-port`: Ethereum RPC port (default: 8545)
- `--chain-id`: Network chain ID (auto-detected if not specified)
- `--max-priority-fee`: Max priority fee in Gwei (auto if not specified)
- `--max-fee`: Max fee per gas in Gwei (auto if not specified)
- `--gas-limit`: Gas limit (default: 21000)
- `--legacy`: Use legacy Type 0 transactions (for Ganache CLI v6)

### cli_generate_ethereum_addresses.py

```bash
python cli_generate_ethereum_addresses.py \
  --config <CONFIG_PATH> \
  --num-addresses <COUNT>
```

**Arguments:**
- `--config`: Path to vault_config.json
- `--num-addresses`: Number of addresses to generate (default: 5)
- `--change`: Change index (0=external, 1=internal, default: 0)

### fund_ethereum_address.py

```bash
python fund_ethereum_address.py \
  --recipient <ETH_ADDRESS> \
  --amount <ETH_AMOUNT> \
  [OPTIONS]
```

**Arguments:**
- `--recipient`: Recipient Ethereum address
- `--amount`: Amount in ETH
- `--rpc-host`: Ethereum RPC host (default: localhost)
- `--rpc-port`: Ethereum RPC port (default: 8545)
- `--sender-index`: Ganache account index to send from (default: 0)

## Transaction Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User creates transaction request                        │
│    - Specifies recipient, amount, fees                     │
│    - Computes Keccak256 signing hash                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Coordination Server receives request                    │
│    - Creates transaction record                            │
│    - Stores message hash for signing                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Guardian Clients participate in MPC                     │
│    - Derive address-level key shares                       │
│    - Run 4-round threshold ECDSA protocol                  │
│    - Produce signature (r, s)                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. User recovers v parameter                               │
│    - Tries v=0 and v=1                                     │
│    - Verifies against expected public key                  │
│    - Applies correct v to transaction                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. User serializes and broadcasts                          │
│    - RLP encodes transaction with signature                │
│    - Sends via eth_sendRawTransaction                      │
│    - Waits for transaction to be mined                     │
└─────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Guardians not signing

**Symptom:** Transaction stays in "pending" status

**Solutions:**
1. Check all 3 guardians are connected
2. Verify guardians loaded correct share files
3. Check coordinator server logs for errors
4. Ensure guardians have Ethereum account shares

### "invalid remainder" error

**Symptom:** Transaction fails to broadcast to Ganache

**Solution:** Add `--legacy` flag for Ganache CLI v6

### "insufficient funds" error

**Symptom:** Balance check fails

**Solution:** Fund the address with more ETH

### "nonce too low" error

**Symptom:** Transaction rejected by node

**Solution:** Transaction with this nonce already used, wait or use next nonce

## Network Configuration

### Ethereum Mainnet
```bash
--rpc-host mainnet.infura.io \
--rpc-port 443 \
--chain-id 1
```

### Polygon
```bash
--rpc-host polygon-rpc.com \
--rpc-port 443 \
--chain-id 137
```

### Arbitrum
```bash
--rpc-host arb1.arbitrum.io \
--rpc-port 443 \
--chain-id 42161
```

### BSC (Binance Smart Chain)
```bash
--rpc-host bsc-dataseed.binance.org \
--rpc-port 443 \
--chain-id 56 \
--legacy  # BSC doesn't support EIP-1559
```

## Example Output

```
======================================================================
Ethereum Transaction Flow (EIP-1559/Type 2)
======================================================================

Step 1: Loading vault configuration...
✓ Sender address: 0x370d8606D865F830478C139C9BF8aAC7171e8e0F (index 0)
  Public key: 034d8762a7db479a139315c61b5b653cdcb7e2e0824ab8b3c7051d6d5dff82208a

Step 2: Querying Ethereum node...
✓ Chain ID: 1337
✓ Current nonce: 0
✓ Balance: 11.000000 ETH
  ✓ Max priority fee: 2.00 Gwei (from node)
  ✓ Max fee per gas: 2.00 Gwei (from node)

Step 3: Building EIP-1559 transaction...
✓ Transaction created
  To: 0xF972d2FC6714fCaF41D5D0008A320fC0f8F00FC8
  Amount: 0.1 ETH
  Nonce: 0
  Gas limit: 21000
  Max priority fee: 2.00 Gwei
  Max fee: 2.00 Gwei

Step 4: Requesting MPC signature from coordination server...
✓ Transaction created: tx_4dLDfkxvshuy
  Guardians will now sign...

Step 5: Waiting for MPC signing...
✓ Transaction signed!

Step 6: Verifying signature...
✓ Signature verified

Step 7: Broadcasting to Ethereum network...
✓ Transaction broadcast successful!
  Transaction hash: 0x...

✓ Transaction mined!
  Block number: 12345
  Gas used: 21000
  Status: Success

======================================================================
✓ Ethereum transaction flow completed successfully!
======================================================================
```

## Files and Directories

```
GuardianVault/
├── guardianvault/
│   ├── rlp_encoding.py              # RLP encoder/decoder
│   ├── ethereum_transaction.py      # Transaction builders
│   ├── ethereum_rpc.py              # RPC client
│   └── threshold_signing.py         # MPC signing (updated)
├── practical_demo/
│   ├── cli_create_ethereum_transaction.py   # Main CLI tool
│   ├── cli_generate_ethereum_addresses.py   # Address generator
│   ├── fund_ethereum_address.py             # Funding utility
│   ├── test_ethereum_implementation.py      # Test suite
│   └── start_guardians.sh                   # Helper script
└── docs/
    └── ETHEREUM_IMPLEMENTATION.md   # Complete documentation
```

## Next Steps

1. Test with different transaction amounts
2. Try different recipient addresses
3. Experiment with custom gas settings
4. Test on different networks (testnet before mainnet!)
5. Implement contract interactions (future enhancement)

## Support

For issues or questions:
1. Check logs in coordination server terminal
2. Check guardian client terminals for errors
3. Verify Ethereum node is running and accessible
4. Review full documentation in `docs/ETHEREUM_IMPLEMENTATION.md`
