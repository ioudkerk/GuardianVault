#!/Users/ivan/.virtualenvs/claude-mcp/bin/python
"""
Complete GuardianVault Coordination Server Test Workflow

This script demonstrates:
1. Generating threshold key shares for 3 guardians
2. Creating a vault on the coordination server
3. Inviting guardians
4. Creating a transaction
5. Simulating guardians signing via WebSocket (4-round MPC)
6. Getting the final signature

Prerequisites:
- MongoDB running (docker run -d -p 27017:27017 mongo:latest)
- Coordination server running (python -m coordination-server.app.main)
"""

import asyncio
import json
import requests
from typing import Dict, List
import socketio
from ecdsa.curves import SECP256k1
from ecdsa.ellipticcurve import Point
import hashlib
import secrets

# Import existing threshold crypto modules from guardianvault package
from guardianvault.threshold_mpc_keymanager import (
    ThresholdKeyGeneration,
    ThresholdBIP32,
    KeyShare as ThresholdKeyShare,
    ExtendedPublicKey
)
from guardianvault.threshold_signing import ThresholdSigner, KeyShare
from guardianvault.threshold_addresses import BitcoinAddressGenerator, EthereumAddressGenerator

# Configuration
COORD_SERVER_URL = "http://localhost:8000"
COORD_WS_URL = "ws://localhost:8000"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_step(step: str, message: str):
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}STEP {step}: {message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")


def print_success(message: str):
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_info(message: str):
    print(f"{Colors.OKCYAN}  {message}{Colors.ENDC}")


def print_error(message: str):
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


# ==============================================================================
# STEP 1: Generate Key Shares (Offline)
# ==============================================================================

def generate_key_shares(num_parties: int = 3, threshold: int = 3):
    """Generate threshold key shares for guardians"""
    print_step("1", "Generating Threshold Key Shares")

    # Generate initial key shares
    print_info(f"Generating {num_parties} key shares...")
    shares, master_pubkey = ThresholdKeyGeneration.generate_shares(num_parties, threshold)
    print_success(f"Key shares generated")

    # Derive BIP32 master keys
    print_info("Deriving BIP32 master keys...")
    seed = secrets.token_bytes(32)
    master_shares, master_pubkey, master_chain = ThresholdBIP32.derive_master_keys_threshold(shares, seed)
    print_success(f"Master public key: {master_pubkey.hex()[:32]}...")

    # Derive Bitcoin account xpub (m/44'/0'/0')
    print_info("Deriving Bitcoin account (m/44'/0'/0')...")
    btc_xpub = ThresholdBIP32.derive_account_xpub_threshold(
        master_shares, master_chain, coin_type=0, account=0
    )

    # Get the Bitcoin account shares
    # Derive m/44' -> m/44'/0' -> m/44'/0'/0'
    btc_shares_44, btc_pub_44, btc_chain_44 = ThresholdBIP32.derive_hardened_child_threshold(
        master_shares, master_pubkey, master_chain, 44
    )
    btc_shares_0, btc_pub_0, btc_chain_0 = ThresholdBIP32.derive_hardened_child_threshold(
        btc_shares_44, btc_pub_44, btc_chain_44, 0
    )
    btc_master_shares, btc_pub_final, btc_chain_final = ThresholdBIP32.derive_hardened_child_threshold(
        btc_shares_0, btc_pub_0, btc_chain_0, 0
    )

    # Derive Ethereum account xpub (m/44'/60'/0')
    print_info("Deriving Ethereum account (m/44'/60'/0')...")
    eth_xpub = ThresholdBIP32.derive_account_xpub_threshold(
        master_shares, master_chain, coin_type=60, account=0
    )

    # Get the Ethereum account shares
    # Derive m/44' -> m/44'/60' -> m/44'/60'/0'
    eth_shares_44, eth_pub_44, eth_chain_44 = ThresholdBIP32.derive_hardened_child_threshold(
        master_shares, master_pubkey, master_chain, 44
    )
    eth_shares_60, eth_pub_60, eth_chain_60 = ThresholdBIP32.derive_hardened_child_threshold(
        eth_shares_44, eth_pub_44, eth_chain_44, 60
    )
    eth_master_shares, eth_pub_final, eth_chain_final = ThresholdBIP32.derive_hardened_child_threshold(
        eth_shares_60, eth_pub_60, eth_chain_60, 0
    )

    # Save shares to files
    parties_data = []
    for i in range(num_parties):
        party_data = {
            "party_id": i + 1,
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"][i],
            "key_share": {
                "party_id": shares[i].party_id,
                "share_value": shares[i].share_value.hex(),
                "total_parties": shares[i].total_parties,
                "threshold": shares[i].threshold,
                "metadata": shares[i].metadata
            },
            "master_shares": {
                "bitcoin": {
                    "party_id": btc_master_shares[i].party_id,
                    "share_value": btc_master_shares[i].share_value.hex(),
                    "total_parties": btc_master_shares[i].total_parties,
                    "threshold": btc_master_shares[i].threshold,
                    "metadata": btc_master_shares[i].metadata
                },
                "ethereum": {
                    "party_id": eth_master_shares[i].party_id,
                    "share_value": eth_master_shares[i].share_value.hex(),
                    "total_parties": eth_master_shares[i].total_parties,
                    "threshold": eth_master_shares[i].threshold,
                    "metadata": eth_master_shares[i].metadata
                }
            }
        }

        filename = f"party_{i+1}_shares.json"
        with open(filename, 'w') as f:
            json.dump(party_data, f, indent=2)

        print_success(f"Saved {party_data['name']}'s shares to {filename}")
        parties_data.append(party_data)

    # Generate addresses for verification
    print_info("\nGenerating Bitcoin address from public key...")
    btc_address = BitcoinAddressGenerator.pubkey_to_address(btc_pub_final, network="mainnet")
    print_success(f"Bitcoin Address: {btc_address}")

    return parties_data, btc_address


# ==============================================================================
# STEP 2: Create Vault on Coordination Server
# ==============================================================================

def create_vault(btc_address: str, threshold: int = 3, total_guardians: int = 3):
    """Create a new vault on the coordination server"""
    print_step("2", "Creating Vault on Coordination Server")

    vault_data = {
        "name": "Test Treasury Vault",
        "coin_type": "bitcoin",
        "threshold": threshold,
        "total_guardians": total_guardians,
        "account_index": 0,
        "xpub": btc_address  # Store the address for reference
    }

    print_info("Sending vault creation request...")
    response = requests.post(
        f"{COORD_SERVER_URL}/api/vaults",
        json=vault_data
    )

    if response.status_code in [200, 201]:
        vault = response.json()
        print_success(f"Vault created: {vault['vault_id']}")
        print_info(f"  Name: {vault['name']}")
        print_info(f"  Coin: {vault['coin_type']}")
        print_info(f"  Threshold: {vault['threshold']}/{vault['total_guardians']}")
        print_info(f"  Status: {vault['status']}")
        return vault
    else:
        print_error(f"Failed to create vault (status {response.status_code}): {response.text}")
        return None


# ==============================================================================
# STEP 3: Invite Guardians
# ==============================================================================

def invite_guardians(vault_id: str, parties_data: List[Dict]):
    """Invite guardians to the vault"""
    print_step("3", "Inviting Guardians to Vault")

    guardians = []
    for party in parties_data:
        print_info(f"Inviting {party['name']}...")

        response = requests.post(
            f"{COORD_SERVER_URL}/api/guardians/invite",
            json={
                "vault_id": vault_id,
                "name": party['name'],
                "email": f"{party['name'].lower()}@example.com",
                "role": f"Guardian {party['party_id']}"
            }
        )

        if response.status_code in [200, 201]:
            guardian = response.json()
            guardian['party_data'] = party  # Attach the key share data
            guardians.append(guardian)

            print_success(f"  Guardian ID: {guardian['guardian_id']}")
            print_success(f"  Invitation Code: {guardian['invitation_code']}")
        else:
            print_error(f"Failed to invite {party['name']} (status {response.status_code}): {response.text}")

    return guardians


# ==============================================================================
# STEP 4: Guardians Join Vault
# ==============================================================================

def guardians_join(guardians: List[Dict]):
    """Simulate guardians joining the vault with their invitation codes"""
    print_step("4", "Guardians Joining Vault")

    for guardian in guardians:
        print_info(f"{guardian['name']} joining with code {guardian['invitation_code']}...")

        response = requests.post(
            f"{COORD_SERVER_URL}/api/guardians/join",
            json={
                "invitation_code": guardian['invitation_code'],
                "share_id": guardian['party_data']['party_id']
            }
        )

        if response.status_code in [200, 201]:
            print_success(f"  {guardian['name']} joined successfully")
        else:
            print_error(f"Failed to join (status {response.status_code}): {response.text}")


# ==============================================================================
# STEP 5: Activate Vault
# ==============================================================================

def activate_vault(vault_id: str):
    """Activate the vault once all guardians have joined"""
    print_step("5", "Activating Vault")

    response = requests.post(
        f"{COORD_SERVER_URL}/api/vaults/{vault_id}/activate"
    )

    if response.status_code in [200, 201]:
        vault = response.json()
        print_success("Vault activated successfully")
        print_info(f"  Status: {vault['status']}")
        print_info(f"  Guardians: {vault['guardians_joined']}/{vault['total_guardians']}")
        return vault
    else:
        print_error(f"Failed to activate vault (status {response.status_code}): {response.text}")
        return None


# ==============================================================================
# STEP 6: Create Transaction
# ==============================================================================

def create_transaction(vault_id: str):
    """Create a transaction that needs to be signed"""
    print_step("6", "Creating Transaction")

    # Create a test message hash (in production, this would be the actual transaction hash)
    message = "Send 0.5 BTC to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    message_hash = hashlib.sha256(message.encode()).hexdigest()

    tx_data = {
        "vault_id": vault_id,
        "type": "send",
        "coin_type": "bitcoin",
        "amount": "0.5",
        "recipient": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        "fee": "0.0001",
        "memo": "Test payment",
        "message_hash": message_hash
    }

    print_info("Creating transaction...")
    response = requests.post(
        f"{COORD_SERVER_URL}/api/transactions",
        json=tx_data
    )

    if response.status_code in [200, 201]:
        transaction = response.json()
        print_success(f"Transaction created: {transaction['transaction_id']}")
        print_info(f"  Type: {transaction['type']}")
        print_info(f"  Amount: {transaction['amount']} BTC")
        print_info(f"  Recipient: {transaction['recipient']}")
        print_info(f"  Message Hash: {transaction['message_hash']}")
        print_info(f"  Status: {transaction['status']}")
        return transaction
    else:
        print_error(f"Failed to create transaction (status {response.status_code}): {response.text}")
        return None


# ==============================================================================
# STEP 7: Guardians Sign Transaction (4-Round MPC via WebSocket)
# ==============================================================================

class GuardianSigningClient:
    """Simulates a guardian signing via WebSocket"""

    def __init__(self, guardian: Dict, transaction_id: str, message_hash: str):
        self.guardian = guardian
        self.party_data = guardian['party_data']
        self.transaction_id = transaction_id
        self.message_hash = message_hash
        self.vault_id = guardian['vault_id']

        # Load the Bitcoin key share for signing
        btc_share_data = self.party_data['master_shares']['bitcoin']
        self.key_share = ThresholdKeyShare(
            party_id=btc_share_data['party_id'],
            share_value=bytes.fromhex(btc_share_data['share_value']),
            total_parties=btc_share_data['total_parties'],
            threshold=btc_share_data['threshold'],
            metadata=btc_share_data['metadata']
        )

        # Store nonce for Round 3
        self.nonce_share = None

        # Socket.IO client
        self.sio = socketio.AsyncClient()
        self.setup_handlers()

        # State
        self.round1_complete = False
        self.round2_complete = False
        self.round3_complete = False
        self.signing_complete = False

    def setup_handlers(self):
        """Setup WebSocket event handlers"""

        @self.sio.event
        async def connect():
            print_success(f"  {self.guardian['name']} connected to server")

        @self.sio.event
        async def disconnect():
            print_info(f"  {self.guardian['name']} disconnected")

        @self.sio.on('signing:round2_ready')
        async def on_round2_ready(data):
            print_info(f"  {self.guardian['name']} received signing:round2_ready event: {data}")
            tx_id = data.get('transactionId') or data.get('transaction_id')
            if tx_id == self.transaction_id:
                print_success(f"  {self.guardian['name']} Round 2 ready - executing Round 3")
                await self.execute_round3()
            else:
                print_error(f"  {self.guardian['name']} Transaction ID mismatch: expected {self.transaction_id}, got {tx_id}")

        @self.sio.on('signing:complete')
        async def on_signing_complete(data):
            print_info(f"  {self.guardian['name']} received signing:complete event: {data}")
            tx_id = data.get('transactionId') or data.get('transaction_id')
            if tx_id == self.transaction_id:
                print_success(f"  {self.guardian['name']} Signing complete!")
                self.signing_complete = True
            else:
                print_error(f"  {self.guardian['name']} Transaction ID mismatch: expected {self.transaction_id}, got {tx_id}")

        @self.sio.on('*')
        async def catch_all(event, data):
            print_info(f"  {self.guardian['name']} received event '{event}': {data}")

    async def connect(self):
        """Connect to coordination server"""
        await self.sio.connect(
            COORD_SERVER_URL,
            auth={
                'vaultId': self.vault_id,
                'guardianId': self.guardian['guardian_id']
            },
            transports=['websocket']
        )

    async def execute_round1(self):
        """Execute Round 1: Generate nonce share and R point"""
        print_info(f"  {self.guardian['name']} executing Round 1...")

        # Generate nonce and R point using static method
        self.nonce_share, r_point_bytes = ThresholdSigner.sign_round1_generate_nonce(
            self.key_share.party_id
        )

        # Submit to server
        response = await self.sio.call(
            'signing_submit_round1',
            {
                'transactionId': self.transaction_id,
                'guardianId': self.guardian['guardian_id'],
                'nonceShare': self.nonce_share.to_bytes(32, 'big').hex(),
                'rPoint': r_point_bytes.hex()
            }
        )

        if response['success']:
            print_success(f"    Round 1 submitted")
            self.round1_complete = True
        else:
            print_error(f"    Round 1 failed: {response.get('error')}")

    async def execute_round3(self):
        """Execute Round 3: Compute signature share"""
        print_info(f"  {self.guardian['name']} executing Round 3...")

        # Get Round 2 data from server
        response = await self.sio.call(
            'signing_get_round2_data',
            {
                'transactionId': self.transaction_id,
                'guardianId': self.guardian['guardian_id']
            }
        )

        if not response['success']:
            print_error(f"    Failed to get Round 2 data: {response.get('error')}")
            return

        round2_data = response['data']
        k_total = round2_data['kTotal']
        r = round2_data['r']

        # Compute signature share using static method
        message_hash_bytes = bytes.fromhex(self.message_hash)
        sig_share = ThresholdSigner.sign_round3_compute_signature_share(
            key_share=self.key_share,
            nonce_share=self.nonce_share,
            message_hash=message_hash_bytes,
            r=r,
            k_total=k_total,
            num_parties=self.key_share.total_parties
        )

        # Submit to server
        response = await self.sio.call(
            'signing_submit_round3',
            {
                'transactionId': self.transaction_id,
                'guardianId': self.guardian['guardian_id'],
                'signatureShare': sig_share
            }
        )

        if response['success']:
            print_success(f"    Round 3 submitted")
            self.round3_complete = True
        else:
            print_error(f"    Round 3 failed: {response.get('error')}")

    async def disconnect(self):
        """Disconnect from server"""
        await self.sio.disconnect()


async def guardians_sign_transaction(guardians: List[Dict], transaction: Dict):
    """Simulate all guardians signing the transaction"""
    print_step("7", "Guardians Signing Transaction (4-Round MPC)")

    # Create signing clients for each guardian
    clients = []
    for guardian in guardians:
        client = GuardianSigningClient(
            guardian=guardian,
            transaction_id=transaction['transaction_id'],
            message_hash=transaction['message_hash']
        )
        clients.append(client)

    # Connect all guardians
    print_info("Connecting guardians to server...")
    await asyncio.gather(*[client.connect() for client in clients])
    await asyncio.sleep(1)  # Give connections time to establish

    # Round 1: All guardians generate and submit nonce shares
    print_info("\n[Round 1] Guardians generating nonce shares...")
    await asyncio.gather(*[client.execute_round1() for client in clients])

    # Wait for Round 2, 3, and 4 to complete (triggered by server events)
    print_info("\n[Round 2-4] Waiting for server to coordinate signing rounds...")

    # Wait up to 30 seconds for signing to complete
    max_wait = 30
    waited = 0
    while waited < max_wait:
        if all(client.signing_complete for client in clients):
            print_success(f"\nAll guardians completed signing after {waited}s")
            break
        await asyncio.sleep(1)
        waited += 1

    if not all(client.signing_complete for client in clients):
        print_error(f"\nWarning: Not all guardians completed signing after {max_wait}s")
        for client in clients:
            if not client.signing_complete:
                print_error(f"  {client.guardian['name']}: Round1={client.round1_complete}, Round3={client.round3_complete}, Complete={client.signing_complete}")

    # Give a moment for any final events
    await asyncio.sleep(2)

    # Disconnect all clients
    await asyncio.gather(*[client.disconnect() for client in clients])

    print_success("\nGuardians disconnected")


# ==============================================================================
# STEP 8: Get Final Signature
# ==============================================================================

def get_final_signature(transaction_id: str):
    """Retrieve the final signature from the server"""
    print_step("8", "Retrieving Final Signature")

    response = requests.get(
        f"{COORD_SERVER_URL}/api/transactions/{transaction_id}"
    )

    if response.status_code == 200:
        transaction = response.json()

        print_info(f"Transaction Status: {transaction['status']}")

        if transaction['status'] == 'completed' and 'final_signature' in transaction:
            sig = transaction['final_signature']
            print_success("\nFinal Signature:")
            print_info(f"  r: {sig['r']}")
            print_info(f"  s: {sig['s']}")
            print_info(f"  r (hex): {sig['rHex']}")
            print_info(f"  s (hex): {sig['sHex']}")
            return sig
        else:
            print_error("Transaction not yet completed or signature not available")
            print_info(f"  Current status: {transaction['status']}")
            print_info(f"  Signatures received: {transaction['signatures_received']}/{transaction['signatures_required']}")
    else:
        print_error(f"Failed to get transaction: {response.text}")

    return None


# ==============================================================================
# MAIN WORKFLOW
# ==============================================================================

async def main():
    """Run the complete workflow"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 80)
    print("  GuardianVault Coordination Server - Complete Test Workflow")
    print("=" * 80)
    print(f"{Colors.ENDC}\n")

    print_info("Prerequisites:")
    print_info("  1. MongoDB running (docker run -d -p 27017:27017 mongo:latest)")
    print_info("  2. Coordination server running (cd coordination-server && python -m app.main)")

    input("\nPress Enter to start the workflow...")

    try:
        # Step 1: Generate key shares
        parties_data, btc_address = generate_key_shares(num_parties=3, threshold=3)

        # Step 2: Create vault
        vault = create_vault(btc_address, threshold=3, total_guardians=3)
        if not vault:
            return

        # Step 3: Invite guardians
        guardians = invite_guardians(vault['vault_id'], parties_data)

        # Step 4: Guardians join
        guardians_join(guardians)

        # Step 5: Activate vault
        activated_vault = activate_vault(vault['vault_id'])
        if not activated_vault:
            return

        # Step 6: Create transaction
        transaction = create_transaction(vault['vault_id'])
        if not transaction:
            return

        # Step 7: Guardians sign transaction
        await guardians_sign_transaction(guardians, transaction)

        # Step 8: Get final signature
        signature = get_final_signature(transaction['transaction_id'])

        if signature:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}")
            print("=" * 80)
            print("  SUCCESS! Transaction signed using threshold MPC")
            print("=" * 80)
            print(f"{Colors.ENDC}\n")
        else:
            print(f"\n{Colors.WARNING}")
            print("Signing may still be in progress. Check server logs for details.")
            print(f"{Colors.ENDC}\n")

    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Workflow interrupted{Colors.ENDC}")
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
