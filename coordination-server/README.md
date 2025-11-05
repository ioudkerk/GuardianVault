# GuardianVault Coordination Server

**MPC Coordination Server for Threshold Cryptography**

FastAPI + MongoDB + Socket.IO server that orchestrates the 4-round threshold ECDSA signing protocol for GuardianVault.

## Features

- ✅ **REST API** - Vault, guardian, and transaction management
- ✅ **WebSocket MPC** - Real-time 4-round signing protocol coordination
- ✅ **MongoDB** - Async database with Motor driver
- ✅ **Threshold Crypto** - Integrates with existing Python threshold crypto code
- ✅ **Guardian Invitations** - Secure invitation code system
- ✅ **Auto Round Progression** - Server automatically progresses through signing rounds
- ✅ **Complete Observability** - Detailed logging and status tracking

## Architecture

```
Guardian Apps (3+) ←→ WebSocket ←→ Coordination Server ←→ MongoDB
                                          ↓
                                  Threshold Crypto
                                  (Python threshold_*.py)
```

### 4-Round MPC Protocol

**Round 1** - Guardian generates nonce share k_i and R_i point
- Guardian → Server: `{nonce_share, R_point}`
- Server stores data, waits for all guardians

**Round 2** - Server combines all R points (automatic)
- Server computes: `R = R_1 + R_2 + R_3`, `r = R.x mod n`
- Server computes: `k_total = k_1 + k_2 + k_3 mod n`
- Server broadcasts: Round 2 complete

**Round 3** - Guardian computes signature share
- Guardian requests Round 2 data
- Guardian computes: `s_i = k^(-1) × (z/n + r×x_i) mod n`
- Guardian → Server: `{signature_share}`

**Round 4** - Server combines signature shares (automatic)
- Server computes: `s = s_1 + s_2 + s_3 mod n`
- Server stores final signature `(r, s)`
- Server broadcasts: Transaction complete

## Installation

### Prerequisites

- Python 3.8+
- MongoDB 4.4+
- GuardianVault threshold crypto dependencies

### Install Dependencies

```bash
cd coordination-server
pip install -r requirements.txt
```

### Configure Environment

```bash
cp .env.example .env
# Edit .env with your MongoDB URL and settings
```

### Start MongoDB

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install MongoDB locally
brew install mongodb-community  # macOS
# Linux/Windows: see https://www.mongodb.com/docs/manual/installation/
```

## Usage

### Start Server

```bash
# Development mode (with auto-reload)
cd coordination-server
python -m app.main

# Or with uvicorn directly
uvicorn app.main:socket_app --reload --host 0.0.0.0 --port 8000
```

Server will be available at:
- REST API: `http://localhost:8000`
- WebSocket: `ws://localhost:8000/socket.io/`
- API Docs: `http://localhost:8000/docs`

### Quick Test

```bash
# Health check
curl http://localhost:8000/health

# Create a vault
curl -X POST http://localhost:8000/api/vaults \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Vault",
    "coin_type": "bitcoin",
    "threshold": 2,
    "total_guardians": 3,
    "account_index": 0
  }'

# Response: {"vault_id": "vault_...", ...}

# Invite guardians
curl -X POST http://localhost:8000/api/guardians/invite \
  -H "Content-Type: application/json" \
  -d '{
    "vault_id": "vault_...",
    "name": "Alice",
    "email": "alice@example.com"
  }'

# Response: {"guardian_id": "guard_...", "invitation_code": "INVITE-...", ...}
```

## API Reference

### REST API

#### Vaults

```
POST   /api/vaults              - Create vault
GET    /api/vaults              - List vaults
GET    /api/vaults/{vault_id}   - Get vault
PATCH  /api/vaults/{vault_id}   - Update vault
DELETE /api/vaults/{vault_id}   - Archive vault
POST   /api/vaults/{vault_id}/activate - Activate vault
GET    /api/vaults/{vault_id}/stats - Get vault stats
```

#### Guardians

```
POST   /api/guardians/invite     - Invite guardian
POST   /api/guardians/join       - Join with invitation code
GET    /api/guardians            - List guardians
GET    /api/guardians/{id}       - Get guardian
PATCH  /api/guardians/{id}       - Update guardian
DELETE /api/guardians/{id}       - Remove guardian
GET    /api/guardians/{id}/stats - Get guardian stats
```

#### Transactions

```
POST   /api/transactions          - Create transaction
GET    /api/transactions          - List transactions
GET    /api/transactions/pending  - Get pending transactions
GET    /api/transactions/{id}     - Get transaction
PATCH  /api/transactions/{id}     - Update transaction
DELETE /api/transactions/{id}     - Cancel transaction
GET    /api/transactions/{id}/status - Get detailed status
```

### WebSocket Events

#### Connection

