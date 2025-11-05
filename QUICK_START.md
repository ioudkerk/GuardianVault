# GuardianVault Quick Start Guide

Complete step-by-step guide to create a vault, generate shares, and sign a transaction.

## Prerequisites

### 1. Start MongoDB
```bash
# Using Docker (easiest)
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or using Homebrew on macOS
brew install mongodb-community
brew services start mongodb-community
```

### 2. Start Coordination Server
```bash
# Terminal 1
cd coordination-server
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

Server will be available at: http://localhost:8000

## Method 1: Automated Test (Recommended for First Try)

Run the complete automated test:

```bash
# Make sure MongoDB and coordination server are running first!
python test_coordination_server.py
```

This will:
- Generate 3 guardian key shares (Alice, Bob, Charlie)
- Create a vault on the server
- Invite and register all guardians
- Create a test transaction
- Simulate all 3 guardians signing via WebSocket (4-round MPC)
- Display the final signature

## Method 2: Manual Step-by-Step

### Step 1: Generate Key Shares

```bash
# Create a simple key generation script
python3 << 'EOF'
from threshold_mpc_keymanager import ThresholdKeyManager
import json

# Generate shares for 3 guardians, 3-of-3 threshold
key_manager = ThresholdKeyManager(num_parties=3, threshold=3)
master_key = key_manager.generate_master_key()
shares = key_manager.create_shares(master_key)

# Derive Bitcoin shares
btc_shares = key_manager.derive_coin_master_key(shares, "bitcoin")

# Save each party's share
names = ["Alice", "Bob", "Charlie"]
for i, (name, share, btc_share) in enumerate(zip(names, shares, btc_shares)):
    data = {
        "party_id": i + 1,
        "name": name,
        "key_share": {
            "party_id": share.party_id,
            "share_value": share.share_value.hex(),
            "total_parties": share.total_parties,
            "threshold": share.threshold,
            "metadata": share.metadata
        },
        "master_shares": {
            "bitcoin": {
                "party_id": btc_share.party_id,
                "share_value": btc_share.share_value.hex(),
                "total_parties": btc_share.total_parties,
                "threshold": btc_share.threshold,
                "metadata": btc_share.metadata
            }
        }
    }
    with open(f"party_{i+1}_shares.json", 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved {name}'s shares to party_{i+1}_shares.json")

EOF
```

This creates: `party_1_shares.json`, `party_2_shares.json`, `party_3_shares.json`

### Step 2: Create a Vault

```bash
# Create vault via REST API
curl -X POST http://localhost:8000/api/vaults \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Test Vault",
    "coin_type": "bitcoin",
    "threshold": 3,
    "total_guardians": 3,
    "account_index": 0
  }'
```

**Response:**
```json
{
  "vault_id": "vault_abc123",
  "name": "My Test Vault",
  "coin_type": "bitcoin",
  "threshold": 3,
  "total_guardians": 3,
  "status": "pending",
  ...
}
```

Save the `vault_id` for next steps!

### Step 3: Invite Guardians

```bash
# Replace VAULT_ID with your actual vault_id from Step 2
VAULT_ID="vault_abc123"

# Invite Alice
curl -X POST http://localhost:8000/api/guardians/invite \
  -H "Content-Type: application/json" \
  -d "{
    \"vault_id\": \"$VAULT_ID\",
    \"name\": \"Alice\",
    \"email\": \"alice@example.com\"
  }"

# Invite Bob
curl -X POST http://localhost:8000/api/guardians/invite \
  -H "Content-Type: application/json" \
  -d "{
    \"vault_id\": \"$VAULT_ID\",
    \"name\": \"Bob\",
    \"email\": \"bob@example.com\"
  }"

# Invite Charlie
curl -X POST http://localhost:8000/api/guardians/invite \
  -H "Content-Type: application/json" \
  -d "{
    \"vault_id\": \"$VAULT_ID\",
    \"name\": \"Charlie\",
    \"email\": \"charlie@example.com\"
  }"
