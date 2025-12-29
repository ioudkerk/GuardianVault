#!/usr/bin/env python3
"""
GuardianVault Crypto Operations CLI
This script provides a command-line interface for MPC signing operations.
It's called by the Electron main process via subprocess.
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path to import guardianvault library
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from guardianvault.mpc_signing import MPCSigner


def round1_generate_nonce(key_share_data: dict, message_hash: str) -> dict:
    """
    Generate nonce for Round 1 of threshold signing

    Args:
        key_share_data: Guardian's key share containing 'x' (private key share)
        message_hash: Message hash to sign (hex string)

    Returns:
        Dictionary with 'R' (nonce public point) and 'k_blind' (blinded nonce)
    """
    try:
        # Extract private key share
        x_i = int(key_share_data['x'], 16)

        # Create signer instance
        signer = MPCSigner()

        # Generate nonce for Round 1
        result = signer.sign_round1_generate_nonce(x_i, message_hash)

        return {
            'R': result['R'],
            'k_blind': result['k_blind'],
            'success': True
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def round3_compute_signature_share(
    key_share_data: dict,
    k_blind: str,
    r: str,
    message_hash: str
) -> dict:
    """
    Compute signature share for Round 3 of threshold signing

    Args:
        key_share_data: Guardian's key share containing 'x' (private key share)
        k_blind: Blinded nonce from Round 1
        r: Combined r value from Round 2 (provided by server)
        message_hash: Message hash to sign (hex string)

    Returns:
        Dictionary with 's' (signature share)
    """
    try:
        # Extract private key share
        x_i = int(key_share_data['x'], 16)

        # Create signer instance
        signer = MPCSigner()

        # Compute signature share for Round 3
        result = signer.sign_round3_compute_signature_share(
            x_i=x_i,
            k_blind=k_blind,
            r=r,
            message_hash=message_hash
        )

        return {
            's': result['s'],
            'success': True
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description='GuardianVault Threshold Signing Operations'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Round 1: Generate nonce
    round1_parser = subparsers.add_parser(
        'round1',
        help='Generate nonce for Round 1 signing'
    )
    round1_parser.add_argument(
        '--key-share',
        required=True,
        help='Key share data as JSON string'
    )
    round1_parser.add_argument(
        '--message-hash',
        required=True,
        help='Message hash to sign (hex string)'
    )

    # Round 3: Compute signature share
    round3_parser = subparsers.add_parser(
        'round3',
        help='Compute signature share for Round 3'
    )
    round3_parser.add_argument(
        '--key-share',
        required=True,
        help='Key share data as JSON string'
    )
    round3_parser.add_argument(
        '--k-blind',
        required=True,
        help='Blinded nonce from Round 1'
    )
    round3_parser.add_argument(
        '--r',
        required=True,
        help='Combined r value from Round 2'
    )
    round3_parser.add_argument(
        '--message-hash',
        required=True,
        help='Message hash to sign (hex string)'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        # Parse key share data
        key_share_data = json.loads(args.key_share)

        if args.command == 'round1':
            result = round1_generate_nonce(key_share_data, args.message_hash)
        elif args.command == 'round3':
            result = round3_compute_signature_share(
                key_share_data,
                args.k_blind,
                args.r,
                args.message_hash
            )
        else:
            result = {
                'success': False,
                'error': f'Unknown command: {args.command}'
            }

        # Output result as JSON
        print(json.dumps(result))

        # Exit with appropriate code
        sys.exit(0 if result.get('success') else 1)

    except json.JSONDecodeError as e:
        print(json.dumps({
            'success': False,
            'error': f'Invalid JSON in key-share: {str(e)}'
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }))
        sys.exit(1)


if __name__ == '__main__':
    main()
