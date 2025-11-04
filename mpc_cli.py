#!/usr/bin/env python3
"""
CLI Tool for MPC Cryptocurrency Key Management
Easy-to-use command-line interface for common operations
"""

import argparse
import sys
import os
from crypto_mpc_keymanager import DistributedKeyManager, KeyShare


def generate_and_split(args):
    """Generate new master seed and split into shares"""
    manager = DistributedKeyManager()
    
    print(f"Generating master seed...")
    master_seed = manager.generate_master_seed()
    print(f"✓ Master seed generated: {master_seed.hex()}")
    print()
    
    print(f"Splitting into {args.num_shares} shares (threshold: {args.threshold})...")
    shares = manager.split_master_seed(master_seed, args.threshold, args.num_shares)
    print(f"✓ Created {len(shares)} shares")
    print()
    
    # Save shares
    output_dir = args.output_dir or "."
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Saving shares to {output_dir}/")
    for share in shares:
        filename = os.path.join(output_dir, f"share_{share.share_id}.json")
        manager.save_share_to_file(share, filename)
        print(f"  ✓ Share {share.share_id} → {filename}")
    
    print()
    print("⚠️  IMPORTANT: Store each share in a separate secure location!")
    print("⚠️  DESTROY the master seed - it should never be stored!")
    print()
    
    if args.save_seed:
        seed_file = os.path.join(output_dir, "master_seed.txt")
        with open(seed_file, 'w') as f:
            f.write(master_seed.hex())
        print(f"⚠️  WARNING: Saved master seed to {seed_file} (for testing only!)")
        print(f"⚠️  DELETE THIS FILE after distributing shares!")


def derive_keys(args):
    """Derive Bitcoin or Ethereum keys from shares"""
    manager = DistributedKeyManager()
    
    # Load shares
    print(f"Loading {len(args.shares)} share files...")
    shares = []
    for share_file in args.shares:
        share = manager.load_share_from_file(share_file)
        shares.append(share)
        print(f"  ✓ Loaded share {share.share_id} from {share_file}")
    
    print()
    
    # Verify threshold
    if shares:
        required = shares[0].threshold
        if len(shares) < required:
            print(f"❌ ERROR: Need at least {required} shares, but only {len(shares)} provided")
            return
        print(f"✓ Have {len(shares)} shares (threshold: {required})")
    
    print()
    print("Reconstructing master seed...")
    master_seed = manager.reconstruct_master_seed(shares)
    print("✓ Master seed reconstructed")
    print()
    
    # Derive keys based on coin type
    coin_type = args.coin_type.lower()
    account = args.account
    
    print(f"Deriving {coin_type.upper()} keys:")
    print(f"Account: {account}, Addresses: {args.start_index} to {args.start_index + args.count - 1}")
    print()
    
    for i in range(args.start_index, args.start_index + args.count):
        if coin_type == 'bitcoin':
            key = manager.derive_bitcoin_address_key(master_seed, account, i)
            path = f"m/44'/0'/{account}'/0/{i}"
        elif coin_type == 'ethereum':
            key = manager.derive_ethereum_address_key(master_seed, account, i)
            path = f"m/44'/60'/{account}'/0/{i}"
        else:
            print(f"❌ ERROR: Unsupported coin type: {coin_type}")
            return
        
        print(f"Address {i}:")
        print(f"  Path: {path}")
        print(f"  Private Key: {key.hex()}")
        print()
    
    print("✓ Keys derived successfully")
    print("⚠️  Master seed cleared from memory")
    del master_seed


