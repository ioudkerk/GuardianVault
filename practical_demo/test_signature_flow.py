#!/usr/bin/env python3
"""
Test Complete Signature Flow
Simulate the entire MPC signing process locally to verify correctness
"""
import sys
import os
import json
import hashlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardianvault.threshold_mpc_keymanager import (
    KeyShare,
    ThresholdBIP32,
    ExtendedPublicKey,
    PublicKeyDerivation,
    EllipticCurvePoint,
    SECP256K1_N
)
from guardianvault.threshold_signing import ThresholdSigner, ThresholdSignature


def derive_address_share(account_share, account_xpub, address_index, total_parties):
    """
    Derive address-level share from account share using non-hardened derivation

    Args:
        account_share: Account-level share (m/44'/0'/0')
        account_xpub: Account-level extended public key
        address_index: Address index to derive
        total_parties: Total number of parties (for tweak/n calculation)

    Returns:
        (address_share, address_pubkey)
    """
    import hmac

    # Step 1: Derive change share (m/44'/0'/0'/0) - non-hardened
    # Get change public key
    change_pubkey, change_chain = PublicKeyDerivation.derive_public_child(account_xpub, 0)

    # Compute tweak
    data = account_xpub.public_key + (0).to_bytes(4, 'big')
    hmac_result = hmac.new(account_xpub.chain_code, data, hashlib.sha512).digest()
    tweak = int.from_bytes(hmac_result[:32], 'big') % SECP256K1_N

    # Each party adds tweak/n
    tweak_share = (tweak * pow(total_parties, -1, SECP256K1_N)) % SECP256K1_N
    account_int = int.from_bytes(account_share.share_value, 'big')
    change_int = (account_int + tweak_share) % SECP256K1_N

    # Step 2: Derive address share (m/44'/0'/0'/0/address_index) - non-hardened
    change_xpub = ExtendedPublicKey(change_pubkey, change_chain, account_xpub.depth + 1, b'\x00'*4, 0)
    address_pubkey, _ = PublicKeyDerivation.derive_public_child(change_xpub, address_index)

    # Compute tweak for address
    data = change_pubkey + address_index.to_bytes(4, 'big')
    hmac_result = hmac.new(change_chain, data, hashlib.sha512).digest()
    tweak = int.from_bytes(hmac_result[:32], 'big') % SECP256K1_N

    # Each party adds tweak/n
    tweak_share = (tweak * pow(total_parties, -1, SECP256K1_N)) % SECP256K1_N
    address_int = (change_int + tweak_share) % SECP256K1_N

    address_share = KeyShare(
        party_id=account_share.party_id,
        share_value=address_int.to_bytes(32, 'big'),
        total_parties=account_share.total_parties,
        threshold=account_share.threshold,
        metadata={'derived': True}
    )

    return address_share, address_pubkey


