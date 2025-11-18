# GuardianVault Practical Demo

Complete end-to-end demonstration of the GuardianVault threshold MPC wallet system.

## Overview

This demo shows the complete GuardianVault workflow:
1. **Key Generation**: Create threshold key shares (3-of-3)
2. **Vault Creation**: Set up vaults in coordination server
3. **Guardian Management**: Invite and register guardians
4. **Funding**: Fund Bitcoin addresses from regtest
5. **MPC Signing**: Create and sign transactions using threshold signatures
6. **Broadcasting**: Send signed transactions to Bitcoin network

## Prerequisites

Before running the demo, ensure you have:

### 1. Coordination Server Running

```bash
cd coordination-server
./run_server.sh
```

Server should be accessible at `http://localhost:8000`

### 2. Bitcoin Regtest Running

```bash
bitcoind -regtest -daemon \
  -rpcuser=regtest \
  -rpcpassword=regtest \
  -rpcport=18443 \
  -fallbackfee=0.00001
```

Create a wallet:
```bash
bitcoin-cli -regtest -rpcuser=regtest -rpcpassword=regtest \
  createwallet regtest_wallet
```

### 3. MongoDB Running

```bash
mongod --dbpath /path/to/db
```

## Quick Start

### Option 1: Automated Demo (Recommended)

Run the complete workflow automatically without prompts:

```bash
cd practical_demo
python3 demo_orchestrator.py --auto
```

This will:
- ✅ Check prerequisites
- ✅ Generate shares
- ✅ Create vault
- ✅ Invite & register guardians
- ✅ Fund addresses
- ✅ Start guardian clients in background
- ✅ Create, sign, and broadcast transaction
- ✅ Cleanup guardian processes

Expected output:
```
======================================================================
  GuardianVault Complete Demo
======================================================================

This demo will demonstrate:
  1. Generating threshold key shares (3-of-3)
  2. Creating a Bitcoin vault
  3. Inviting and registering guardians
  4. Funding a Bitcoin address from regtest
  5. Running guardian clients
  6. Creating and signing a transaction with MPC
  7. Broadcasting to Bitcoin regtest network

...

======================================================================
  Demo Completed Successfully!
======================================================================

✅ Vault created: vault_abc123
✅ Guardians invited and registered: 3
✅ Bitcoin address funded: bcrt1q...
✅ Transaction signed with MPC: <txid>
✅ Transaction broadcast to Bitcoin regtest
```

### Option 2: Interactive Demo

Run with prompts at each step (useful for learning):

```bash
python3 demo_orchestrator.py
```

Press Enter at each step to proceed.

## Manual Workflow

If you prefer to run each step manually:

### Step 1: Generate Shares

```bash
python3 cli_share_generator.py \
  --guardians 3 \
  --threshold 3 \
  --vault "Demo Vault" \
  --output demo_output
```

### Step 2: Create Vault

```bash
python3 cli_admin.py create-vault \
  --config demo_output/vault_config.json
```

Note the Bitcoin vault ID from the output.

### Step 3: Invite Guardians

```bash
python3 cli_admin.py invite-guardian \
  --vault-id <VAULT_ID> \
  --name "Alice" \
  --email "alice@demo.com" \
  --role "CFO"

# Repeat for Bob and Charlie
```

### Step 4: Register Guardians

```bash
python3 cli_guardian_client.py register \
  --server http://localhost:8000 \
  --code <INVITATION_CODE>

# Repeat for each guardian
```

### Step 5: Activate Vault

```bash
python3 cli_admin.py activate-vault \
  --vault-id <VAULT_ID>
```

### Step 6: Fund Address

```bash
python3 cli_transaction_requester.py fund-address \
  --address <BTC_ADDRESS> \
  --amount 2.0
```

### Step 7: Start Guardian Clients (in separate terminals)

Terminal 1:
```bash
python3 cli_guardian_client.py run \
  --share demo_output/guardian_1_share.json \
  --guardian-id <GUARDIAN_1_ID> \
  --vault-id <VAULT_ID> \
  --vault-config demo_output/vault_config.json
```

Terminal 2:
```bash
python3 cli_guardian_client.py run \
  --share demo_output/guardian_2_share.json \
  --guardian-id <GUARDIAN_2_ID> \
  --vault-id <VAULT_ID> \
  --vault-config demo_output/vault_config.json
```

Terminal 3:
```bash
python3 cli_guardian_client.py run \
  --share demo_output/guardian_3_share.json \
  --guardian-id <GUARDIAN_3_ID> \
  --vault-id <VAULT_ID> \
  --vault-config demo_output/vault_config.json
```

### Step 8: Create and Broadcast Transaction

```bash
python3 cli_create_and_broadcast.py \
  --vault-id <VAULT_ID> \
  --vault-config demo_output/vault_config.json \
  --recipient bcrt1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh \
  --amount 0.5 \
  --fee 0.0001 \
  --address-index 0 \
  --memo "Demo transaction"
```

## Available CLI Scripts

### Admin Tools

- **`cli_admin.py`** - Vault and guardian management
  - `create-vault` - Create new vault
  - `invite-guardian` - Invite guardian to vault
  - `activate-vault` - Activate vault for use
  - `list-vaults` - List all vaults
  - `list-guardians` - List guardians in vault

### Share Generation

- **`cli_share_generator.py`** - Generate threshold key shares
  - Creates key shares for all guardians
  - Generates Bitcoin and Ethereum addresses
  - Saves share files and vault config

### Guardian Client

- **`cli_guardian_client.py`** - Guardian participation
  - `register` - Register with invitation code
  - `run` - Run guardian client (auto-signs transactions)

