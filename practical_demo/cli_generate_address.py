#!/usr/bin/env python3
"""
CLI Tool: Generate Deposit Address
Derives new Bitcoin/Ethereum addresses from the vault's account xpub
"""
import sys
import os
import json
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardianvault.threshold_mpc_keymanager import (
    ExtendedPublicKey,
    PublicKeyDerivation
)
from guardianvault.threshold_addresses import (
    BitcoinAddressGenerator,
    EthereumAddressGenerator
)


def load_vault_config(config_file: str) -> dict:
    """Load vault configuration"""
    with open(config_file, 'r') as f:
        return json.load(f)


def get_next_address_index(config_file: str, coin_type: str) -> int:
    """Get the next available address index from tracking file"""
    tracking_file = config_file.replace('vault_config.json', f'{coin_type}_addresses.json')

    if os.path.exists(tracking_file):
        with open(tracking_file, 'r') as f:
            data = json.load(f)
            return data.get('next_index', 0)
    return 0


def save_address_tracking(config_file: str, coin_type: str, index: int, address: str, pubkey: str):
    """Save address to tracking file"""
    tracking_file = config_file.replace('vault_config.json', f'{coin_type}_addresses.json')

    data = {'addresses': [], 'next_index': 0}
    if os.path.exists(tracking_file):
        with open(tracking_file, 'r') as f:
            data = json.load(f)

    # Add new address
    data['addresses'].append({
        'index': index,
        'address': address,
        'public_key': pubkey,
        'path': f"m/44'/{0 if coin_type == 'bitcoin' else 60}'/0'/0/{index}",
        'used': False
    })
    data['next_index'] = index + 1

    with open(tracking_file, 'w') as f:
        json.dump(data, f, indent=2)


def generate_bitcoin_address(vault_config: dict, index: int, change: int = 0) -> tuple:
    """
    Generate Bitcoin address at given index

    Args:
        vault_config: Vault configuration
        index: Address index
        change: Change level (0=receive, 1=change)

    Returns:
        (address, public_key, derivation_path)
    """
    # Get account xpub (m/44'/0'/0')
    account_xpub = ExtendedPublicKey.from_dict(vault_config['bitcoin']['xpub'])
    network = vault_config['bitcoin'].get('network', 'regtest')

    # Derive change level (m/44'/0'/0'/change)
    change_pubkey, change_chain = PublicKeyDerivation.derive_public_child(account_xpub, change)
    change_xpub = ExtendedPublicKey(
        public_key=change_pubkey,
        chain_code=change_chain,
        depth=account_xpub.depth + 1,
        parent_fingerprint=b'\x00\x00\x00\x00',
        child_number=change
    )

    # Derive address level (m/44'/0'/0'/change/index)
    address_pubkey, _ = PublicKeyDerivation.derive_public_child(change_xpub, index)

    # Generate address
    address = BitcoinAddressGenerator.pubkey_to_address(address_pubkey, network=network)

    derivation_path = f"m/44'/0'/0'/{change}/{index}"

    return address, address_pubkey.hex(), derivation_path


def generate_ethereum_address(vault_config: dict, index: int, change: int = 0) -> tuple:
    """
    Generate Ethereum address at given index

    Args:
        vault_config: Vault configuration
        index: Address index
        change: Change level (typically 0 for Ethereum)

    Returns:
        (address, public_key, derivation_path)
    """
    # Get account xpub (m/44'/60'/0')
    account_xpub = ExtendedPublicKey.from_dict(vault_config['ethereum']['xpub'])

    # Derive change level (m/44'/60'/0'/change)
    change_pubkey, change_chain = PublicKeyDerivation.derive_public_child(account_xpub, change)
    change_xpub = ExtendedPublicKey(
        public_key=change_pubkey,
        chain_code=change_chain,
        depth=account_xpub.depth + 1,
        parent_fingerprint=b'\x00\x00\x00\x00',
        child_number=change
    )

    # Derive address level (m/44'/60'/0'/change/index)
    address_pubkey, _ = PublicKeyDerivation.derive_public_child(change_xpub, index)

    # Generate address
    address = EthereumAddressGenerator.pubkey_to_address(address_pubkey)

    derivation_path = f"m/44'/60'/0'/{change}/{index}"

    return address, address_pubkey.hex(), derivation_path


