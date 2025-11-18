#!/usr/bin/env python3
"""
CLI 1: Share Generator
Creates threshold key shares and derives xpub keys for Bitcoin and Ethereum
"""
import sys
import os
import json
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardianvault.threshold_mpc_keymanager import (
    ThresholdKeyGeneration,
    ThresholdBIP32,
    ExtendedPublicKey,
    PublicKeyDerivation
)
from guardianvault.threshold_addresses import (
    BitcoinAddressGenerator,
    EthereumAddressGenerator
)


def generate_shares_and_keys(num_guardians: int, threshold: int, output_dir: str, vault_name: str):
    """Generate distributed key shares and derive keys for Bitcoin and Ethereum"""

    print(f"\n{'='*60}")
    print(f"Generating Threshold Key Shares")
    print(f"{'='*60}")
    print(f"Vault Name: {vault_name}")
    print(f"Total Guardians: {num_guardians}")
    print(f"Threshold: {threshold}")
    print(f"Output Directory: {output_dir}")
    print(f"{'='*60}\n")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Generate distributed key shares
    print("Step 1: Generating distributed key shares...")
    key_shares, master_public_key = ThresholdKeyGeneration.generate_shares(
        num_parties=num_guardians,
        threshold=threshold
    )
    print(f"✓ Generated {len(key_shares)} key shares")
    print(f"✓ Master public key: {master_public_key[:32]}...{master_public_key[-32:]}")

    # Step 2: Derive master keys with BIP32
    print("\nStep 2: Deriving BIP32 master keys...")
    seed = b"GuardianVault Demo Seed 2025"  # In production, use secure random seed
    master_shares, master_pub, chain_code = ThresholdBIP32.derive_master_keys_threshold(
        key_shares, seed
    )
    print(f"✓ Derived master keys")
    print(f"✓ Chain code: {chain_code.hex()[:32]}...")

    # Step 3: Derive Bitcoin account shares (m/44'/0'/0') - ALL GUARDIANS TOGETHER
    print("\nStep 3: Deriving Bitcoin account shares (m/44'/0'/0')...")
    # Derive m/44'
    purpose_shares, _, purpose_chain = ThresholdBIP32.derive_hardened_child_threshold(
        master_shares, None, chain_code, 44
    )
    # Derive m/44'/0'
    coin_shares, _, coin_chain = ThresholdBIP32.derive_hardened_child_threshold(
        purpose_shares, None, purpose_chain, 0
    )
    # Derive m/44'/0'/0'
    btc_account_shares, btc_account_pubkey, btc_account_chain = ThresholdBIP32.derive_hardened_child_threshold(
        coin_shares, None, coin_chain, 0
    )

    # Create Bitcoin xpub from derived account key
    btc_xpub = ExtendedPublicKey(
        public_key=btc_account_pubkey,
        chain_code=btc_account_chain,
        depth=3,
        parent_fingerprint=b'\x00\x00\x00\x00',
        child_number=0x80000000  # Hardened derivation
    )
    print(f"✓ Bitcoin account shares and xpub generated")

    # Generate sample Bitcoin addresses
    btc_addresses = PublicKeyDerivation.derive_address_public_keys(
        btc_xpub,
        change=0,
        num_addresses=5
    )
    btc_address_strings = [
        BitcoinAddressGenerator.pubkey_to_address(pk, network="regtest")
        for pk in btc_addresses
    ]

    # Step 4: Derive Ethereum account shares (m/44'/60'/0') - ALL GUARDIANS TOGETHER
    print("\nStep 4: Deriving Ethereum account shares (m/44'/60'/0')...")
    # Derive m/44' (reuse from Bitcoin)
    # Derive m/44'/60'
    eth_coin_shares, _, eth_coin_chain = ThresholdBIP32.derive_hardened_child_threshold(
        purpose_shares, None, purpose_chain, 60
    )
    # Derive m/44'/60'/0'
    eth_account_shares, eth_account_pubkey, eth_account_chain = ThresholdBIP32.derive_hardened_child_threshold(
        eth_coin_shares, None, eth_coin_chain, 0
    )

    # Create Ethereum xpub from derived account key
    eth_xpub = ExtendedPublicKey(
        public_key=eth_account_pubkey,
        chain_code=eth_account_chain,
        depth=3,
        parent_fingerprint=b'\x00\x00\x00\x00',
        child_number=0x80000000  # Hardened derivation
    )
    print(f"✓ Ethereum account shares and xpub generated")

    # Generate sample Ethereum addresses
    eth_addresses = PublicKeyDerivation.derive_address_public_keys(
        eth_xpub,
        change=0,
        num_addresses=5
    )
    eth_address_strings = [
        EthereumAddressGenerator.pubkey_to_address(pk)
        for pk in eth_addresses
    ]

    # Step 5: Save ACCOUNT-LEVEL shares to individual files
    # IMPORTANT: We save account shares, not master shares!
    # This allows guardians to derive addresses independently using non-hardened derivation
    print("\nStep 5: Saving account-level key shares...")
    share_files = []
    for i, (btc_share, eth_share) in enumerate(zip(btc_account_shares, eth_account_shares), 1):
        filename = f"{output_dir}/guardian_{i}_share.json"
        share_data = {
            "vault_name": vault_name,
            "guardian_id": i,
            "total_guardians": num_guardians,
            "threshold": threshold,
            "bitcoin_account_share": btc_share.to_dict(),
            "ethereum_account_share": eth_share.to_dict(),
            "metadata": {
                "created_at": "2025-11-16",
                "share_level": "account",
                "note": "These are account-level shares (m/44'/coin'/0'), not master shares",
                "coin_types": ["bitcoin", "ethereum"],
                "derivation_paths": {
                    "bitcoin": "m/44'/0'/0'",
                    "ethereum": "m/44'/60'/0'"
                }
            }
        }
        with open(filename, 'w') as f:
            json.dump(share_data, f, indent=2)
        share_files.append(filename)
        print(f"  ✓ Saved: {filename}")

    # Step 6: Save vault configuration
    print("\nStep 6: Saving vault configuration...")
    vault_config = {
        "vault_name": vault_name,
        "total_guardians": num_guardians,
        "threshold": threshold,
        "bitcoin": {
            "coin_type": 0,
            "account": 0,
            "derivation_path": "m/44'/0'/0'",
            "xpub": btc_xpub.to_dict(),
            "sample_addresses": btc_address_strings[:5],
            "network": "regtest"
        },
        "ethereum": {
            "coin_type": 60,
            "account": 0,
            "derivation_path": "m/44'/60'/0'",
            "xpub": eth_xpub.to_dict(),
            "sample_addresses": eth_address_strings[:5],
            "network": "testnet"
        },
        "master_chain_code": chain_code.hex()
    }

    vault_config_file = f"{output_dir}/vault_config.json"
    with open(vault_config_file, 'w') as f:
        json.dump(vault_config, f, indent=2)
    print(f"  ✓ Saved: {vault_config_file}")

    # Step 7: Print summary
    print(f"\n{'='*60}")
    print("Generation Complete!")
    print(f"{'='*60}\n")

    print("Bitcoin Configuration:")
    print(f"  Derivation Path: m/44'/0'/0'")
    print(f"  Network: regtest")
    print(f"  Sample Addresses:")
    for i, addr in enumerate(btc_address_strings[:3], 1):
        print(f"    {i}. {addr}")

    print("\nEthereum Configuration:")
    print(f"  Derivation Path: m/44'/60'/0'")
    print(f"  Network: testnet")
    print(f"  Sample Addresses:")
    for i, addr in enumerate(eth_address_strings[:3], 1):
        print(f"    {i}. {addr}")

    print(f"\n{'='*60}")
    print("Files Generated:")
    print(f"{'='*60}")
    for f in share_files:
        print(f"  • {f}")
    print(f"  • {vault_config_file}")

    print(f"\n{'='*60}")
    print("Next Steps:")
    print(f"{'='*60}")
    print("1. Start the coordination server:")
    print("   cd coordination-server && poetry run uvicorn app.main:app --reload")
    print("\n2. Use the admin CLI to create a vault:")
    print(f"   python3 cli_admin.py create-vault --config {vault_config_file}")
    print("\n3. Distribute shares to guardians:")
    for i in range(1, num_guardians + 1):
        print(f"   • Guardian {i}: {output_dir}/guardian_{i}_share.json")
    print(f"{'='*60}\n")

    return vault_config