```

**Response (example):**
```json
{
  "guardian_id": "guard_xyz789",
  "vault_id": "vault_abc123",
  "name": "Alice",
  "invitation_code": "INVITE-ABC-123-XYZ",
  "status": "invited"
}
```

Save each guardian's `guardian_id` and `invitation_code`!

### Step 4: Guardians Join with Invitation Codes

```bash
# Alice joins (use her invitation code)
curl -X POST http://localhost:8000/api/guardians/join \
  -H "Content-Type: application/json" \
  -d '{
    "invitation_code": "INVITE-ABC-123-XYZ",
    "share_id": 1
  }'

# Bob joins
curl -X POST http://localhost:8000/api/guardians/join \
  -H "Content-Type: application/json" \
  -d '{
    "invitation_code": "INVITE-DEF-456-UVW",
    "share_id": 2
  }'

# Charlie joins
curl -X POST http://localhost:8000/api/guardians/join \
  -H "Content-Type: application/json" \
  -d '{
    "invitation_code": "INVITE-GHI-789-RST",
    "share_id": 3
  }'
```

### Step 5: Activate Vault

```bash
# Once all guardians have joined
curl -X POST http://localhost:8000/api/vaults/$VAULT_ID/activate
```

### Step 6: Create a Transaction

```bash
# Create a test transaction
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d "{
    \"vault_id\": \"$VAULT_ID\",
    \"type\": \"send\",
    \"coin_type\": \"bitcoin\",
    \"amount\": \"0.5\",
    \"recipient\": \"1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa\",
    \"fee\": \"0.0001\",
    \"memo\": \"Test transaction\",
    \"message_hash\": \"$(echo -n 'test message' | shasum -a 256 | cut -d' ' -f1)\"
  }"
```

**Response:**
```json
{
  "transaction_id": "tx_def456",
  "vault_id": "vault_abc123",
  "status": "pending_signatures",
  "signatures_required": 3,
  "signatures_received": 0,
  ...
}
```

Save the `transaction_id`!

### Step 7: Sign Transaction (Guardian WebSocket Client)

For this step, you need guardian clients to connect via WebSocket. You can either:

**Option A: Use the automated test script**
```bash
python test_coordination_server.py
```

**Option B: Create a guardian client script**

```python
# guardian_signer.py
import asyncio
import socketio
from threshold_signing import ThresholdSigner, KeyShare
import json
import sys

async def sign_transaction(guardian_file, vault_id, guardian_id, transaction_id, message_hash):
    # Load guardian's key share
    with open(guardian_file) as f:
        data = json.load(f)

    btc_share = data['master_shares']['bitcoin']
    key_share = KeyShare(
        party_id=btc_share['party_id'],
        share_value=bytes.fromhex(btc_share['share_value']),
        total_parties=btc_share['total_parties'],
        threshold=btc_share['threshold'],
        metadata=btc_share['metadata']
    )

    signer = ThresholdSigner([key_share])
    sio = socketio.AsyncClient()

    @sio.event
    async def connect():
        print(f"{data['name']} connected!")

        # Round 1: Generate nonce share
        nonce_share, r_point = signer.generate_nonce_share(0)

        await sio.call('signing:submit_round1', {
            'transactionId': transaction_id,
            'guardianId': guardian_id,
            'nonceShare': nonce_share.to_bytes(32, 'big').hex(),
            'rPoint': signer.point_to_hex(r_point)
        })
        print(f"{data['name']} submitted Round 1")

    @sio.on('signing:round2_ready')
    async def on_round2_ready(event_data):
        if event_data['transactionId'] == transaction_id:
            print(f"{data['name']} Round 2 ready, computing signature share...")

            # Get Round 2 data
            response = await sio.call('signing:get_round2_data', {
                'transactionId': transaction_id,
                'guardianId': guardian_id
            })

            k_total = response['data']['kTotal']
            r = response['data']['r']

            # Compute signature share
            sig_share = signer.compute_signature_share(
                share_index=0,
                message_hash=int(message_hash, 16),
                k_total=k_total,
                r=r
            )

            # Submit Round 3
            await sio.call('signing:submit_round3', {
                'transactionId': transaction_id,
                'guardianId': guardian_id,
                'signatureShare': sig_share
            })
            print(f"{data['name']} submitted Round 3")

    @sio.on('signing:complete')
    async def on_complete(event_data):
        print(f"{data['name']}: Signing complete!")
        await sio.disconnect()

    await sio.connect(
        'http://localhost:8000',
        auth={'vaultId': vault_id, 'guardianId': guardian_id},
        transports=['websocket']
    )

    await sio.wait()

