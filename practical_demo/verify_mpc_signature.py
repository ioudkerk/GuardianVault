#!/usr/bin/env python3
"""
Verify MPC Signature Computation
Debug tool to check each step of the threshold ECDSA signing
"""
import sys
import os
import json
import argparse
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardianvault.mpc_keymanager import ExtendedPublicKey, PublicKeyDerivation, SECP256K1_N, EllipticCurvePoint
from guardianvault.mpc_signing import MPCSigner, ThresholdSignature


def verify_mpc_computation(transaction_id: str, server_url: str, vault_config_file: str, share_files: list):
    """Verify the MPC signature computation step by step"""

    print("="*70)
    print("MPC SIGNATURE VERIFICATION")
    print("="*70)

    # Step 1: Fetch transaction
    print("\nStep 1: Fetching transaction...")
    response = requests.get(f"{server_url}/api/transactions/{transaction_id}")
    if response.status_code != 200:
        print(f"❌ Failed to fetch transaction")
        return False

    tx = response.json()
    print(f"✓ Transaction fetched: {transaction_id}")
    print(f"  Status: {tx['status']}")
    print(f"  Message Hash: {tx['message_hash'][:32]}...")

    # Step 2: Load vault config and shares
    print("\nStep 2: Loading vault config and shares...")
    with open(vault_config_file, 'r') as f:
        vault_config = json.load(f)

    shares = []
    for share_file in share_files:
        with open(share_file, 'r') as f:
            share_data = json.load(f)
            shares.append(share_data)

    print(f"✓ Loaded {len(shares)} guardian shares")

    # Step 3: Get Round 1 data from transaction
    print("\nStep 3: Analyzing Round 1 data...")
    round1_data = tx.get('round1_data', {})
    print(f"  Guardians participated: {len(round1_data)}")

    r_points = []
    nonce_shares = []
    for guardian_id, data in round1_data.items():
        r_point_hex = data['r_point']
        nonce_hex = data['nonce_share']
        r_points.append(bytes.fromhex(r_point_hex))
        nonce_shares.append(int.from_bytes(bytes.fromhex(nonce_hex), 'big'))
        print(f"  {guardian_id}:")
        print(f"    R point: {r_point_hex[:32]}...")
        print(f"    Nonce: {nonce_hex[:32]}...")

    # Step 4: Verify Round 2 computation
    print("\nStep 4: Verifying Round 2 computation...")
    round2_data = tx.get('round2_data', {})

    # Combine R points
    combined_r = EllipticCurvePoint.infinity()
    for r_bytes in r_points:
        r_point = EllipticCurvePoint.from_bytes(r_bytes)
        combined_r = combined_r + r_point

    computed_r = combined_r.x % SECP256K1_N
    stored_r = int(round2_data['r'])

    print(f"  Computed r: {hex(computed_r)[:32]}...")
    print(f"  Stored r:   {hex(stored_r)[:32]}...")
    print(f"  Match: {computed_r == stored_r}")

    # Compute k_total
    k_total_computed = sum(nonce_shares) % SECP256K1_N
    k_total_stored = int(round2_data['kTotal'])

    print(f"  Computed k_total: {hex(k_total_computed)[:32]}...")
    print(f"  Stored k_total:   {hex(k_total_stored)[:32]}...")
    print(f"  Match: {k_total_computed == k_total_stored}")

    # Verify R = k_total * G
    G = EllipticCurvePoint.generator()
    R_from_k = G * k_total_computed
    print(f"  R from k_total: ({hex(R_from_k.x)[:20]}..., {hex(R_from_k.y)[:20]}...)")
    print(f"  Combined R:     ({hex(combined_r.x)[:20]}..., {hex(combined_r.y)[:20]}...)")
    print(f"  Match: {R_from_k.x == combined_r.x and R_from_k.y == combined_r.y}")

    if R_from_k.x != combined_r.x or R_from_k.y != combined_r.y:
        print("  ❌ ERROR: R point mismatch!")
        return False

    # Step 5: Verify Round 3 computation (signature shares)
    print("\nStep 5: Verifying Round 3 signature shares...")
    round3_data = tx.get('round3_data', {})

    # Get address index and derive key shares
    address_index = tx.get('address_index', 0)
    print(f"  Address index: {address_index}")

    # Derive the same shares the guardians would have used
    master_chain_code = bytes.fromhex(vault_config['master_chain_code'])
    xpub = ExtendedPublicKey.from_dict(vault_config['bitcoin']['xpub'])

    message_hash = bytes.fromhex(tx['message_hash'])
    r = stored_r
    k_total = k_total_stored
    z = int.from_bytes(message_hash, 'big')

    print(f"\n  Signature parameters:")
    print(f"    z (message): {hex(z)[:32]}...")
    print(f"    r: {hex(r)[:32]}...")
    print(f"    k_total: {hex(k_total)[:32]}...")

    # Check each guardian's signature share
    total_s = 0
    for guardian_id, data in round3_data.items():
        s_i_stored = int(data['signature_share'])
        total_s = (total_s + s_i_stored) % SECP256K1_N
        print(f"\n  {guardian_id}:")
        print(f"    s_i: {hex(s_i_stored)[:32]}...")

    print(f"\n  Combined s: {hex(total_s)[:32]}...")

    # Apply low-S enforcement
    if total_s > SECP256K1_N // 2:
        print(f"  Applying low-S enforcement...")
        total_s = SECP256K1_N - total_s
        print(f"  New s: {hex(total_s)[:32]}...")

    # Step 6: Verify the final signature
    print("\nStep 6: Verifying final signature...")
    final_sig = tx.get('final_signature', {})
    final_r = int(final_sig['r'])
    final_s = int(final_sig['s'])

    print(f"  Stored r: {hex(final_r)[:32]}...")
    print(f"  Stored s: {hex(final_s)[:32]}...")
    print(f"  r matches: {r == final_r}")
    print(f"  s matches: {total_s == final_s}")

    # Step 7: Manual ECDSA verification
    print("\nStep 7: Manual ECDSA verification...")

    # Get the correct public key
    pubkeys = PublicKeyDerivation.derive_address_public_keys(xpub, change=0, num_addresses=address_index + 1)
    correct_pubkey = pubkeys[address_index]

    print(f"  Public key: {correct_pubkey.hex()[:32]}...")

    signature = ThresholdSignature(r=r, s=total_s)
    valid = MPCSigner.verify_signature(correct_pubkey, message_hash, signature)

    print(f"  ✓ Signature valid: {valid}")

    if not valid:
        print("\n❌ SIGNATURE VERIFICATION FAILED!")
        print("\nDebug: Let me manually verify the ECDSA equation...")

        # Manual verification
        pubkey_point = EllipticCurvePoint.from_bytes(correct_pubkey)

        # Compute w = s^(-1) mod n
        w = pow(total_s, -1, SECP256K1_N)
        print(f"  w = s^(-1): {hex(w)[:32]}...")

        # Compute u1 = z * w mod n
        u1 = (z * w) % SECP256K1_N
        print(f"  u1 = z*w: {hex(u1)[:32]}...")

        # Compute u2 = r * w mod n
        u2 = (r * w) % SECP256K1_N
        print(f"  u2 = r*w: {hex(u2)[:32]}...")

        # Compute P = u1*G + u2*PubKey
        P1 = G * u1
        P2 = pubkey_point * u2
        P = P1 + P2

        print(f"  P = u1*G + u2*Q:")
        print(f"    x: {hex(P.x)[:32]}...")
        print(f"    y: {hex(P.y)[:32]}...")

        # Check if r == P.x mod n
        computed_r = P.x % SECP256K1_N
        print(f"  P.x mod n: {hex(computed_r)[:32]}...")
        print(f"  r:         {hex(r)[:32]}...")
        print(f"  Match: {computed_r == r}")

        # Additional debug: check if the signature equation holds
        print("\n  Checking signature equation: s*k = z + r*x (mod n)")

        # We don't have the actual private key x, but we can check if s*k_total = z + r*x
        # Actually, we can't verify this without the full private key

        return False

    print("\n" + "="*70)
    print("✅ SIGNATURE VERIFICATION PASSED")
    print("="*70)
    return True


def main():
    parser = argparse.ArgumentParser(description="Verify MPC signature computation")
    parser.add_argument('--transaction-id', '-t', required=True, help='Transaction ID')
    parser.add_argument('--server', '-s', default='http://localhost:8000', help='Server URL')
    parser.add_argument('--vault-config', '-c', required=True, help='Vault config file')
    parser.add_argument('--shares', nargs='+', required=True, help='Guardian share files')

    args = parser.parse_args()

    try:
        success = verify_mpc_computation(
            transaction_id=args.transaction_id,
            server_url=args.server,
            vault_config_file=args.vault_config,
            share_files=args.shares
        )

        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
