#!/usr/bin/env python3
"""
Diagnostic script to debug signature verification issues
"""
import sys
import os
import json
import argparse
import requests

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardianvault.threshold_mpc_keymanager import ExtendedPublicKey, PublicKeyDerivation
from guardianvault.threshold_addresses import BitcoinAddressGenerator
from guardianvault.bitcoin_transaction import BitcoinTransactionBuilder
from guardianvault.threshold_signing import ThresholdSigner, ThresholdSignature


def verify_signature_manually(
    public_key: bytes,
    message_hash: bytes,
    r: int,
    s: int
) -> bool:
    """Manually verify ECDSA signature"""
    print("\n" + "=" * 70)
    print("MANUAL SIGNATURE VERIFICATION")
    print("=" * 70)

    print(f"\nPublic Key: {public_key.hex()}")
    print(f"Message Hash: {message_hash.hex()}")
    print(f"r: {hex(r)[:32]}...")
    print(f"s: {hex(s)[:32]}...")

    signature = ThresholdSignature(r=r, s=s)

    try:
        valid = ThresholdSigner.verify_signature(public_key, message_hash, signature)
        print(f"\n✓ Signature Valid: {valid}")
        return valid
    except Exception as e:
        print(f"\n✗ Verification Error: {e}")
        return False


def analyze_transaction(server_url: str, transaction_id: str, vault_config_file: str):
    """Analyze a transaction and verify signature"""
    print("\n" + "=" * 70)
    print(f"ANALYZING TRANSACTION: {transaction_id}")
    print("=" * 70)

    # Fetch transaction from server
    response = requests.get(f"{server_url}/api/transactions/{transaction_id}")
    if response.status_code != 200:
        print(f"✗ Failed to fetch transaction: {response.status_code}")
        return False

    tx = response.json()

    print(f"\nTransaction Details:")
    print(f"  Status: {tx['status']}")
    print(f"  Coin Type: {tx['coin_type']}")
    print(f"  Amount: {tx['amount']}")
    print(f"  Recipient: {tx['recipient']}")
    print(f"  Sender Address: {tx.get('sender_address', 'N/A')}")
    print(f"  Address Index: {tx.get('address_index', 'N/A')}")
    print(f"  Message Hash: {tx['message_hash'][:32]}...")

    # Load vault config
    with open(vault_config_file, 'r') as f:
        vault_config = json.load(f)

    # Get address index
    address_index = tx.get('address_index', 0)
    print(f"\n✓ Using address index: {address_index}")

    # Derive public key
    xpub = ExtendedPublicKey.from_dict(vault_config['bitcoin']['xpub'])
    pubkeys = PublicKeyDerivation.derive_address_public_keys(
        xpub, change=0, num_addresses=address_index + 1
    )
    correct_pubkey = pubkeys[address_index]

    print(f"✓ Derived public key: {correct_pubkey.hex()[:32]}...")

    # Verify the address matches
    derived_address = BitcoinAddressGenerator.pubkey_to_address(correct_pubkey, network="regtest")
    sender_address = tx.get('sender_address')

    print(f"\nAddress Verification:")
    print(f"  Derived Address: {derived_address}")
    print(f"  Sender Address: {sender_address}")
    print(f"  Addresses Match: {derived_address == sender_address}")

    if derived_address != sender_address:
        print("\n⚠️  WARNING: Address mismatch! This will cause signature verification to fail!")

    # Check if signature is complete
    final_sig = tx.get('final_signature')
    if not final_sig:
        print("\n✗ Transaction not yet signed")
        return False

    print(f"\nFinal Signature:")
    print(f"  r: {final_sig['r'][:32]}...")
    print(f"  s: {final_sig['s'][:32]}...")
    print(f"  rHex: {final_sig['rHex'][:32]}...")
    print(f"  sHex: {final_sig['sHex'][:32]}...")
    print(f"  DER: {final_sig['der'][:64]}...")

    # Verify signature
    r = int(final_sig['r'])
    s = int(final_sig['s'])
    message_hash = bytes.fromhex(tx['message_hash'])

    valid = verify_signature_manually(correct_pubkey, message_hash, r, s)

    if not valid:
        print("\n✗ SIGNATURE VERIFICATION FAILED!")
        print("\nPossible causes:")
        print("  1. Wrong public key (address derivation mismatch)")
        print("  2. Wrong message hash (sighash mismatch)")
        print("  3. Signature computation error")
        print("  4. Low-S enforcement issue")
        return False

    print("\n✓ SIGNATURE VERIFICATION PASSED!")

    # Verify Bitcoin transaction construction
    if tx.get('utxo_txid'):
        print("\n" + "=" * 70)
        print("VERIFYING BITCOIN TRANSACTION CONSTRUCTION")
        print("=" * 70)

        try:
            # Build the transaction
            tx_builder, script_code = BitcoinTransactionBuilder.build_p2pkh_transaction(
                utxo_txid=tx['utxo_txid'],
                utxo_vout=tx['utxo_vout'],
                utxo_amount_btc=float(tx['utxo_amount']),
                sender_address=tx['sender_address'],
                recipient_address=tx['recipient'],
                send_amount_btc=float(tx['amount']),
                fee_btc=float(tx.get('fee', '0.0001'))
            )

            # Compute sighash
            computed_sighash = tx_builder.get_sighash(input_index=0, script_code=script_code)
            expected_sighash = bytes.fromhex(tx['message_hash'])

            print(f"\nSighash Verification:")
            print(f"  Expected:  {expected_sighash.hex()[:32]}...")
            print(f"  Computed:  {computed_sighash.hex()[:32]}...")
            print(f"  Match: {computed_sighash == expected_sighash}")

            if computed_sighash != expected_sighash:
                print("\n✗ SIGHASH MISMATCH!")
                print("  The transaction parameters changed between signing and broadcasting!")
                return False

            print("\n✓ Sighash matches!")

            # Build signed transaction
            signature_der = bytes.fromhex(final_sig['der'])
            signed_tx = BitcoinTransactionBuilder.sign_transaction(
                tx_builder,
                input_index=0,
                script_code=script_code,
                signature_der=signature_der,
                public_key=correct_pubkey
            )

            raw_tx_hex = signed_tx.serialize().hex()
            print(f"\nSigned Transaction:")
            print(f"  Hex: {raw_tx_hex[:64]}...")
            print(f"  Length: {len(raw_tx_hex) // 2} bytes")

            print("\n✓ Transaction built successfully!")
            print(f"\nYou can broadcast this transaction:")
            print(f"  bitcoin-cli -regtest sendrawtransaction {raw_tx_hex}")

        except Exception as e:
            print(f"\n✗ Error building transaction: {e}")
            import traceback
            traceback.print_exc()
            return False

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

    return valid


def main():
    parser = argparse.ArgumentParser(
        description="Debug signature verification issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python3 debug_signature.py \\
      --transaction-id tx_abc123 \\
      --vault-config demo_shares/vault_config.json \\
      --server http://localhost:8000
        """
    )

    parser.add_argument('--transaction-id', '-t', type=str, required=True,
                       help='Transaction ID to analyze')
    parser.add_argument('--vault-config', '-c', type=str, required=True,
                       help='Path to vault configuration file')
    parser.add_argument('--server', '-s', type=str, default='http://localhost:8000',
                       help='Coordination server URL')

    args = parser.parse_args()

    try:
        success = analyze_transaction(
            server_url=args.server,
            transaction_id=args.transaction_id,
            vault_config_file=args.vault_config
        )

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