def main():
    parser = argparse.ArgumentParser(
        description="Generate threshold key shares and xpub keys for Bitcoin and Ethereum",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate shares for 3 guardians with threshold 3
  python3 cli_share_generator.py --guardians 3 --threshold 3 --vault "Demo Vault" --output demo_shares

  # Generate shares for 5 guardians with threshold 3
  python3 cli_share_generator.py --guardians 5 --threshold 3 --vault "Production Vault" --output prod_shares
        """
    )

    parser.add_argument('--guardians', '-g', type=int, required=True,
                        help='Total number of guardians')
    parser.add_argument('--threshold', '-t', type=int, required=True,
                        help='Minimum number of guardians required for signing')
    parser.add_argument('--vault', '-v', type=str, required=True,
                        help='Name of the vault')
    parser.add_argument('--output', '-o', type=str, default='demo_shares',
                        help='Output directory for shares (default: demo_shares)')

    args = parser.parse_args()

    # Validation
    if args.threshold > args.guardians:
        print("Error: Threshold cannot be greater than total guardians")
        sys.exit(1)

    if args.threshold < 2:
        print("Error: Threshold must be at least 2")
        sys.exit(1)

    try:
        generate_shares_and_keys(
            num_guardians=args.guardians,
            threshold=args.threshold,
            output_dir=args.output,
            vault_name=args.vault
        )
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
