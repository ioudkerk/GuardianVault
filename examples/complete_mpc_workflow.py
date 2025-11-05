#!/usr/bin/env python3
"""
Complete MPC Workflow Demonstration
Shows the full lifecycle: Setup → Address Generation → Transaction Signing

KEY FEATURE: Private key is NEVER reconstructed at any point!
"""

import secrets
import json
from typing import List, Dict

from guardianvault.threshold_mpc_keymanager import (
    ThresholdKeyGeneration,
    ThresholdBIP32,
    ExtendedPublicKey,
    KeyShare,
    save_xpub_to_file,
    load_xpub_from_file
)
from guardianvault.threshold_addresses import (
    BitcoinAddressGenerator,
    EthereumAddressGenerator
)
from guardianvault.threshold_signing import (
    ThresholdSigningWorkflow
)


class MPCParty:
    """Represents one party in the MPC system"""

    def __init__(self, party_id: int, name: str):
        self.party_id = party_id
        self.name = name
        self.key_share: KeyShare = None
        self.master_shares: Dict[str, KeyShare] = {}  # coin_type -> share

    def receive_key_share(self, share: KeyShare):
        """Receive initial key share"""
        self.key_share = share
        print(f"  [{self.name}] Received key share {share.party_id}")

    def receive_master_share(self, coin_type: str, share: KeyShare):
        """Receive master key share for specific coin"""
        self.master_shares[coin_type] = share
        print(f"  [{self.name}] Received {coin_type} master share")

    def save_shares(self, directory: str = "."):
        """Save shares to secure storage (simulated)"""
        filename = f"{directory}/party_{self.party_id}_shares.json"
        data = {
            'party_id': self.party_id,
            'name': self.name,
            'key_share': self.key_share.to_dict() if self.key_share else None,
            'master_shares': {
                coin: share.to_dict()
                for coin, share in self.master_shares.items()
            }
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  [{self.name}] Saved shares to {filename}")


def simulate_async_setup():
    """
    Phase 1: One-time setup with threshold computation
    This is the ONLY time parties need to interact for key derivation
    """
    print("=" * 80)
    print("PHASE 1: ONE-TIME SETUP (Threshold Computation Required)")
    print("=" * 80)
    print()

    # Create parties
    parties = [
        MPCParty(1, "Alice"),
        MPCParty(2, "Bob"),
        MPCParty(3, "Charlie")
    ]

    print("Parties:")
    for party in parties:
        print(f"  {party.party_id}. {party.name}")
    print()

    # Step 1: Generate initial key shares
    print("Step 1: Generate distributed key shares")
    print("-" * 80)
    num_parties = len(parties)
    key_shares, master_pubkey = ThresholdKeyGeneration.generate_shares(num_parties)

    for i, party in enumerate(parties):
        party.receive_key_share(key_shares[i])
    print()

    # Step 2: Derive master keys (simulating async communication)
    print("Step 2: Derive BIP32 master keys (threshold computation)")
    print("-" * 80)
    seed = secrets.token_bytes(32)
    print(f"Using seed: {seed.hex()[:32]}...")

    master_shares, master_pubkey, master_chain = \
        ThresholdBIP32.derive_master_keys_threshold(key_shares, seed)

    print(f"✓ Master public key: {master_pubkey.hex()[:32]}...")
    print()

    # Step 3: Derive Bitcoin account xpub (threshold computation)
    print("Step 3: Derive Bitcoin account xpub m/44'/0'/0' (threshold)")
    print("-" * 80)
    btc_xpub = ThresholdBIP32.derive_account_xpub_threshold(
        master_shares, master_chain, coin_type=0, account=0
    )
    print(f"✓ Bitcoin xpub derived")
    print(f"  Public key: {btc_xpub.public_key.hex()[:32]}...")

    # Save xpub (public, can be shared)
    save_xpub_to_file(btc_xpub, "bitcoin_account_0.xpub")
    print(f"✓ Saved to bitcoin_account_0.xpub")
    print()

    # Step 4: Derive Ethereum account xpub (threshold computation)
    print("Step 4: Derive Ethereum account xpub m/44'/60'/0' (threshold)")
    print("-" * 80)
    eth_xpub = ThresholdBIP32.derive_account_xpub_threshold(
        master_shares, master_chain, coin_type=60, account=0
    )
    print(f"✓ Ethereum xpub derived")
    print(f"  Public key: {eth_xpub.public_key.hex()[:32]}...")

    save_xpub_to_file(eth_xpub, "ethereum_account_0.xpub")
    print(f"✓ Saved to ethereum_account_0.xpub")
    print()

    # Step 5: Distribute account-level shares to parties
    print("Step 5: Distribute shares to parties")
    print("-" * 80)

    # For Bitcoin account
    btc_account_shares, _, _ = ThresholdBIP32.derive_hardened_child_threshold(
        master_shares, master_pubkey, master_chain, 44
    )
    btc_account_shares, _, _ = ThresholdBIP32.derive_hardened_child_threshold(
        btc_account_shares, None, _, 0
    )
    btc_account_shares, _, _ = ThresholdBIP32.derive_hardened_child_threshold(
        btc_account_shares, None, _, 0
    )

    for i, party in enumerate(parties):
        party.receive_master_share("bitcoin", btc_account_shares[i])

    # For Ethereum account
    eth_account_shares, _, _ = ThresholdBIP32.derive_hardened_child_threshold(
        master_shares, master_pubkey, master_chain, 44
    )
    eth_account_shares, _, _ = ThresholdBIP32.derive_hardened_child_threshold(
        eth_account_shares, None, _, 60
    )
    eth_account_shares, _, _ = ThresholdBIP32.derive_hardened_child_threshold(
        eth_account_shares, None, _, 0
    )

    for i, party in enumerate(parties):
        party.receive_master_share("ethereum", eth_account_shares[i])

    print()

    # Step 6: Parties save their shares securely
    print("Step 6: Parties save shares to secure storage")
    print("-" * 80)
    for party in parties:
        party.save_shares()
    print()

    print("✓ Setup complete! Each party has their private shares.")
    print("✓ Account xpubs are available for address generation.")
    print()

    return parties, btc_xpub, eth_xpub


def simulate_address_generation(btc_xpub: ExtendedPublicKey, eth_xpub: ExtendedPublicKey):
    """
    Phase 2: Generate unlimited addresses (NO threshold computation!)
    Anyone with the xpub can do this - no private keys needed!
    """
    print("=" * 80)
    print("PHASE 2: ADDRESS GENERATION (NO Threshold Computation!)")
    print("=" * 80)
    print()

    print("This can be done by ANYONE with the xpub")
    print("No private keys required!")
    print("No communication with parties needed!")
    print()

    # Generate Bitcoin addresses
    print("Bitcoin Receiving Addresses:")
    print("-" * 80)
    btc_addresses = BitcoinAddressGenerator.generate_addresses_from_xpub(
        btc_xpub, change=0, start_index=0, count=5
    )

    for addr in btc_addresses:
        print(f"  {addr['path']}: {addr['address']}")
    print()

    # Generate Ethereum addresses
    print("Ethereum Receiving Addresses:")
    print("-" * 80)
    eth_addresses = EthereumAddressGenerator.generate_addresses_from_xpub(
        eth_xpub, change=0, start_index=0, count=5
    )

    for addr in eth_addresses:
        print(f"  {addr['path']}: {addr['address']}")
    print()

    print("✓ Generated 10 addresses total")
    print("✓ Can generate UNLIMITED more without any threshold computation")
    print()

    return btc_addresses[0]  # Return first address for signing demo


def simulate_transaction_signing(parties: List[MPCParty], address_info: Dict):
    """
    Phase 3: Sign transaction (threshold computation required)
    Parties collaborate to sign WITHOUT reconstructing private key
    """
    print("=" * 80)
    print("PHASE 3: TRANSACTION SIGNING (Threshold Computation)")
    print("=" * 80)
    print()

    print(f"Scenario: Spend funds from {address_info['address']}")
    print(f"Path: {address_info['path']}")
    print()

    # Create transaction message (simplified)
    message = f"Send 0.5 BTC from {address_info['address']} to recipient_address"
    print(f"Transaction: {message}")
    print()

    # Gather Bitcoin account shares from parties
    print("Gathering shares from parties...")
    print("-" * 80)
    bitcoin_shares = []
    for party in parties:
        bitcoin_share = party.master_shares.get("bitcoin")
        if bitcoin_share:
            bitcoin_shares.append(bitcoin_share)
            print(f"  [{party.name}] Providing Bitcoin account share")
    print()

    # Get public key for the address
    # (In real implementation, derive from path)
    public_key = bytes.fromhex(address_info['public_key'])

    # Sign using threshold protocol
    print("Executing threshold signing protocol...")
    print()

    signature = ThresholdSigningWorkflow.sign_message(
        bitcoin_shares,
        message.encode('utf-8'),
        public_key
    )

    print("=" * 80)
    print("TRANSACTION SIGNED!")
    print(f"  Signature (DER): {signature.to_der().hex()[:64]}...")
    print(f"  Signature (Compact): {signature.to_compact().hex()[:64]}...")
    print()
    print("✓ Transaction can now be broadcast to the network")
    print("✓ Private key was NEVER reconstructed")
    print("=" * 80)


def main():
    """Run complete MPC workflow demonstration"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + " " * 20 + "COMPLETE MPC WORKFLOW DEMONSTRATION" + " " * 23 + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  Private Key NEVER Reconstructed - Unlimited Addresses - Secure Signing  " + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    # Phase 1: Setup (one-time, threshold required)
    parties, btc_xpub, eth_xpub = simulate_async_setup()

    input("Press Enter to continue to address generation...")
    print("\n")

    # Phase 2: Address generation (unlimited, no threshold)
    first_btc_address = simulate_address_generation(btc_xpub, eth_xpub)

    input("Press Enter to continue to transaction signing...")
    print("\n")

    # Phase 3: Transaction signing (threshold required)
    simulate_transaction_signing(parties, first_btc_address)

    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + " " * 30 + "WORKFLOW COMPLETE!" + " " * 29 + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  Summary:" + " " * 67 + "║")
    print("║" + "  ✓ Setup: ONE-TIME threshold computation for account xpubs" + " " * 18 + "║")
    print("║" + "  ✓ Addresses: UNLIMITED generation with no threshold computation" + " " * 13 + "║")
    print("║" + "  ✓ Signing: Threshold computation WITHOUT private key reconstruction" + " " * 7 + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  🔐 Security Achievement:" + " " * 52 + "║")
    print("║" + "     - Private key shares NEVER combined" + " " * 37 + "║")
    print("║" + "     - Each party only uses their secret share" + " " * 32 + "║")
    print("║" + "     - Unlimited addresses from public xpub" + " " * 35 + "║")
    print("║" + "     - Signatures created through MPC protocol" + " " * 32 + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")


if __name__ == "__main__":
    main()
