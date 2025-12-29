#!/usr/bin/env python3
"""
Verify Account-Level Shares
Check if the account shares are correct additive shares
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardianvault.mpc_keymanager import (
    KeyShare,
    MPCBIP32,
    ExtendedPublicKey,
    EllipticCurvePoint,
    SECP256K1_N
)


def verify_account_shares(vault_config_file: str, share_files: list):
    """Verify that account-level shares sum to the correct private key"""

    print("="*70)
    print("ACCOUNT SHARES VERIFICATION")
    print("="*70)

    # Load vault config
    with open(vault_config_file, 'r') as f:
        vault_config = json.load(f)

    master_chain_code = bytes.fromhex(vault_config['master_chain_code'])
    account_xpub = ExtendedPublicKey.from_dict(vault_config['bitcoin']['xpub'])

    print(f"\nAccount xpub (m/44'/0'/0'):")
    print(f"  Public key: {account_xpub.public_key.hex()[:32]}...")
    print(f"  Chain code: {account_xpub.chain_code.hex()[:32]}...")

    # Load guardian account shares
    print(f"\nLoading {len(share_files)} account shares...")
    account_shares_loaded = []
    for i, share_file in enumerate(share_files, 1):
        with open(share_file, 'r') as f:
            share_data = json.load(f)
            # Support new account share format
            if 'bitcoin_account_share' in share_data:
                share = KeyShare.from_dict(share_data['bitcoin_account_share'])
                print(f"  Guardian {i}: {share.share_value.hex()[:32]}... (account level)")
            else:
                raise ValueError("Old share format detected. Please regenerate shares!")
            account_shares_loaded.append(share)

    # Verify these account shares are correct
    print(f"\nNote: These are account-level shares (m/44'/0'/0'), not master shares.")
    print(f"      They should already sum to the correct account public key.")

    # Test: Verify account shares sum to correct public key
    print(f"\nTest: Verifying account shares sum correctly...")

    G = EllipticCurvePoint.generator()
    account_sum = sum(int.from_bytes(s.share_value, 'big') for s in account_shares_loaded) % SECP256K1_N
    account_pub_computed = (G * account_sum).to_bytes(compressed=True)

    print(f"  Guardian 1: {account_shares_loaded[0].share_value.hex()[:32]}...")
    if len(account_shares_loaded) > 1:
        print(f"  Guardian 2: {account_shares_loaded[1].share_value.hex()[:32]}...")
    if len(account_shares_loaded) > 2:
        print(f"  Guardian 3: {account_shares_loaded[2].share_value.hex()[:32]}...")
    print(f"  Sum of shares: {hex(account_sum)[:32]}...")
    print(f"  Computed public key: {account_pub_computed.hex()[:32]}...")
    print(f"  Expected public key: {account_xpub.public_key.hex()[:32]}...")
    print(f"  Match: {account_pub_computed == account_xpub.public_key}")

    if account_pub_computed != account_xpub.public_key:
        print("\n  ❌ Account shares don't sum to correct public key!")
        print("\n  This means the shares are incorrectly generated.")
        return False

    print("\n✅ Account shares are correct!")
    print("   The shares sum to the expected account public key.")

    # Test 2: Non-hardened derivation
    print(f"\nTest 2: Testing non-hardened derivation (m/44'/0'/0'/0)...")

    # Use the PUBLIC derivation
    from guardianvault.mpc_keymanager import PublicKeyDerivation

    change_pub, change_chain = PublicKeyDerivation.derive_public_child(
        account_xpub, 0
    )

    print(f"  Expected change public key: {change_pub.hex()[:32]}...")

    # Now derive change shares with our formula
    import hmac
    import hashlib

    data = account_xpub.public_key + (0).to_bytes(4, 'big')
    hmac_result = hmac.new(account_xpub.chain_code, data, hashlib.sha512).digest()
    tweak = int.from_bytes(hmac_result[:32], 'big') % SECP256K1_N

    print(f"  Tweak: {hex(tweak)[:32]}...")

    # Each guardian adds tweak/n
    n = len(account_shares_loaded)
    tweak_share = (tweak * pow(n, -1, SECP256K1_N)) % SECP256K1_N

    print(f"  Tweak per guardian (tweak/{n}): {hex(tweak_share)[:32]}...")

    change_shares = []
    for i, acc_share in enumerate(account_shares_loaded, 1):
        acc_int = int.from_bytes(acc_share.share_value, 'big')
        change_int = (acc_int + tweak_share) % SECP256K1_N
        change_shares.append(change_int)
        print(f"  Guardian {i} change share: {hex(change_int)[:32]}...")

    # Sum and verify
    change_sum = sum(change_shares) % SECP256K1_N
    change_pub_computed = (G * change_sum).to_bytes(compressed=True)

    print(f"\n  Sum of change shares: {hex(change_sum)[:32]}...")
    print(f"  Computed change public key: {change_pub_computed.hex()[:32]}...")
    print(f"  Expected change public key: {change_pub.hex()[:32]}...")
    print(f"  Match: {change_pub_computed == change_pub}")

    if change_pub_computed != change_pub:
        print("\n  ❌ Non-hardened derivation formula is still wrong!")
        return False

    print("\n✅ Non-hardened derivation is correct!")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Verify account shares")
    parser.add_argument('--vault-config', '-c', required=True)
    parser.add_argument('--shares', nargs='+', required=True)

    args = parser.parse_args()

    try:
        success = verify_account_shares(args.vault_config, args.shares)

        print("\n" + "="*70)
        if success:
            print("✅ ALL TESTS PASSED!")
        else:
            print("❌ TESTS FAILED!")
        print("="*70)

        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