def test_signature_flow(vault_config_file: str, share_files: list, address_index: int = 0):
    """Test complete MPC signature flow"""

    print("="*70)
    print("TESTING COMPLETE MPC SIGNATURE FLOW")
    print("="*70)

    # Load vault config and shares
    with open(vault_config_file, 'r') as f:
        vault_config = json.load(f)

    account_xpub = ExtendedPublicKey.from_dict(vault_config['bitcoin']['xpub'])

    # Load account-level shares (m/44'/0'/0')
    account_shares = []
    for share_file in share_files:
        with open(share_file, 'r') as f:
            share_data = json.load(f)
            # Support both old (master) and new (account) format
            if 'bitcoin_account_share' in share_data:
                share = KeyShare.from_dict(share_data['bitcoin_account_share'])
            elif 'share' in share_data:
                raise ValueError("Old master share format detected! Please regenerate shares with updated share generator.")
            else:
                raise ValueError("Share file missing 'bitcoin_account_share' field")
            account_shares.append(share)

    print(f"\nLoaded {len(account_shares)} guardian account shares (m/44'/0'/0')")
    total_parties = len(account_shares)

    # Derive address-level shares for all guardians
    print(f"\nDeriving address-level shares (m/44'/0'/0'/0/{address_index})...")
    address_shares = []
    address_pubkey = None

    for i, account_share in enumerate(account_shares, 1):
        addr_share, addr_pub = derive_address_share(
            account_share, account_xpub, address_index, total_parties
        )
        address_shares.append(addr_share)
        address_pubkey = addr_pub
        print(f"  Guardian {i}: {addr_share.share_value.hex()[:32]}...")

    # Verify derived shares sum to correct private key
    print(f"\nVerifying derived shares...")
    total_key = sum(int.from_bytes(s.share_value, 'big') for s in address_shares) % SECP256K1_N
    G = EllipticCurvePoint.generator()
    computed_pubkey = (G * total_key).to_bytes(compressed=True)

    print(f"  Sum of shares: {hex(total_key)[:32]}...")
    print(f"  Computed pubkey: {computed_pubkey.hex()[:32]}...")
    print(f"  Expected pubkey: {address_pubkey.hex()[:32]}...")
    print(f"  Match: {computed_pubkey == address_pubkey}")

    if computed_pubkey != address_pubkey:
        print("\n❌ Derived shares don't sum correctly!")
        return False

    # Create a test message to sign
    message = b"Test Bitcoin transaction"
    message_hash = hashlib.sha256(hashlib.sha256(message).digest()).digest()

    print(f"\nTest message: {message}")
    print(f"Message hash: {message_hash.hex()[:32]}...")

    # Round 1: Each guardian generates nonce
    print(f"\n{'='*70}")
    print("ROUND 1: Nonce Generation")
    print(f"{'='*70}")

    nonce_shares = []
    r_points = []

    for i, share in enumerate(address_shares, 1):
        nonce, r_point = ThresholdSigner.sign_round1_generate_nonce(share.party_id)
        nonce_shares.append(nonce)
        r_points.append(r_point)
        print(f"Guardian {i}:")
        print(f"  Nonce: {hex(nonce)[:32]}...")
        print(f"  R point: {r_point.hex()[:32]}...")

    # Round 2: Combine R points
    print(f"\n{'='*70}")
    print("ROUND 2: Combine R Points")
    print(f"{'='*70}")

    R_combined, r = ThresholdSigner.sign_round2_combine_nonces(r_points)
    k_total = sum(nonce_shares) % SECP256K1_N

    print(f"  Combined R: ({hex(R_combined.x)[:20]}..., {hex(R_combined.y)[:20]}...)")
    print(f"  r value: {hex(r)[:32]}...")
    print(f"  k_total: {hex(k_total)[:32]}...")

    # Verify R = k_total * G
    R_from_k = G * k_total
    print(f"  R from k: ({hex(R_from_k.x)[:20]}..., {hex(R_from_k.y)[:20]}...)")
    print(f"  Match: {R_from_k.x == R_combined.x and R_from_k.y == R_combined.y}")

    if R_from_k.x != R_combined.x or R_from_k.y != R_combined.y:
        print("\n❌ R point mismatch!")
        return False

    # Round 3: Each guardian computes signature share
    print(f"\n{'='*70}")
    print("ROUND 3: Compute Signature Shares")
    print(f"{'='*70}")

    s_shares = []

    for i, (share, nonce) in enumerate(zip(address_shares, nonce_shares), 1):
        s_i = ThresholdSigner.sign_round3_compute_signature_share(
            key_share=share,
            nonce_share=nonce,
            message_hash=message_hash,
            r=r,
            k_total=k_total,
            num_parties=total_parties
        )
        s_shares.append(s_i)
        print(f"Guardian {i}:")
        print(f"  s_i: {hex(s_i)[:32]}...")

    # Round 4: Combine signature shares
    print(f"\n{'='*70}")
    print("ROUND 4: Combine Signature Shares")
    print(f"{'='*70}")

    signature = ThresholdSigner.sign_round4_combine_signatures(s_shares, r)

    print(f"  Final signature:")
    print(f"    r: {hex(signature.r)[:32]}...")
    print(f"    s: {hex(signature.s)[:32]}...")

    # Verify signature
    print(f"\n{'='*70}")
    print("VERIFICATION")
    print(f"{'='*70}")

    valid = ThresholdSigner.verify_signature(address_pubkey, message_hash, signature)

    print(f"  Message hash: {message_hash.hex()[:32]}...")
    print(f"  Public key: {address_pubkey.hex()[:32]}...")
    print(f"  Signature (r, s): ({hex(signature.r)[:32]}..., {hex(signature.s)[:32]}...)")
    print(f"  ✓ Valid: {valid}")

    if not valid:
        print("\n❌ SIGNATURE VERIFICATION FAILED!")
        return False

    print(f"\n{'='*70}")
    print("✅ SUCCESS! MPC SIGNATURE IS VALID!")
    print(f"{'='*70}")
    print("\nAll steps:")
    print("  ✅ Key derivation correct (shares sum to private key)")
    print("  ✅ Nonce generation correct")
    print("  ✅ R point combination correct")
    print("  ✅ Signature shares correct")
    print("  ✅ Final signature valid")
    print("\nThe guardian clients should now produce valid signatures!")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test MPC signature flow")
    parser.add_argument('--vault-config', '-c', required=True)
    parser.add_argument('--shares', nargs='+', required=True)
    parser.add_argument('--address-index', '-a', type=int, default=0)

    args = parser.parse_args()

    try:
        success = test_signature_flow(args.vault_config, args.shares, args.address_index)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
