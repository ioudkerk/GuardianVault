# GuardianVault Demo Cheatsheet

Quick reference for running demos with clients.

## Pre-Demo Setup (5 minutes)

```bash
# 1. Start Bitcoin Regtest
cd GuardianVault
docker compose -f docker-compose.regtest.yml up -d

# 2. Start Coordination Server (separate terminal)
cd coordination-server
./run_server.sh
# OR: poetry run uvicorn app.main:socket_app --reload
# IMPORTANT: Use socket_app (not app) for WebSocket support!

# 3. Prepare Demo Directory
cd ../practical_demo
pip3 install -r requirements.txt

# 4. Setup Bitcoin Regtest (IMPORTANT - run once)
python3 setup_regtest.py
```

## Quick Demo Script (10 minutes)

### Part 1: Setup (2 minutes)

```bash
# Generate 3 key shares
python3 cli_share_generator.py -g 3 -t 3 -v "Client Demo" -o demo_shares

# Create vaults
python3 cli_admin.py create-vault -c demo_shares/vault_config.json
# Copy the Bitcoin vault_id: ________________
```

### Part 2: Guardian Management (3 minutes)

```bash
# Invite 3 guardians
python3 cli_admin.py invite-guardian --vault-id <VAULT_ID> -n Alice -e alice@demo.com -r CFO
# Copy invitation code 1: ________________

python3 cli_admin.py invite-guardian --vault-id <VAULT_ID> -n Bob -e bob@demo.com -r CTO
# Copy invitation code 2: ________________

python3 cli_admin.py invite-guardian --vault-id <VAULT_ID> -n Charlie -e charlie@demo.com -r CEO
# Copy invitation code 3: ________________

# Register guardians
python3 cli_guardian_client.py register -s http://localhost:8000 -c <CODE_1>
# Copy guardian_id 1: ________________

python3 cli_guardian_client.py register -s http://localhost:8000 -c <CODE_2>
# Copy guardian_id 2: ________________

python3 cli_guardian_client.py register -s http://localhost:8000 -c <CODE_3>
# Copy guardian_id 3: ________________

# Activate vault
python3 cli_admin.py activate-vault --vault-id <VAULT_ID>
```

### Part 3: Bitcoin Transaction Demo (5 minutes)

```bash
# Get Bitcoin address from config
cat demo_shares/vault_config.json | grep -A 5 "sample_addresses"
# Copy first address: ________________

# Fund address
python3 cli_transaction_requester.py fund-address -a <ADDRESS> --amount 2.0

# Check balance
python3 cli_transaction_requester.py check-balance -a <ADDRESS>
```

**Open 3 new terminals and start guardian clients:**

Terminal 1:
```bash
cd practical_demo
python3 cli_guardian_client.py run -s http://localhost:8000 \
  --share demo_shares/guardian_1_share.json \
  --guardian-id <GUARDIAN_ID_1> \
  --vault-id <VAULT_ID>
```

Terminal 2:
```bash
cd practical_demo
python3 cli_guardian_client.py run -s http://localhost:8000 \
  --share demo_shares/guardian_2_share.json \
  --guardian-id <GUARDIAN_ID_2> \
  --vault-id <VAULT_ID>
```

Terminal 3:
```bash
cd practical_demo
python3 cli_guardian_client.py run -s http://localhost:8000 \
  --share demo_shares/guardian_3_share.json \
  --guardian-id <GUARDIAN_ID_3> \
  --vault-id <VAULT_ID>
```

**Back in main terminal:**
```bash
# Create transaction
python3 cli_transaction_requester.py create-transaction \
  --vault-id <VAULT_ID> \
  -r bcrt1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh \
  -a 0.5 -f 0.0001 -m "Demo transaction"

# Copy transaction_id: ________________

# Watch guardians automatically sign! (check their terminals)

# Wait for completion
python3 cli_transaction_requester.py wait-for-signature -t <TRANSACTION_ID>
```

## Key Talking Points for Clients

### Security Benefits
✓ "Private keys are NEVER reconstructed - not even during signing"
✓ "Requires 3 guardians to approve every transaction"
✓ "Each guardian only holds 1/3 of the key - useless alone"
✓ "Unlimited addresses without guardian interaction"

### Operational Benefits
✓ "Real-time coordination through WebSocket"
✓ "Support for Bitcoin and Ethereum (and more)"
✓ "BIP32 hierarchical derivation for compliance"
✓ "Fully auditable transaction history"

### Technical Highlights
✓ "4-round threshold ECDSA protocol"
✓ "Production-ready coordination server"
✓ "Desktop app for guardians (GUI)"
✓ "Tested with Bitcoin regtest integration"

## Common Demo Scenarios

### Scenario 1: Treasury Management
"Company treasury requires 3 executives (CFO, CTO, CEO) to approve payments"

### Scenario 2: Custody Service
"Crypto custody provider with distributed security across geographic locations"

### Scenario 3: DAO Treasury
"Decentralized organization requiring multi-sig for fund management"

## Troubleshooting

### Bitcoin regtest not responding
```bash
docker compose -f ../docker-compose.regtest.yml restart
docker compose -f ../docker-compose.regtest.yml logs -f bitcoin-regtest
```

### Coordination server error
```bash
# Check logs in coordination-server terminal
# Verify MongoDB is running
```

### Guardians not connecting
```bash
# Verify all IDs are correct
# Check vault is ACTIVE status
python3 cli_admin.py get-vault --vault-id <VAULT_ID>
```

### Transaction not signing
- Ensure all 3 guardian clients are running
- Check guardian terminals for errors
- Verify transaction was created successfully

## Demo Cleanup

```bash
# Stop guardian clients (Ctrl+C in each terminal)

# Stop services
docker compose -f ../docker-compose.regtest.yml down

# Remove demo data
rm -rf demo_shares/
```

## Quick Commands Reference

```bash
# List all vaults
python3 cli_admin.py list-vaults

# List all guardians for a vault
python3 cli_admin.py list-guardians --vault-id <VAULT_ID>

# Get vault statistics
python3 cli_admin.py vault-stats --vault-id <VAULT_ID>

# List all transactions
python3 cli_transaction_requester.py list-transactions --vault-id <VAULT_ID>

# Check specific transaction
python3 cli_transaction_requester.py wait-for-signature -t <TX_ID> --timeout 30
```

## Automated Demo

For a fully automated walkthrough:

```bash
python3 demo_orchestrator.py
```

This will guide you through each step with explanations.
