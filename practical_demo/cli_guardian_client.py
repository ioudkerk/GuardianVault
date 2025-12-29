#!/usr/bin/env python3
"""
CLI 2: Guardian Client Simulator
Simulates a guardian client that connects to the coordination server and participates in signing
"""
import sys
import os
import json
import argparse
import asyncio
import socketio
import aiohttp

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardianvault.mpc_keymanager import (
    KeyShare,
    MPCBIP32,
    ExtendedPublicKey,
    PublicKeyDerivation
)
from guardianvault.mpc_signing import MPCSigner


class GuardianClient:
    """Guardian client that connects to coordination server and participates in MPC signing"""

    def __init__(self, server_url: str, share_file: str, guardian_id: str = None, vault_id: str = None, vault_config: str = None):
        self.server_url = server_url
        self.share_file = share_file
        self.guardian_id = guardian_id
        self.vault_id = vault_id
        self.vault_config_file = vault_config

        # Load share
        self.share_data = self._load_share()

        # Load Bitcoin account share (m/44'/0'/0')
        # New format stores account-level shares directly
        if 'bitcoin_account_share' in self.share_data:
            self.bitcoin_account_share = KeyShare.from_dict(self.share_data['bitcoin_account_share'])
        elif 'share' in self.share_data:
            # Legacy format - assume it's a master share (will fail)
            print("⚠️  WARNING: Using legacy master share format. Please regenerate shares!")
            self.bitcoin_account_share = KeyShare.from_dict(self.share_data['share'])
        else:
            raise ValueError("Share file missing 'bitcoin_account_share' or 'share' field")

        # Load Ethereum account share (m/44'/60'/0') if available
        if 'ethereum_account_share' in self.share_data:
            self.ethereum_account_share = KeyShare.from_dict(self.share_data['ethereum_account_share'])
        else:
            # If no Ethereum share, we can't sign Ethereum transactions
            print("⚠️  WARNING: No ethereum_account_share found. Ethereum transactions will not work!")
            self.ethereum_account_share = None

        # Load vault config for xpub
        self.vault_config = None
        if vault_config:
            with open(vault_config, 'r') as f:
                self.vault_config = json.load(f)

        # Socket.IO client
        self.sio = socketio.AsyncClient()
        self._setup_event_handlers()

        # State
        self.connected = False
        self.current_transaction = None
        self.nonce_share = None
        self.r_point = None

    def _load_share(self):
        """Load share from file"""
        with open(self.share_file, 'r') as f:
            return json.load(f)

    def _derive_non_hardened_child_share(self, parent_share: KeyShare, parent_pubkey: bytes, parent_chain: bytes, index: int) -> KeyShare:
        """
        Derive non-hardened child share from parent share
        Each party can do this independently without threshold computation

        IMPORTANT: For additive secret sharing, each party must add tweak/n
        where n is the total number of parties. This ensures that the sum
        of child shares equals parent_key + tweak, not parent_key + n*tweak.

        Args:
            parent_share: Parent key share
            parent_pubkey: Parent public key (public information)
            parent_chain: Parent chain code
            index: Child index (< 0x80000000 for non-hardened)
        """
        import hmac
        import hashlib
        from guardianvault.mpc_keymanager import SECP256K1_N

        # Ensure non-hardened
        if index >= 0x80000000:
            raise ValueError("Index must be < 0x80000000 for non-hardened derivation")

        # Compute HMAC using parent public key (same for all parties)
        data = parent_pubkey + index.to_bytes(4, 'big')
        hmac_result = hmac.new(parent_chain, data, hashlib.sha512).digest()
        tweak = int.from_bytes(hmac_result[:32], 'big') % SECP256K1_N

        # For additive secret sharing: each party adds tweak/n
        # This ensures sum(child_shares) = sum(parent_shares) + tweak
        n = parent_share.total_parties
        tweak_share = (tweak * pow(n, -1, SECP256K1_N)) % SECP256K1_N

        # Child share = parent_share + tweak/n (mod n)
        parent_share_int = int.from_bytes(parent_share.share_value, 'big')
        child_share_int = (parent_share_int + tweak_share) % SECP256K1_N

        child_share = KeyShare(
            party_id=parent_share.party_id,
            share_value=child_share_int.to_bytes(32, 'big'),
            total_parties=parent_share.total_parties,
            threshold=parent_share.threshold,
            metadata={
                'type': 'non_hardened_child',
                'parent_path': parent_share.metadata.get('derivation', 'unknown'),
                'index': index
            }
        )

        return child_share

    def _setup_event_handlers(self):
        """Setup Socket.IO event handlers"""

        @self.sio.event
        async def connect():
            print(f"✓ Connected to coordination server")
            self.connected = True

        @self.sio.event
        async def disconnect():
            print(f"✗ Disconnected from coordination server")
            self.connected = False

        @self.sio.on('signing:new_transaction')
        async def on_new_transaction(data):
            print(f"\n📨 New transaction received:")
            print(f"  Transaction ID: {data['transactionId']}")
            print(f"  Type: {data['type']}")
            print(f"  Amount: {data.get('amount', 'N/A')}")
            print(f"  Recipient: {data.get('recipient', 'N/A')}")

            # Auto-participate in signing
            await self.participate_in_signing(data['transactionId'])

        @self.sio.on('signing:round2_ready')
        async def on_round2_ready(data):
            # Handle both snake_case and camelCase
            transaction_id = data.get('transactionId') or data.get('transaction_id')
            print(f"\n🔄 Round 2 ready for transaction {transaction_id}")
            print(f"  Message: {data.get('message', 'N/A')}")
            if self.current_transaction == transaction_id:
                await self.submit_round3(transaction_id)

        @self.sio.on('signing:complete')
        async def on_signing_complete(data):
            # Handle both snake_case and camelCase
            transaction_id = data.get('transactionId') or data.get('transaction_id')
            print(f"\n✅ Signing complete for transaction {transaction_id}")
            signature = data.get('signature', {})
            print(f"  Final signature:")
            print(f"    r: {str(signature.get('r', 'N/A'))[:32]}...")
            print(f"    s: {str(signature.get('s', 'N/A'))[:32]}...")
            self.current_transaction = None

    async def connect(self):
        """Connect to coordination server"""
        print(f"\n{'='*60}")
        print(f"Guardian Client Starting")
        print(f"{'='*60}")
        print(f"Server: {self.server_url}")
        print(f"Guardian ID: {self.guardian_id}")
        print(f"Vault ID: {self.vault_id}")
        print(f"Share File: {self.share_file}")
        print(f"{'='*60}\n")

        auth = {}
        if self.vault_id:
            auth['vaultId'] = self.vault_id
        if self.guardian_id:
            auth['guardianId'] = self.guardian_id

        print(f"Connecting with auth: {auth}")

        try:
            # Allow polling first, then upgrade to websocket (Socket.IO standard)
            await self.sio.connect(
                self.server_url,
                auth=auth,
                transports=['polling', 'websocket'],  # Try polling first
                wait_timeout=10
            )
        except Exception as e:
            print(f"❌ Failed to connect: {str(e)}")
            print(f"   Make sure:")
            print(f"   1. Coordination server is running")
            print(f"   2. Guardian ID and Vault ID are correct")
            print(f"   3. Guardian status is 'active'")
            raise

    async def disconnect(self):
        """Disconnect from server"""
        if self.connected:
            await self.sio.disconnect()

    async def participate_in_signing(self, transaction_id: str):
        """Participate in transaction signing"""
        self.current_transaction = transaction_id

        print(f"\n{'='*60}")
        print(f"Participating in Signing")
        print(f"{'='*60}")
        print(f"Transaction ID: {transaction_id}")
        print(f"{'='*60}\n")

        # Round 1: Generate nonce and submit
        await self.submit_round1(transaction_id)

    async def submit_round1(self, transaction_id: str):
        """Submit Round 1: Nonce share and R point"""
        print("Round 1: Generating nonce share...")

        # Generate nonce
        self.nonce_share, self.r_point = MPCSigner.sign_round1_generate_nonce(
            self.bitcoin_account_share.party_id
        )

        print(f"  ✓ Nonce share generated")
        print(f"  ✓ R point: {self.r_point.hex()[:32]}...")

        # Submit to server
        print("  Submitting to server...")
        try:
            result = await self.sio.call('signing_submit_round1', {
                'transactionId': transaction_id,
                'guardianId': self.guardian_id,
                'nonceShare': self.nonce_share.to_bytes(32, 'big').hex(),
                'rPoint': self.r_point.hex()
            }, timeout=30)

            if result.get('success'):
                print(f"  ✓ Round 1 submitted successfully")
                if result.get('allSubmitted'):
                    print(f"  ✓ All guardians submitted Round 1")
                    print(f"  → Moving to Round 2...")
            else:
                print(f"  ✗ Failed to submit Round 1: {result.get('error')}")
        except Exception as e:
            print(f"  ❌ Error submitting Round 1: {str(e)}")

    async def submit_round3(self, transaction_id: str):
        """Submit Round 3: Signature share"""
        print("\nRound 3: Computing signature share...")

        # Get Round 2 data
        try:
            round2_result = await self.sio.call('signing_get_round2_data', {
                'transactionId': transaction_id,
                'guardianId': self.guardian_id
            }, timeout=30)

            if not round2_result.get('success'):
                print(f"  ✗ Failed to get Round 2 data: {round2_result.get('error')}")
                return

            round2_data = round2_result['data']
            # Handle both snake_case and camelCase
            k_total = int(round2_data.get('kTotal') or round2_data.get('k_total'))
            r = int(round2_data.get('r'))
            message_hash_hex = round2_data.get('messageHash') or round2_data.get('message_hash')

            print(f"  ✓ Received Round 2 data")
            print(f"    k_total: {hex(k_total)[:32]}...")
            print(f"    r: {hex(r)[:32]}...")
            print(f"    message_hash: {message_hash_hex[:32]}...")

            # Derive address-level share for signing
            # Both Bitcoin and Ethereum transactions must be signed with address-level shares
            # Bitcoin: m/44'/0'/0'/0/address_index
            # Ethereum: m/44'/60'/0'/0/address_index
            if self.vault_config:
                # Get address index and coin type from transaction
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{self.server_url}/api/transactions/{transaction_id}") as resp:
                            tx_response = await resp.json()

                    address_index = tx_response.get('address_index', 0)
                    coin_type = tx_response.get('coin_type', 'bitcoin')
                    print(f"  ✓ Coin type: {coin_type}")
                    print(f"  ✓ Address index: {address_index}")

                    # Choose the correct account share and xpub based on coin type
                    if coin_type == 'ethereum':
                        # Use Ethereum account share (m/44'/60'/0')
                        if self.ethereum_account_share is None:
                            raise ValueError("No Ethereum account share available! Guardian was not registered with Ethereum support.")
                        account_share = self.ethereum_account_share
                        account_xpub = ExtendedPublicKey.from_dict(self.vault_config['ethereum']['xpub'])
                        path_prefix = "m/44'/60'/0'/0"
                    else:
                        # Use Bitcoin account share (m/44'/0'/0')
                        account_share = self.bitcoin_account_share
                        account_xpub = ExtendedPublicKey.from_dict(self.vault_config['bitcoin']['xpub'])
                        path_prefix = "m/44'/0'/0'/0"

                    # Derive change-level share (m/44'/coin_type'/0'/0) - non-hardened
                    change_pubkey, change_chain = PublicKeyDerivation.derive_public_child(account_xpub, 0)
                    change_share = self._derive_non_hardened_child_share(
                        account_share, account_xpub.public_key, account_xpub.chain_code, 0
                    )

                    # Derive address-level share (m/44'/coin_type'/0'/0/address_index) - non-hardened
                    address_pubkey, _ = PublicKeyDerivation.derive_public_child(
                        ExtendedPublicKey(change_pubkey, change_chain, account_xpub.depth + 1, b'\x00'*4, 0),
                        address_index
                    )
                    address_share = self._derive_non_hardened_child_share(
                        change_share, change_pubkey, change_chain, address_index
                    )

                    print(f"  ✓ Derived address-level share for signing ({path_prefix}/{address_index})")
                    signing_share = address_share

                except Exception as e:
                    print(f"  ⚠️  Failed to derive address share: {e}")
                    print(f"  ⚠️  Falling back to account share (will likely fail)")
                    import traceback
                    traceback.print_exc()
                    signing_share = self.bitcoin_account_share
            else:
                # No vault config - cannot derive addresses
                print(f"  ⚠️  No vault config - cannot derive address shares!")
                signing_share = self.bitcoin_account_share

            # Compute signature share using the derived address-level share
            print(f"\n  Computing signature share...")
            print(f"    Using key share: {signing_share.share_value.hex()[:32]}...")
            print(f"    Nonce: {hex(self.nonce_share)[:32]}...")
            print(f"    Message hash: {message_hash_hex[:32]}...")
            print(f"    r: {hex(r)[:32]}...")
            print(f"    k_total: {hex(k_total)[:32]}...")

            signature_share = MPCSigner.sign_round3_compute_signature_share(
                key_share=signing_share,
                nonce_share=self.nonce_share,
                message_hash=bytes.fromhex(message_hash_hex),
                r=r,
                k_total=k_total,
                num_parties=self.bitcoin_account_share.total_parties
            )

            print(f"  ✓ Signature share computed: {hex(signature_share)[:32]}...")

            # Verify the signature share is valid (non-zero and within range)
            from guardianvault.mpc_keymanager import SECP256K1_N
            if signature_share == 0 or signature_share >= SECP256K1_N:
                print(f"  ⚠️  WARNING: Signature share out of range!")
                print(f"    Value: {signature_share}")
                print(f"    Max: {SECP256K1_N}")

            # Submit to server
            print("  Submitting to server...")
            result = await self.sio.call('signing_submit_round3', {
                'transactionId': transaction_id,
                'guardianId': self.guardian_id,
                'signatureShare': str(signature_share)
            }, timeout=30)

            if result.get('success'):
                print(f"  ✓ Round 3 submitted successfully")
                if result.get('allSubmitted'):
                    print(f"  ✓ All guardians submitted Round 3")
                    print(f"  → Finalizing signature...")
            else:
                print(f"  ✗ Failed to submit Round 3: {result.get('error')}")
        except Exception as e:
            print(f"  ❌ Error in Round 3: {str(e)}")
            import traceback
            traceback.print_exc()

    async def run(self):
        """Run the guardian client"""
        try:
            await self.connect()

            # Keep running
            print("\n✓ Guardian client is running. Press Ctrl+C to stop.\n")
            while self.connected:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
        finally:
            await self.disconnect()