def list_addresses(config_file: str, coin_type: str):
    """List all generated addresses"""
    tracking_file = config_file.replace('vault_config.json', f'{coin_type}_addresses.json')

    if not os.path.exists(tracking_file):
        print(f"No {coin_type} addresses generated yet.")
        return

    with open(tracking_file, 'r') as f:
        data = json.load(f)

    print(f"\n{'='*70}")
    print(f"{coin_type.upper()} ADDRESSES")
    print(f"{'='*70}")
    print(f"Total addresses: {len(data['addresses'])}")
    print(f"Next index: {data['next_index']}")
    print(f"\n{'Index':<8} {'Address':<45} {'Used':<6} Path")
    print(f"{'-'*70}")

    for addr in data['addresses']:
        used = '✓' if addr.get('used', False) else ''
        print(f"{addr['index']:<8} {addr['address']:<45} {used:<6} {addr['path']}")

    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate deposit addresses for GuardianVault",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate next Bitcoin address
  python3 cli_generate_address.py --config demo_output/vault_config.json --coin bitcoin

  # Generate Bitcoin address at specific index
  python3 cli_generate_address.py --config demo_output/vault_config.json --coin bitcoin --index 5

  # Generate Ethereum address
  python3 cli_generate_address.py --config demo_output/vault_config.json --coin ethereum

  # List all generated Bitcoin addresses
  python3 cli_generate_address.py --config demo_output/vault_config.json --coin bitcoin --list

  # Generate multiple addresses
  python3 cli_generate_address.py --config demo_output/vault_config.json --coin bitcoin --count 5
        """
    )

    parser.add_argument('--config', '-c', type=str, required=True,
                       help='Path to vault configuration file')
    parser.add_argument('--coin', type=str, choices=['bitcoin', 'ethereum'], required=True,
                       help='Coin type (bitcoin or ethereum)')
    parser.add_argument('--index', '-i', type=int, default=None,
                       help='Address index (default: next available)')
    parser.add_argument('--change', type=int, default=0,
                       help='Change level: 0=receive, 1=change (default: 0)')
    parser.add_argument('--count', '-n', type=int, default=1,
                       help='Number of addresses to generate (default: 1)')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List all generated addresses')
    parser.add_argument('--no-save', action='store_true',
                       help='Do not save address to tracking file')

    args = parser.parse_args()

    try:
        # List addresses if requested
        if args.list:
            list_addresses(args.config, args.coin)
            return

        # Load vault config
        vault_config = load_vault_config(args.config)

        print(f"\n{'='*70}")
        print(f"GENERATING {args.coin.upper()} ADDRESS(ES)")
        print(f"{'='*70}")
        print(f"Vault: {vault_config.get('vault_name', 'Unknown')}")
        print(f"Network: {vault_config[args.coin].get('network', 'N/A')}")
        print(f"{'='*70}\n")

        # Determine starting index
        if args.index is not None:
            start_index = args.index
        else:
            start_index = get_next_address_index(args.config, args.coin)

        # Generate addresses
        for i in range(args.count):
            index = start_index + i

            if args.coin == 'bitcoin':
                address, pubkey, path = generate_bitcoin_address(vault_config, index, args.change)
            else:  # ethereum
                address, pubkey, path = generate_ethereum_address(vault_config, index, args.change)

            print(f"Address #{index}:")
            print(f"  Path:       {path}")
            print(f"  Address:    {address}")
            print(f"  Public Key: {pubkey[:32]}...{pubkey[-32:]}")

            # Save to tracking file
            if not args.no_save:
                save_address_tracking(args.config, args.coin, index, address, pubkey)
                print(f"  ✓ Saved to tracking file")

            print()

        print(f"{'='*70}")
        print(f"✅ Generated {args.count} {args.coin} address(es)")
        print(f"{'='*70}\n")

        # Show usage hint
        if not args.no_save:
            print("💡 Tip: Use --list to see all generated addresses")
            print(f"   python3 cli_generate_address.py --config {args.config} --coin {args.coin} --list\n")

    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"❌ Error: Invalid vault config - missing key {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
