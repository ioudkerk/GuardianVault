# GuardianVault Demo Guide

Complete guide for running Bitcoin and Ethereum demos with MPC threshold signing.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Bitcoin Demo](#bitcoin-demo)
4. [Ethereum Demo](#ethereum-demo)
5. [Combined Demo](#combined-demo)
6. [Manual CLI Usage](#manual-cli-usage)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Services

1. **Coordination Server** (Port 8000)
   ```bash
   # From the root directory
   cd coordination_server
   python3 server.py
   ```

2. **Bitcoin Regtest & Ethereum Ganache** (via Docker Compose)
   ```bash
   # From the root directory
   docker compose -f docker-compose.regtest.yml up -d
   ```

   This starts:
   - Bitcoin regtest on port 18443
   - Ethereum Ganache on port 8545
   - Mempool explorer on port 8080

3. **MongoDB** (for coordination server)
   ```bash
   # Ensure MongoDB is running (usually starts automatically)
   mongod
   ```

### Verify Services

```bash
# Check Bitcoin regtest
curl -u regtest:regtest http://localhost:18443

# Check Ganache
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  http://localhost:8545

# Check coordination server
curl http://localhost:8000/health
```

## Quick Start

### 1. Setup Bitcoin Regtest
```bash
cd practical_demo
python3 setup_regtest.py
```

This creates a wallet and mines initial blocks.

### 2. Run Bitcoin Demo (Default)
```bash
python3 demo_orchestrator.py
```

Interactive mode with step-by-step prompts.

### 3. Run Ethereum Demo
```bash
python3 demo_orchestrator.py --type ethereum
```

### 4. Run Both Demos
```bash
python3 demo_orchestrator.py --type both
```

### 5. Automatic Mode (No Prompts)
```bash
python3 demo_orchestrator.py --auto --type ethereum
```

## Bitcoin Demo

### What It Does

1. **Generate Threshold Key Shares** (3-of-3)
   - Creates master key pair with BIP32 derivation
   - Splits into 3 guardian shares
   - Generates Bitcoin and Ethereum addresses

2. **Create Bitcoin Vault**
   - Registers vault in coordination server
   - Stores extended public key (xpub)
   - Links to guardian shares

3. **Invite & Register Guardians**
   - Sends 3 invitation codes
   - Guardians register with server
   - Associates guardian shares with vault

4. **Fund Bitcoin Address**
   - Uses regtest wallet to send 2.0 BTC
   - Mines block for confirmation

5. **Start Guardian Clients**
   - Launches 3 guardian processes in background
   - Connects to coordination server via WebSocket
   - Ready to participate in MPC signing

6. **Create & Sign Transaction**
   - Finds UTXO for sender address
   - Creates Bitcoin transaction (P2PKH or P2WPKH)
   - Guardians perform MPC threshold signing
   - Broadcasts to Bitcoin regtest
   - Mines block for confirmation

### Manual Bitcoin Flow

```bash
# 1. Generate shares
python3 cli_share_generator.py \
  --guardians 3 \
  --threshold 3 \
  --vault "My Bitcoin Vault" \
  --output demo_output

# 2. Create vault
python3 cli_admin.py create-vault \
  --config demo_output/vault_config.json

# 3. Invite guardian
python3 cli_admin.py invite-guardian \
  --vault-id vault_abc123 \
  --name "Alice" \
  --email "alice@example.com" \
  --role "CFO"

# 4. Register guardian
python3 cli_guardian_client.py register \
  --server http://localhost:8000 \
  --code INVITE-XXXXXXXX

# 5. Activate vault
python3 cli_admin.py activate-vault \
  --vault-id vault_abc123

# 6. Fund address
python3 cli_fund_address.py bitcoin \
  --address bcrt1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh \
  --amount 2.0

# 7. Start guardian (in separate terminals)
python3 cli_guardian_client.py run \
  --server http://localhost:8000 \
  --share demo_output/guardian_1_share.json \
  --guardian-id guard_xxx \
  --vault-id vault_abc123 \
  --vault-config demo_output/vault_config.json

# 8. Create & broadcast transaction
python3 cli_create_and_broadcast.py \
  --vault-id vault_abc123 \
  --vault-config demo_output/vault_config.json \
  --recipient bcrt1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh \
  --amount 0.5 \
  --address-index 3
```

## Ethereum Demo

### What It Does

1. **Generate Threshold Key Shares** (3-of-3)
   - Same as Bitcoin demo
   - Derives Ethereum addresses from same master key

2. **Create Ethereum Vault**
   - Registers Ethereum vault in coordination server
   - Stores Ethereum extended public key

3. **Invite & Register Guardians**
   - Creates separate guardians for Ethereum vault
   - Each guardian can manage both Bitcoin and Ethereum

4. **Fund Ethereum Address**
   - Uses Ganache pre-funded account to send 10.0 ETH
   - Transaction mines instantly on Ganache

5. **Start Guardian Clients**
   - Launches 3 guardian processes for Ethereum vault
   - Connects to coordination server

6. **Create & Sign Transaction**
   - Queries Ganache for nonce and gas prices
   - Creates EIP-1559 or legacy transaction
   - Guardians perform MPC threshold signing (ECDSA)
   - Recovers Ethereum v parameter
   - Broadcasts to Ganache
   - Verifies receipt and checks balances

### Manual Ethereum Flow

```bash
# 1-5. Same as Bitcoin (shares, vault, guardians)

# 6. Fund Ethereum address
python3 cli_fund_address.py ethereum \
  --address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb \
  --amount 10.0

# 7. Check balance
python3 cli_fund_address.py ethereum \
  --check-balance \
  --address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

# 8. Start guardian (in separate terminals)
python3 cli_guardian_client.py run \
  --server http://localhost:8000 \
  --share demo_output/guardian_1_share.json \
  --guardian-id guard_yyy \
  --vault-id vault_eth123 \
  --vault-config demo_output/vault_config.json

# 9. Create & broadcast Ethereum transaction
python3 cli_create_ethereum_transaction.py \
  --server http://localhost:8000 \
  --vault-id vault_eth123 \
  --config demo_output/vault_config.json \
  --recipient 0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199 \
  --amount 1.0 \
  --address-index 0 \
  --legacy  # Use for Ganache CLI v6
```

## Combined Demo

Runs Bitcoin demo first, then Ethereum demo:

```bash
python3 demo_orchestrator.py --type both
```

This creates:
- 1 Bitcoin vault with 3 guardians
- 1 Ethereum vault with 3 guardians
- Demonstrates MPC signing on both chains

## Manual CLI Usage

### Unified Funding CLI

The new `cli_fund_address.py` works for both Bitcoin and Ethereum:

```bash
# Bitcoin
python3 cli_fund_address.py bitcoin --address <ADDR> --amount 1.0
python3 cli_fund_address.py bitcoin --check-balance --address <ADDR>

# Ethereum
python3 cli_fund_address.py ethereum --address <ADDR> --amount 10.0
python3 cli_fund_address.py ethereum --check-balance --address <ADDR>
```

### Key Generation

```bash
# Generate 2-of-3 threshold
python3 cli_share_generator.py \
  --guardians 3 \
  --threshold 2 \
  --vault "My Vault" \
  --output my_vault

# Generate 5-of-9 threshold
python3 cli_share_generator.py \
  --guardians 9 \
  --threshold 5 \
  --vault "Enterprise Vault" \
  --output enterprise_vault
```

### Address Generation

```bash
# Generate Bitcoin addresses
python3 cli_generate_address.py \
  --coin bitcoin \
  --type p2wpkh \
  --num-addresses 10

# Generate Ethereum addresses
python3 cli_generate_address.py \
  --coin ethereum \
  --num-addresses 5
```

## Troubleshooting

### Bitcoin Regtest Issues

**Problem**: "Connection refused" on port 18443
```bash
# Check if Docker container is running
docker ps | grep bitcoin-regtest

# Restart container
docker compose -f docker-compose.regtest.yml restart bitcoin-regtest

# Check logs
docker logs guardianvault-bitcoin-regtest
```

**Problem**: "Insufficient balance" when funding
```bash
# Run setup again to mine blocks
python3 setup_regtest.py
```

### Ethereum Ganache Issues

**Problem**: "Connection refused" on port 8545
```bash
# Check if Ganache is running
docker ps | grep ganache

# Restart Ganache
docker compose -f docker-compose.regtest.yml restart ganache

# Check logs
docker logs guardianvault-ganache
```

**Problem**: "Transaction reverted" or "invalid sender"
```bash
# Check Ganache accounts
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_accounts","params":[],"id":1}' \
  http://localhost:8545
```

### Coordination Server Issues

**Problem**: "Cannot connect to server"
```bash
# Check if server is running
curl http://localhost:8000/health

# Check logs for errors
# Look at the terminal where you started the server
```

**Problem**: "MongoDB connection error"
```bash
# Check MongoDB status
mongo --eval "db.runCommand({ ping: 1 })"

# Start MongoDB
mongod
```

### Guardian Client Issues

**Problem**: "Guardian process died"
```bash
# Check the error output in the terminal
# Common issues:
# - Wrong vault ID
# - Wrong guardian ID
# - Share file not found
# - Server not accessible
```

**Problem**: "Signature timeout"
```bash
# Ensure all guardians are running
# Check that threshold is met (e.g., 3 guardians for 3-of-3)
# Verify guardians are connected to the correct vault
```

### Transaction Issues

**Problem**: "UTXO not found" (Bitcoin)
```bash
# Check address balance
python3 cli_fund_address.py bitcoin --check-balance --address <ADDR>

# Fund the address
python3 cli_fund_address.py bitcoin --address <ADDR> --amount 2.0
```

**Problem**: "Nonce too low" (Ethereum)
```bash
# Ganache automatically manages nonces
# This usually means a transaction is pending
# Wait for previous transaction to complete
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Coordination Server                       │
│                    (Port 8000)                               │
│  - Manages vaults                                            │
│  - Coordinates MPC signing rounds                            │
│  - Stores transaction requests                               │
└─────────────────────────────────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
    ┌───────────┐  ┌───────────┐  ┌───────────┐
    │ Guardian 1│  │ Guardian 2│  │ Guardian 3│
    │  (Share)  │  │  (Share)  │  │  (Share)  │
    └───────────┘  └───────────┘  └───────────┘
            │              │              │
            └──────────────┼──────────────┘
                           │
                    MPC Signing
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
    ┌──────────────┐            ┌──────────────┐
    │   Bitcoin    │            │   Ethereum   │
    │   Regtest    │            │   Ganache    │
    │ (Port 18443) │            │ (Port 8545)  │
    └──────────────┘            └──────────────┘
```

## Security Notes

⚠️ **This is a DEMO environment**

- Uses regtest and Ganache (test networks)
- Private keys are stored in JSON files
- No encryption on guardian shares
- Coordination server has no authentication
- Not suitable for production use

For production:
- Use hardware security modules (HSMs)
- Encrypt guardian shares
- Implement proper authentication/authorization
- Use secure communication channels
- Regular security audits
- Key rotation policies

## Next Steps

1. **Explore the code**: Review the CLI scripts to understand the flow
2. **Modify parameters**: Try different thresholds (2-of-3, 5-of-7, etc.)
3. **Test edge cases**: What happens if a guardian goes offline?
4. **Integrate with your app**: Use the CLI tools as reference for your application
5. **Production hardening**: Add security, monitoring, and error handling

## Support

For issues or questions:
- GitHub Issues: https://github.com/ioudkerk/GuardianVault/issues
- Review the code in `practical_demo/` directory
- Check coordination server logs for debugging
