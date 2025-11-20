#!/usr/bin/env python3
"""
Complete FROST Workflow Demonstration
3-of-5 Threshold Schnorr Signatures for Bitcoin/Ethereum

KEY FEATURES:
- k-of-n threshold (any 3 of 5 guardians can sign)
- Private key NEVER reconstructed
- Schnorr signatures (Bitcoin Taproot BIP340 compatible)
- 2-round signing protocol (more efficient than 4-round ECDSA)
"""

import json
import secrets
from typing import List, Dict

from guardianvault.threshold_frost import (
    FrostKeyGeneration,
    FrostKeyShare,
    FrostPublicKeyPackage,
    FrostWorkflow,
    FrostCoordinator
)


class Guardian:
    """Represents one guardian in the 3-of-5 system"""

    def __init__(self, guardian_id: int, name: str):
        self.guardian_id = guardian_id
        self.name = name
        self.key_share: FrostKeyShare = None

    def receive_key_share(self, share: FrostKeyShare):
        """Receive key share during setup"""
        self.key_share = share
        print(f"  [{self.name}] Received key share (Participant {share.participant_id})")

    def save_share(self, directory: str = "."):
        """Save share to secure storage (simulated)"""
        filename = f"{directory}/frost_guardian_{self.guardian_id}_share.json"
        data = {
            'guardian_id': self.guardian_id,
            'name': self.name,
            'participant_id': self.key_share.participant_id,
            'secret_share': hex(self.key_share.secret_share),
            'threshold': self.key_share.threshold,
            'max_participants': self.key_share.max_participants
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  [{self.name}] Saved share to {filename}")


def phase1_setup():
    """
    Phase 1: One-time setup with trusted dealer
    Creates 3-of-5 threshold scheme
    """
    print("=" * 80)
    print("PHASE 1: SETUP - 3-of-5 THRESHOLD SCHEME")
    print("=" * 80)
    print()

    # Create 5 guardians
    guardians = [
        Guardian(1, "Alice"),
        Guardian(2, "Bob"),
        Guardian(3, "Charlie"),
        Guardian(4, "Diana"),
        Guardian(5, "Eve")
    ]

    print("Guardians:")
    for guardian in guardians:
        print(f"  {guardian.guardian_id}. {guardian.name}")
    print()

    # Generate FROST key shares (3-of-5)
    print("Step 1: Generate FROST key shares (Trusted Dealer)")
    print("-" * 80)
    threshold = 3
    max_participants = 5

    key_shares, public_key_package = FrostKeyGeneration.trusted_dealer_keygen(
        threshold, max_participants
    )

    print(f"✓ Generated {len(key_shares)} key shares")
    print(f"✓ Threshold: {threshold}-of-{max_participants}")
    print(f"✓ Group public key: {public_key_package.serialize_group_pubkey().hex()[:32]}...")
    print()

    # Distribute shares to guardians
    print("Step 2: Distribute shares to guardians")
    print("-" * 80)
    for i, guardian in enumerate(guardians):
        guardian.receive_key_share(key_shares[i])
    print()

    # Verify all shares
    print("Step 3: Verify shares")
    print("-" * 80)
    for guardian in guardians:
        valid = FrostKeyGeneration.verify_share(
            guardian.key_share,
            public_key_package
        )
        status = "✓ Valid" if valid else "✗ Invalid"
        print(f"  [{guardian.name}] Share verification: {status}")
    print()

    # Save shares to secure storage
    print("Step 4: Save shares to secure storage")
    print("-" * 80)
    for guardian in guardians:
        guardian.save_share()
    print()

    print("✓ Setup complete!")
    print(f"✓ Any {threshold} guardians can now sign transactions")
    print(f"✓ Group public key can be used to generate addresses")
    print()

    return guardians, public_key_package


def phase2_address_generation(public_key_package: FrostPublicKeyPackage):
    """
    Phase 2: Generate addresses from group public key
    Note: FROST doesn't support hierarchical derivation like BIP32
    This demo shows basic address generation
    """
    print("=" * 80)
    print("PHASE 2: ADDRESS GENERATION")
    print("=" * 80)
    print()

    print("Group Public Key (for address generation):")
    print("-" * 80)
    group_pubkey_bytes = public_key_package.serialize_group_pubkey()
    print(f"  Compressed: {group_pubkey_bytes.hex()}")
    print()

    print("Note: For production use, you would:")
    print("  1. Use this public key with BIP340 (Taproot) for Bitcoin")
    print("  2. Derive addresses using standard methods")
    print("  3. Store the group public key for verification")
    print()

    # For demonstration: show how to derive Bitcoin Taproot address
    # (simplified - production would use proper BIP340 encoding)
    import hashlib
    pubkey_hash = hashlib.sha256(group_pubkey_bytes).digest()
    print(f"Example Bitcoin Taproot key hash: {pubkey_hash.hex()[:32]}...")
    print()

    return group_pubkey_bytes


def phase3_transaction_signing(
    guardians: List[Guardian],
    public_key_package: FrostPublicKeyPackage
):
    """
    Phase 3: Sign transaction with 3 of 5 guardians
    Demonstrates flexible threshold signing
    """
    print("=" * 80)
    print("PHASE 3: TRANSACTION SIGNING (3-of-5 Threshold)")
    print("=" * 80)
    print()

    # Scenario: Need to sign a Bitcoin transaction
    # Select 3 guardians (Alice, Charlie, Eve)
    print("Scenario: Sign Bitcoin transaction")
    print("-" * 80)
    print("Transaction: Send 0.5 BTC from treasury to recipient")
    print()

    selected_guardians = [guardians[0], guardians[2], guardians[4]]  # Alice, Charlie, Eve
    print(f"Selected guardians ({len(selected_guardians)} of {len(guardians)}):")
    for g in selected_guardians:
        print(f"  • {g.name} (Participant {g.key_share.participant_id})")
    print()

    # Message to sign (transaction hash)
    tx_message = b"Bitcoin TX: Send 0.5 BTC to bc1q... [txid: abc123...]"
    print(f"Message to sign: {tx_message.decode()}")
    print()

    # Gather key shares
    print("Gathering key shares from selected guardians...")
    print("-" * 80)
    selected_shares = []
    for guardian in selected_guardians:
        selected_shares.append(guardian.key_share)
        print(f"  [{guardian.name}] Providing key share")
    print()

    # Execute FROST signing protocol
    print("Executing 2-round FROST signing protocol...")
    print()

    R_bytes, z = FrostWorkflow.sign_message(
        selected_shares,
        tx_message,
        public_key_package
    )

    print("=" * 80)
    print("TRANSACTION SIGNED!")
    print(f"  Schnorr Signature (R, z):")
    print(f"    R: {R_bytes.hex()}")
    print(f"    z: {hex(z)}")
    print()
    print("✓ Transaction ready to broadcast")
    print("✓ Private key was NEVER reconstructed")
    print("✓ Only 3 of 5 guardians needed")
    print("=" * 80)
    print()

    return R_bytes, z


def phase4_different_signers(
    guardians: List[Guardian],
    public_key_package: FrostPublicKeyPackage
):
    """
    Phase 4: Sign with different set of guardians
    Demonstrates flexibility - any 3 can sign
    """
    print("=" * 80)
    print("PHASE 4: SIGNING WITH DIFFERENT GUARDIANS")
    print("=" * 80)
    print()

    # Now use Bob, Diana, Eve instead
    selected_guardians = [guardians[1], guardians[3], guardians[4]]  # Bob, Diana, Eve
    print(f"New signing group ({len(selected_guardians)} of {len(guardians)}):")
    for g in selected_guardians:
        print(f"  • {g.name} (Participant {g.key_share.participant_id})")
    print()

    # Different transaction
    tx_message = b"Ethereum TX: Transfer 10 ETH to 0x123... [nonce: 42]"
    print(f"Message to sign: {tx_message.decode()}")
    print()

    # Gather shares
    selected_shares = [g.key_share for g in selected_guardians]

    # Sign
    R_bytes, z = FrostWorkflow.sign_message(
        selected_shares,
        tx_message,
        public_key_package
    )

    print("=" * 80)
    print("SUCCESS WITH DIFFERENT SIGNERS!")
    print(f"  Signature: R={R_bytes.hex()[:32]}..., z={hex(z)[:32]}...")
    print()
    print("✓ Same group public key, different signers")
    print("✓ Demonstrates true k-of-n threshold flexibility")
    print("=" * 80)
    print()


def main():
    """Run complete FROST workflow demonstration"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + " " * 23 + "FROST THRESHOLD SIGNATURES" + " " * 29 + "║")
    print("║" + " " * 26 + "3-of-5 Demonstration" + " " * 32 + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  Schnorr Signatures • k-of-n Threshold • Never Reconstruct Key" + " " * 13 + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    # Phase 1: Setup
    guardians, public_key_package = phase1_setup()

    input("Press Enter to continue to address generation...")
    print("\n")

    # Phase 2: Address generation
    group_pubkey = phase2_address_generation(public_key_package)

    input("Press Enter to continue to transaction signing...")
    print("\n")

    # Phase 3: Sign transaction (Alice, Charlie, Eve)
    phase3_transaction_signing(guardians, public_key_package)

    input("Press Enter to sign with different guardians...")
    print("\n")

    # Phase 4: Sign with different guardians (Bob, Diana, Eve)
    phase4_different_signers(guardians, public_key_package)

    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + " " * 30 + "WORKFLOW COMPLETE!" + " " * 29 + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  Summary:" + " " * 67 + "║")
    print("║" + "  ✓ Setup: Generated 3-of-5 threshold key shares" + " " * 29 + "║")
    print("║" + "  ✓ Flexibility: ANY 3 guardians can sign" + " " * 36 + "║")
    print("║" + "  ✓ Efficiency: 2-round signing protocol" + " " * 38 + "║")
    print("║" + "  ✓ Security: Private key NEVER reconstructed" + " " * 32 + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  🔐 Advantages over ECDSA Threshold:" + " " * 43 + "║")
    print("║" + "     - TRUE k-of-n threshold (not just t-of-t)" + " " * 32 + "║")
    print("║" + "     - More efficient (2 rounds vs 4 rounds)" + " " * 34 + "║")
    print("║" + "     - Bitcoin Taproot (BIP340) compatible" + " " * 36 + "║")
    print("║" + "     - Provably secure Schnorr signatures" + " " * 36 + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  📊 Comparison to Existing Implementation:" + " " * 35 + "║")
    print("║" + "     - Shamir's SSS: Key temporarily reconstructed" + " " * 29 + "║")
    print("║" + "     - Threshold ECDSA: Requires ALL parties (5-of-5)" + " " * 25 + "║")
    print("║" + "     - FROST: Best of both worlds! (3-of-5, never reconstruct)" + " " * 17 + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")


if __name__ == "__main__":
    main()