# Usage: python guardian_signer.py party_1_shares.json vault_abc123 guard_xyz789 tx_def456 abc123...
if __name__ == "__main__":
    asyncio.run(sign_transaction(
        sys.argv[1],  # guardian file
        sys.argv[2],  # vault_id
        sys.argv[3],  # guardian_id
        sys.argv[4],  # transaction_id
        sys.argv[5]   # message_hash
    ))
```

Run for each guardian:
```bash
# Terminal 2 - Alice signs
python guardian_signer.py party_1_shares.json vault_abc123 guard_alice tx_def456 abc123...

# Terminal 3 - Bob signs
python guardian_signer.py party_2_shares.json vault_abc123 guard_bob tx_def456 abc123...

# Terminal 4 - Charlie signs
python guardian_signer.py party_3_shares.json vault_abc123 guard_charlie tx_def456 abc123...
```

### Step 8: Get Final Signature

```bash
# Check transaction status
curl http://localhost:8000/api/transactions/$TRANSACTION_ID

# The response will include the final signature when complete:
{
  "transaction_id": "tx_def456",
  "status": "completed",
  "final_signature": {
    "r": 12345678...,
    "s": 87654321...,
    "rHex": "00bc614e...",
    "sHex": "0537ef2a..."
  }
}
```

## Viewing API Documentation

Open your browser to: **http://localhost:8000/docs**

This shows interactive Swagger documentation for all endpoints!

## Troubleshooting

### MongoDB not running
```bash
docker ps | grep mongo
# If not running:
docker start mongodb
```

### Server connection refused
```bash
# Check server is running
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### Check server logs
The coordination server prints detailed logs showing:
- Round 1 submissions
- Round 2 automatic processing
- Round 3 submissions
- Round 4 final signature

### View MongoDB data
```bash
# Connect to MongoDB
docker exec -it mongodb mongosh

# List databases
show dbs

# Use guardianvault database
use guardianvault

# View vaults
db.vaults.find().pretty()

# View guardians
db.guardians.find().pretty()

# View transactions
db.transactions.find().pretty()
```

## Next Steps

1. **Build Guardian Desktop App** - Create a React/Electron app that uses the guardian_signer.py logic
2. **Add Authentication** - Implement JWT tokens instead of invitation codes
3. **Add Transaction Broadcasting** - Integrate with Bitcoin/Ethereum nodes to broadcast signed transactions
4. **Add Monitoring** - Build a dashboard to monitor vault activity and guardian status

## Architecture

```
┌─────────────────┐
│ Guardian App 1  │──┐
│ (Alice)         │  │
└─────────────────┘  │
                     │   WebSocket (Socket.IO)
┌─────────────────┐  │
│ Guardian App 2  │──┼──────────> ┌──────────────────────┐
│ (Bob)           │  │            │ Coordination Server  │
└─────────────────┘  │            │ (FastAPI + Socket.IO)│
                     │            └──────────────────────┘
┌─────────────────┐  │                       │
│ Guardian App 3  │──┘                       │
│ (Charlie)       │                          ▼
└─────────────────┘                  ┌──────────────┐
                                     │   MongoDB    │
                                     └──────────────┘
```

## Support

- **Coordination Server README**: `coordination-server/README.md`
- **API Documentation**: http://localhost:8000/docs
- **Guardian App Docs**: `docs/GUARDIAN_APP_IMPLEMENTATION.md`