async def register_guardian(server_url: str, invitation_code: str):
    """Register a guardian with an invitation code"""
    import aiohttp

    print(f"\n{'='*60}")
    print(f"Registering Guardian")
    print(f"{'='*60}")
    print(f"Server: {server_url}")
    print(f"Invitation Code: {invitation_code}")
    print(f"{'='*60}\n")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{server_url}/api/guardians/join",
                json={"invitation_code": invitation_code}
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    print("✅ Successfully registered!")
                    print(f"\nGuardian Details:")
                    print(f"  Guardian ID: {result['guardian_id']}")
                    print(f"  Vault ID: {result['vault_id']}")
                    print(f"  Status: {result['status']}")
                    print(f"\nSave these IDs for connecting to the server.")
                    return result
                else:
                    error = await response.text()
                    print(f"❌ Registration failed: {error}")
                    return None
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None


async def main():
    parser = argparse.ArgumentParser(
        description="Guardian client for participating in MPC signing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Register with invitation code
  python3 cli_guardian_client.py register --server http://localhost:8000 --code INVITE-ABC-123

  # Run guardian client
  python3 cli_guardian_client.py run --server http://localhost:8000 \\
      --share demo_shares/guardian_1_share.json \\
      --guardian-id guard_abc123 \\
      --vault-id vault_xyz789 \\
      --vault-config demo_shares/vault_config.json
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Register command
    register_parser = subparsers.add_parser('register', help='Register with invitation code')
    register_parser.add_argument('--server', '-s', type=str, default='http://localhost:8000',
                                 help='Coordination server URL')
    register_parser.add_argument('--code', '-c', type=str, required=True,
                                 help='Invitation code')

    # Run command
    run_parser = subparsers.add_parser('run', help='Run guardian client')
    run_parser.add_argument('--server', '-s', type=str, default='http://localhost:8000',
                           help='Coordination server URL')
    run_parser.add_argument('--share', type=str, required=True,
                           help='Path to guardian share file')
    run_parser.add_argument('--guardian-id', '-g', type=str, required=True,
                           help='Guardian ID from registration')
    run_parser.add_argument('--vault-id', '-v', type=str, required=True,
                           help='Vault ID')
    run_parser.add_argument('--vault-config', '-c', type=str, required=True,
                           help='Path to vault configuration file (needed for account derivation)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'register':
            await register_guardian(args.server, args.code)
        elif args.command == 'run':
            client = GuardianClient(
                server_url=args.server,
                share_file=args.share,
                guardian_id=args.guardian_id,
                vault_id=args.vault_id,
                vault_config=args.vault_config
            )
            await client.run()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