### Transaction Management

- **`cli_transaction_requester.py`** - Transaction operations
  - `fund-address` - Fund address from regtest
  - `check-balance` - Check address balance
  - `create-transaction` - Create transaction request
  - `wait-for-signature` - Wait for signing to complete

- **`cli_create_and_broadcast.py`** - Complete transaction flow
  - Creates transaction with proper UTXO
  - Waits for MPC signing
  - Broadcasts to Bitcoin network

- **`cli_broadcast_transaction.py`** - Broadcast pre-signed transaction

### Debugging

- **`debug_signature.py`** - Diagnostic tool for signature issues
  - Verifies address derivation
  - Checks ECDSA signature
  - Validates sighash
  - Identifies exact failure point

## Troubleshooting

### Transaction Broadcast Fails

If the transaction is signed but broadcast fails, run the diagnostic:

```bash
python3 debug_signature.py \
  --transaction-id <TX_ID> \
  --vault-config demo_output/vault_config.json
```

This will show:
- ✅/❌ Address derivation match
- ✅/❌ ECDSA signature validity
- ✅/❌ Bitcoin sighash match
- Detailed error information

### Common Issues

**Issue**: "Coordination server is NOT running"
```bash
# Solution: Start the server
cd coordination-server
./run_server.sh
```

**Issue**: "Bitcoin regtest is NOT running"
```bash
# Solution: Start Bitcoin regtest
bitcoind -regtest -daemon \
  -rpcuser=regtest \
  -rpcpassword=regtest \
  -rpcport=18443
```

**Issue**: "Guardian process died"
```bash
# Solution: Check guardian client logs
# Usually means invalid guardian ID or vault ID
# Make sure to use the IDs returned from registration
```

**Issue**: "Signature verification failed"
```bash
# Solution: Run diagnostic
python3 debug_signature.py \
  --transaction-id <TX_ID> \
  --vault-config demo_output/vault_config.json

# Check SIGNATURE_DEBUG_GUIDE.md for detailed troubleshooting
```

**Issue**: "UTXO not found"
```bash
# Solution: Make sure address is funded
python3 cli_transaction_requester.py fund-address \
  --address <ADDRESS> \
  --amount 2.0

# Verify balance
python3 cli_transaction_requester.py check-balance \
  --address <ADDRESS>
```

## Demo Output

The demo creates a `demo_output/` directory with:

```
demo_output/
├── vault_config.json          # Vault configuration (safe to share)
├── guardian_1_share.json      # Guardian 1's private share (KEEP SECRET)
├── guardian_2_share.json      # Guardian 2's private share (KEEP SECRET)
└── guardian_3_share.json      # Guardian 3's private share (KEEP SECRET)
```

**⚠️ IMPORTANT**: Share files contain private key shares. In production:
- Never store all shares on one machine
- Distribute to different guardians
- Use secure storage (HSM, encrypted drives, etc.)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Coordination Server                      │
│  • Vault Management                                        │
│  • Guardian Registration                                   │
│  • MPC Protocol Coordination                               │
│  • Transaction Status Tracking                             │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │ WebSocket/HTTP
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Guardian 1  │  │  Guardian 2  │  │  Guardian 3  │
│  (Alice)     │  │  (Bob)       │  │  (Charlie)   │
│              │  │              │  │              │
│  • Share 1   │  │  • Share 2   │  │  • Share 3   │
│  • Round 1   │  │  • Round 1   │  │  • Round 1   │
│  • Round 3   │  │  • Round 3   │  │  • Round 3   │
└──────────────┘  └──────────────┘  └──────────────┘
```

## MPC Signing Protocol

The demo demonstrates a 4-round threshold ECDSA signing protocol:

**Round 1**: Each guardian generates a random nonce share and R point
```
Guardian 1: k₁, R₁ = k₁ · G
Guardian 2: k₂, R₂ = k₂ · G
Guardian 3: k₃, R₃ = k₃ · G
```

**Round 2**: Server combines R points
```
R = R₁ + R₂ + R₃
r = R.x mod n
k_total = k₁ + k₂ + k₃ mod n
```

**Round 3**: Each guardian computes signature share
```
s₁ = k⁻¹ · (z/n + r·x₁) mod n
s₂ = k⁻¹ · (z/n + r·x₂) mod n
s₃ = k⁻¹ · (z/n + r·x₃) mod n
```

**Round 4**: Server combines signature shares
```
s = s₁ + s₂ + s₃ mod n
Final signature: (r, s)
```

✅ **Private keys NEVER reconstructed**
✅ **Each party only uses their share**
✅ **Standard ECDSA signature output**

## Security Considerations

This is a **DEMO** implementation. For production:

1. **Key Storage**: Use HSMs or secure enclaves
2. **Communication**: TLS + mutual authentication
3. **Access Control**: Multi-factor authentication
4. **Key Rotation**: Implement share refresh
5. **Monitoring**: Log all operations
6. **Backup**: Encrypted share backups
7. **Testing**: Security audits and penetration testing

## Further Reading

- [SIGNATURE_DEBUG_GUIDE.md](../SIGNATURE_DEBUG_GUIDE.md) - Troubleshooting guide
- [GuardianVault Documentation](../README.md) - Full system documentation
- [Threshold ECDSA](https://eprint.iacr.org/2019/114.pdf) - Academic paper

## Support

For issues or questions:
1. Run the diagnostic tool: `debug_signature.py`
2. Check the debug guide: `SIGNATURE_DEBUG_GUIDE.md`
3. Review logs in `coordination-server/logs/`
4. Check Bitcoin regtest logs

## License

See parent directory LICENSE file.