```javascript
// Connect with authentication
const socket = io('ws://localhost:8000', {
  auth: {
    vaultId: 'vault_...',
    guardianId: 'guard_...'
  }
});

// Events
socket.on('connect', () => console.log('Connected'));
socket.on('disconnect', () => console.log('Disconnected'));
socket.on('guardian:connected', (data) => console.log('Guardian joined:', data));
socket.on('guardian:disconnected', (data) => console.log('Guardian left:', data));
```

#### Signing Protocol

```javascript
// Submit Round 1 data
socket.emit('signing:submit_round1', {
  transactionId: 'tx_...',
  guardianId: 'guard_...',
  nonceShare: 'hex_string',
  rPoint: 'hex_string'
}, (response) => {
  console.log('Round 1 submitted:', response);
});

// Listen for Round 2 ready
socket.on('signing:round2_ready', (data) => {
  console.log('Round 2 ready:', data);
  // Get Round 2 data for Round 3
});

// Get Round 2 data
socket.emit('signing:get_round2_data', {
  transactionId: 'tx_...',
  guardianId: 'guard_...'
}, (response) => {
  const { kTotal, r, numParties } = response.data;
  // Use for Round 3 computation
});

// Submit Round 3 data
socket.emit('signing:submit_round3', {
  transactionId: 'tx_...',
  guardianId: 'guard_...',
  signatureShare: 12345
}, (response) => {
  console.log('Round 3 submitted:', response);
});

// Listen for signing complete
socket.on('signing:complete', (data) => {
  console.log('Transaction signed!', data);
  // Get final signature
});

// Get final signature
socket.emit('signing:get_final_signature', {
  transactionId: 'tx_...',
  guardianId: 'guard_...'
}, (response) => {
  const { r, s, rHex, sHex } = response.signature;
  console.log('Final signature:', { r, s });
});
```

#### Transactions

```javascript
// Get pending transactions
socket.emit('transactions:get_pending', {
  vaultId: 'vault_...'
}, (response) => {
  console.log('Pending transactions:', response.transactions);
});

// Get single transaction
socket.emit('transactions:get', {
  transactionId: 'tx_...'
}, (response) => {
  console.log('Transaction:', response.transaction);
});
```

## Complete Workflow Example

### 1. Setup Vault and Guardians

```python
import requests

BASE_URL = "http://localhost:8000"

# Create vault
vault_resp = requests.post(f"{BASE_URL}/api/vaults", json={
    "name": "Company Treasury",
    "coin_type": "bitcoin",
    "threshold": 3,
    "total_guardians": 5,
    "account_index": 0
})
vault_id = vault_resp.json()["vault_id"]

# Invite 5 guardians
guardians = []
for i, name in enumerate(["Alice", "Bob", "Charlie", "Diana", "Eve"], 1):
    resp = requests.post(f"{BASE_URL}/api/guardians/invite", json={
        "vault_id": vault_id,
        "name": name,
        "email": f"{name.lower()}@company.com",
        "role": f"Guardian {i}"
    })
    guardians.append(resp.json())
    print(f"Invited {name}: {resp.json()['invitation_code']}")

# Each guardian joins with their invitation code
# (This would be done by Guardian Desktop App)
```

### 2. Initiate Transaction

```python
# Create transaction
tx_resp = requests.post(f"{BASE_URL}/api/transactions", json={
    "vault_id": vault_id,
    "type": "send",
    "coin_type": "bitcoin",
    "amount": "0.5",
    "recipient": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    "fee": "0.0001",
    "memo": "Payment for services"
})
transaction_id = tx_resp.json()["transaction_id"]
print(f"Created transaction: {transaction_id}")
```

### 3. Guardians Sign (via Guardian App)

Each guardian:
1. Connects via WebSocket
2. Receives transaction notification
3. Executes Round 1 locally → submits to server
4. Server combines R points (Round 2)
5. Executes Round 3 locally → submits to server
6. Server combines signatures (Round 4)
7. Transaction complete!

## MongoDB Collections

### vaults
```javascript
{
  vault_id: "vault_abc123",
  name: "Company Treasury",
  coin_type: "bitcoin",
  threshold: 3,
  total_guardians: 5,
  status: "active",
  guardians_joined: 5,
  guardian_ids: ["guard_1", "guard_2", ...],
  xpub: "...",
  created_at: ISODate("...")
}
```

### guardians
```javascript
{
  guardian_id: "guard_abc123",
  vault_id: "vault_abc123",
  name: "Alice",
  email: "alice@company.com",
  invitation_code: "INVITE-ABC-123-XYZ",
  status: "active",
  share_id: 1,
  has_share: true,
  total_signatures: 15,
  created_at: ISODate("...")
}
```

