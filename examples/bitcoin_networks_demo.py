#!/usr/bin/env python3
"""
Bitcoin Network Support Demo
Demonstrates generating Bitcoin addresses for mainnet, testnet, and regtest
"""

import os
import sys
import secrets

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from guardianvault.mpc_keymanager import (
    MPCKeyGeneration,
    MPCBIP32
)
from guardianvault.mpc_addresses import BitcoinAddressGenerator


def main():
    print("\n")
    print("=" * 80)
    print("BITCOIN NETWORK SUPPORT DEMO")
    print("Generate addresses for Mainnet, Testnet, and Regtest")
    print("=" * 80)
    print()

    # Setup MPC key generation
    print("Step 1: Generate MPC key shares")
    print("-" * 80)
    num_parties = 3
    key_shares, _ = MPCKeyGeneration.generate_shares(num_parties)
    print(f"✓ Generated {num_parties} key shares")
    print()

    # Derive master keys
    print("Step 2: Derive BIP32 master keys")
    print("-" * 80)
    seed = secrets.token_bytes(32)
    master_shares, master_pubkey, master_chain = \
        MPCBIP32.derive_master_keys_distributed(key_shares, seed)
    print(f"✓ Master public key: {master_pubkey.hex()[:32]}...")
    print()

    # Derive Bitcoin account xpub (m/44'/0'/0')
    print("Step 3: Derive Bitcoin account xpub (m/44'/0'/0')")
    print("-" * 80)
    btc_xpub = MPCBIP32.derive_account_xpub_distributed(
        master_shares, master_chain, coin_type=0, account=0
    )
    print(f"✓ Bitcoin xpub: {btc_xpub.public_key.hex()[:32]}...")
    print()

    # Generate addresses for all three networks
    print("=" * 80)
    print("MAINNET ADDRESSES")
    print("=" * 80)
    print("Use these for production Bitcoin transactions")
    print()
    mainnet_addresses = BitcoinAddressGenerator.generate_addresses_from_xpub(
        btc_xpub, change=0, start_index=0, count=3, network="mainnet"
    )
    for addr in mainnet_addresses:
        print(f"  Path: {addr['path']}")
        print(f"  Address: {addr['address']}")
        print(f"  Format: Starts with '1' (P2PKH mainnet)")
        print()

    print("=" * 80)
    print("TESTNET ADDRESSES")
    print("=" * 80)
    print("Use these for testing with public Bitcoin testnet")
    print()
    testnet_addresses = BitcoinAddressGenerator.generate_addresses_from_xpub(
        btc_xpub, change=0, start_index=0, count=3, network="testnet"
    )
    for addr in testnet_addresses:
        print(f"  Path: {addr['path']}")
        print(f"  Address: {addr['address']}")
        print(f"  Format: Starts with 'm' or 'n' (P2PKH testnet)")
        print()

    print("=" * 80)
    print("REGTEST ADDRESSES")
    print("=" * 80)
    print("Use these for local development with Bitcoin regtest")
    print()
    regtest_addresses = BitcoinAddressGenerator.generate_addresses_from_xpub(
        btc_xpub, change=0, start_index=0, count=3, network="regtest"
    )
    for addr in regtest_addresses:
        print(f"  Path: {addr['path']}")
        print(f"  Address: {addr['address']}")
        print(f"  Format: Starts with 'm' or 'n' (P2PKH regtest)")
        print()

    # Show that testnet and regtest produce identical addresses
    print("=" * 80)
    print("IMPORTANT NOTES")
    print("=" * 80)
    print()
    print("✓ Mainnet addresses start with '1' (version byte 0x00)")
    print("✓ Testnet addresses start with 'm' or 'n' (version byte 0x6f)")
    print("✓ Regtest addresses start with 'm' or 'n' (version byte 0x6f)")
    print()
    print("⚠️  Testnet and regtest use the SAME address format")
    print(f"    Example: {testnet_addresses[0]['address']} == {regtest_addresses[0]['address']}")
    print(f"    Match: {testnet_addresses[0]['address'] == regtest_addresses[0]['address']}")
    print()
    print("This is expected behavior - Bitcoin regtest uses testnet address format")
    print("The network parameter helps you document your intent clearly")
    print()

    print("=" * 80)
    print("USAGE EXAMPLES")
    print("=" * 80)
    print()
    print("# Generate mainnet addresses (production)")
    print("BitcoinAddressGenerator.generate_addresses_from_xpub(xpub, network='mainnet')")
    print()
    print("# Generate testnet addresses (public testing)")
    print("BitcoinAddressGenerator.generate_addresses_from_xpub(xpub, network='testnet')")
    print()
    print("# Generate regtest addresses (local development)")
    print("BitcoinAddressGenerator.generate_addresses_from_xpub(xpub, network='regtest')")
    print()
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