def verify_shares(args):
    """Verify that shares can reconstruct the original seed"""
    manager = DistributedKeyManager()
    
    print(f"Loading {len(args.shares)} share files...")
    shares = []
    for share_file in args.shares:
        share = manager.load_share_from_file(share_file)
        shares.append(share)
        print(f"  ✓ Loaded share {share.share_id}")
    
    print()
    
    if shares:
        required = shares[0].threshold
        print(f"Share Configuration: {len(shares)} of {shares[0].total_shares} shares")
        print(f"Threshold: {required} shares required")
        print()
        
        if len(shares) < required:
            print(f"❌ Cannot verify - need at least {required} shares")
            return
    
    print("Attempting reconstruction...")
    try:
        reconstructed = manager.reconstruct_master_seed(shares)
        print("✓ Successfully reconstructed master seed!")
        print(f"Reconstructed seed: {reconstructed.hex()}")
        
        if args.original_seed:
            original = bytes.fromhex(args.original_seed)
            if reconstructed == original:
                print("✓ MATCH: Reconstructed seed matches original!")
            else:
                print("❌ MISMATCH: Reconstructed seed does NOT match original!")
        
        del reconstructed
    except Exception as e:
        print(f"❌ Reconstruction failed: {e}")


def show_share_info(args):
    """Display information about share files"""
    manager = DistributedKeyManager()
    
    for share_file in args.shares:
        print(f"\nShare File: {share_file}")
        print("-" * 60)
        
        try:
            share = manager.load_share_from_file(share_file)
            print(f"  Share ID: {share.share_id}")
            print(f"  Share Value: {share.share_value.hex()}")
            print(f"  Threshold: {share.threshold}")
            print(f"  Total Shares: {share.total_shares}")
            print(f"  Configuration: {share.threshold}-of-{share.total_shares}")
        except Exception as e:
            print(f"  ❌ Error loading share: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='MPC Cryptocurrency Key Manager CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate and split a new master seed
  %(prog)s generate -t 3 -n 5 -o ./shares
  
  # Derive Bitcoin keys from shares
  %(prog)s derive -c bitcoin -s share_1.json share_2.json share_3.json
  
  # Derive Ethereum keys (addresses 5-9)
  %(prog)s derive -c ethereum -s share_*.json --start 5 --count 5
  
  # Verify shares can reconstruct
  %(prog)s verify -s share_1.json share_2.json share_3.json
  
  # Show share information
  %(prog)s info -s share_*.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate and split master seed')
    gen_parser.add_argument('-t', '--threshold', type=int, required=True,
                           help='Minimum shares needed to reconstruct')
    gen_parser.add_argument('-n', '--num-shares', type=int, required=True,
                           help='Total number of shares to create')
    gen_parser.add_argument('-o', '--output-dir', 
                           help='Directory to save shares (default: current directory)')
    gen_parser.add_argument('--save-seed', action='store_true',
                           help='Save master seed to file (INSECURE - for testing only!)')
    gen_parser.set_defaults(func=generate_and_split)
    
    # Derive command
    derive_parser = subparsers.add_parser('derive', help='Derive keys from shares')
    derive_parser.add_argument('-c', '--coin-type', required=True, 
                              choices=['bitcoin', 'ethereum'],
                              help='Cryptocurrency type')
    derive_parser.add_argument('-s', '--shares', nargs='+', required=True,
                              help='Share files to use')
    derive_parser.add_argument('-a', '--account', type=int, default=0,
                              help='Account index (default: 0)')
    derive_parser.add_argument('--start', dest='start_index', type=int, default=0,
                              help='Starting address index (default: 0)')
    derive_parser.add_argument('--count', type=int, default=1,
                              help='Number of addresses to derive (default: 1)')
    derive_parser.set_defaults(func=derive_keys)
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify share reconstruction')
    verify_parser.add_argument('-s', '--shares', nargs='+', required=True,
                              help='Share files to verify')
    verify_parser.add_argument('--original-seed',
                              help='Original master seed (hex) to compare against')
    verify_parser.set_defaults(func=verify_shares)
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show share information')
    info_parser.add_argument('-s', '--shares', nargs='+', required=True,
                            help='Share files to inspect')
    info_parser.set_defaults(func=show_share_info)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    args.func(args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