### transactions
```javascript
{
  transaction_id: "tx_abc123",
  vault_id: "vault_abc123",
  coin_type: "bitcoin",
  amount: "0.5",
  recipient: "1A1z...",
  message_hash: "9c12cf...",
  status: "completed",
  signatures_required: 3,
  signatures_received: 3,
  round1_data: {
    "guard_1": { nonce_share: "...", r_point: "..." },
    "guard_2": { nonce_share: "...", r_point: "..." },
    "guard_3": { nonce_share: "...", r_point: "..." }
  },
  round2_data: { k_total: 123, r: 456, ... },
  round3_data: {
    "guard_1": { signature_share: 789 },
    "guard_2": { signature_share: 101 },
    "guard_3": { signature_share: 112 }
  },
  final_signature: { r: 456, s: 1002, ... },
  created_at: ISODate("...")
}
```

## Testing

### Manual Testing with Guardian App

1. **Start server**: `python -m app.main`
2. **Start MongoDB**: Ensure MongoDB is running
3. **Create vault**: Use REST API or admin dashboard
4. **Invite 3+ guardians**: Get invitation codes
5. **Start Guardian Apps**: Use invitation codes to join
6. **Create transaction**: Via REST API
7. **Sign with guardians**: Each guardian signs via their app
8. **Verify signature**: Check transaction status

### Unit Testing

```bash
# Run tests (when implemented)
pytest

# With coverage
pytest --cov=app --cov-report=html
```

## Security Considerations

### Current Implementation (Dev/Testing)

✅ Basic invitation code authentication
✅ Guardian-vault access validation
✅ Round data validation
✅ Transaction timeout tracking

⚠️ **NOT production-ready** - needs:
- JWT authentication
- Rate limiting
- Input sanitization
- HTTPS/WSS only
- Audit logging
- Guardian session management
- Database encryption
- Secrets management (not .env)

### For Production

- Use JWT tokens instead of invitation codes
- Implement rate limiting (per guardian, per vault)
- Add API key authentication for admin operations
- Use HTTPS/WSS with proper TLS certificates
- Store secrets in environment/secrets manager
- Add audit logging for all operations
- Implement guardian session timeouts
- Add intrusion detection
- Regular security audits

## Troubleshooting

### MongoDB Connection Failed

```
Error: ServerSelectionTimeoutError
```

**Solution**:
```bash
# Check MongoDB is running
docker ps | grep mongo
# Or
brew services list | grep mongodb

# Start MongoDB
docker start mongodb
# Or
brew services start mongodb-community
```

### WebSocket Connection Refused

```
Error: WebSocket connection failed
```

**Solution**:
- Check server is running: `curl http://localhost:8000/health`
- Check CORS settings in `.env`
- Verify Guardian App uses correct URL

### Round 2/4 Not Executing

```
Status stuck at "signing_round1"
```

**Solution**:
- Check server logs for errors
- Verify all required guardians submitted Round 1 data
- Check MongoDB for transaction document
- Ensure threshold crypto imports are working

### Import Errors

```
ModuleNotFoundError: No module named 'threshold_signing'
```

**Solution**:
```bash
# Verify parent directory structure
ls ../*.py | grep threshold

# Ensure running from project root
cd /Users/ivan/Downloads/claude-mcp
python -m coordination-server.app.main
```

## Development

### Project Structure

```
coordination-server/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app + Socket.IO
│   ├── config.py               # Configuration
│   ├── database.py             # MongoDB connection
│   ├── models/                 # Pydantic models
│   │   ├── vault.py
│   │   ├── guardian.py
│   │   └── transaction.py
│   ├── routers/                # REST API endpoints
│   │   ├── vaults.py
│   │   ├── guardians.py
│   │   └── transactions.py
│   ├── services/               # Business logic
│   │   └── mpc_coordinator.py  # MPC signing coordinator
│   └── websocket/              # WebSocket handlers
│       └── signing_protocol.py
├── requirements.txt
├── .env.example
└── README.md
```

### Adding New Features

**New REST Endpoint**:
1. Add route in `app/routers/`
2. Add Pydantic models in `app/models/`
3. Import router in `app/main.py`

**New WebSocket Event**:
1. Add handler in `app/websocket/signing_protocol.py`
2. Register in `register_handlers()` function

**New Database Collection**:
1. Add indexes in `app/database.py`
2. Add Pydantic model in `app/models/`

## Performance

- **MongoDB**: Indexed queries for fast lookups
- **WebSocket**: Async Socket.IO for concurrent connections
- **FastAPI**: Async endpoints with uvicorn ASGI server
- **Threshold Crypto**: Pure Python (consider Rust extension for production)

## License

See LICENSE file in project root.

Non-Commercial Open Source License - Educational and personal use only.

## Support

For issues and questions:
1. Check server logs: Look for ERROR level messages
2. Check MongoDB: `mongo guardianvault --eval "db.transactions.find()"`
3. Test WebSocket: Use socket.io-client test script
4. Contact: ioudkerk@gmail.com

---

**GuardianVault Coordination Server** - MPC Coordination for Cryptocurrency Custody
