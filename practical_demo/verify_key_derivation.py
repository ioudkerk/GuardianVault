#!/usr/bin/env python3
"""
Verify Key Derivation Consistency
Check that all guardians derive to the same key level
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardianvault.mpc_keymanager import (
    KeyShare,
    MPCBIP32,
    ExtendedPublicKey,
    PublicKeyDerivation,
    EllipticCurvePoint,
    SECP256K1_N
)


def verify_key_derivation(vault_config_file: str, share_files: list, address_index: int = 0):
    """Verify that derived keys add up correctly"""

    print("="*70)
    print("KEY DERIVATION VERIFICATION")
    print("="*70)

    # Load vault config
    with open(vault_config_file, 'r') as f:
        vault_config = json.load(f)

    master_chain_code = bytes.fromhex(vault_config['master_chain_code'])
    xpub = ExtendedPublicKey.from_dict(vault_config['bitcoin']['xpub'])

    print(f"\nVault: {vault_config.get('name', 'Unknown')}")
    print(f"Master chain code: {master_chain_code.hex()[:32]}...")
    print(f"Account xpub: {xpub.public_key.hex()[:32]}...")

    # Load guardian account shares
    print(f"\nLoading {len(share_files)} guardian account shares...")
    account_shares_list = []
    for i, share_file in enumerate(share_files, 1):
        with open(share_file, 'r') as f:
            share_data = json.load(f)
            # Support new account share format
            if 'bitcoin_account_share' in share_data:
                share = KeyShare.from_dict(share_data['bitcoin_account_share'])
                print(f"  Guardian {i}: Party {share.party_id} (account level)")
            else:
                raise ValueError("Old share format detected. Please regenerate shares!")
            account_shares_list.append(share)

    # Shares are already at account level (m/44'/0'/0')
    print(f"\nNote: Shares are already at account level (m/44'/0'/0')")
    print(f"      No hardened derivation needed, proceeding to non-hardened derivation...")

    # Store account shares with chain code
    account_shares = [(s, xpub.chain_code) for s in account_shares_list]

    for i, (acc_share, _) in enumerate(account_shares, 1):
        print(f"  Guardian {i}: {acc_share.share_value.hex()[:32]}...")

    # Derive address-level shares (m/44'/0'/0'/0/address_index)
    print(f"\nDeriving address shares (m/44'/0'/0'/0/{address_index})...")

    def derive_non_hardened_child_share(parent_share, parent_pubkey, parent_chain, index, total_parties):
        """Derive non-hardened child with correct additive secret sharing"""
        import hmac
        import hashlib

        if index >= 0x80000000:
            raise ValueError("Must be non-hardened")

        data = parent_pubkey + index.to_bytes(4, 'big')
        hmac_result = hmac.new(parent_chain, data, hashlib.sha512).digest()
        tweak = int.from_bytes(hmac_result[:32], 'big') % SECP256K1_N

        # For additive secret sharing: each party adds tweak/n
        tweak_share = (tweak * pow(total_parties, -1, SECP256K1_N)) % SECP256K1_N

        parent_int = int.from_bytes(parent_share.share_value, 'big')
        child_int = (parent_int + tweak_share) % SECP256K1_N

        return KeyShare(
            party_id=parent_share.party_id,
            share_value=child_int.to_bytes(32, 'big'),
            total_parties=parent_share.total_parties,
            threshold=parent_share.threshold,
            metadata={'derived': True}
        )

    # Derive change level (0) for all guardians
    change_pubkey, change_chain = PublicKeyDerivation.derive_public_child(xpub, 0)
    change_xpub = ExtendedPublicKey(change_pubkey, change_chain, xpub.depth + 1, b'\x00'*4, 0)

    total_parties = len(account_shares_list)
    change_shares = []
    for i, (acc_share, acc_chain) in enumerate(account_shares, 1):
        change_share = derive_non_hardened_child_share(
            acc_share, xpub.public_key, xpub.chain_code, 0, total_parties
        )
        change_shares.append(change_share)
        print(f"  Guardian {i} change share: {change_share.share_value.hex()[:32]}...")

    # Derive address level (address_index) for all guardians
    address_pubkey, _ = PublicKeyDerivation.derive_public_child(change_xpub, address_index)

    address_shares = []
    for i, change_share in enumerate(change_shares, 1):
        address_share = derive_non_hardened_child_share(
            change_share, change_pubkey, change_chain, address_index, total_parties
        )
        address_shares.append(address_share)
        print(f"  Guardian {i} address share: {address_share.share_value.hex()[:32]}...")

    # Verify: Sum of shares should give us the correct public key
    print(f"\nVerifying derived public key...")

    # Sum all address-level shares
    total_key = 0
    for address_share in address_shares:
        share_int = int.from_bytes(address_share.share_value, 'big')
        total_key = (total_key + share_int) % SECP256K1_N

    print(f"  Sum of shares (x): {hex(total_key)[:32]}...")

    # Compute public key from sum
    G = EllipticCurvePoint.generator()
    computed_pubkey_point = G * total_key
    computed_pubkey = computed_pubkey_point.to_bytes(compressed=True)

    print(f"  Computed pubkey: {computed_pubkey.hex()[:32]}...")
    print(f"  Expected pubkey: {address_pubkey.hex()[:32]}...")

    if computed_pubkey == address_pubkey:
        print(f"\n✅ KEY DERIVATION IS CORRECT!")
        print(f"   All guardians are deriving to the same key level.")
        print(f"   Sum of shares equals the expected private key.")
        return True
    else:
        print(f"\n❌ KEY DERIVATION MISMATCH!")
        print(f"   The sum of guardian shares does NOT match the expected public key!")
        print(f"   This will cause signature verification to fail.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Verify key derivation consistency")
    parser.add_argument('--vault-config', '-c', required=True, help='Vault config file')
    parser.add_argument('--shares', nargs='+', required=True, help='Guardian share files')
    parser.add_argument('--address-index', '-a', type=int, default=0, help='Address index')

    args = parser.parse_args()

    try:
        success = verify_key_derivation(
            vault_config_file=args.vault_config,
            share_files=args.shares,
            address_index=args.address_index
        )

        print("\n" + "="*70)
        if success:
            print("✅ All checks passed!")
        else:
            print("❌ Verification failed!")
        print("="*70)

        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
