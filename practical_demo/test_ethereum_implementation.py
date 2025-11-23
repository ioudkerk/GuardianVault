#!/usr/bin/env python3
"""
Test Ethereum Implementation
Verifies all Ethereum components without requiring a live network
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardianvault.rlp_encoding import encode, encode_int, encode_address, decode
from guardianvault.ethereum_transaction import EthereumTransaction, EthereumTransactionBuilder
from guardianvault.threshold_signing import ThresholdSignature, ThresholdSigner
from guardianvault.threshold_mpc_keymanager import ThresholdKeyGeneration


def test_rlp_encoding():
    """Test RLP encoding functionality"""
    print("\n" + "="*70)
    print("TEST 1: RLP Encoding")
    print("="*70)

    # Test basic encoding
    assert encode(b'dog') == b'\x83dog', "Basic string encoding failed"
    print("✓ Basic string encoding")

    assert encode([]) == b'\xc0', "Empty list encoding failed"
    print("✓ Empty list encoding")

    result = encode([b'cat', b'dog'])
    assert result == b'\xc8\x83cat\x83dog', "List encoding failed"
    print("✓ List encoding")

    # Test integer encoding
    assert encode_int(0) == b'', "Zero encoding failed"
    assert encode_int(127) == b'\x7f', "Small int encoding failed"
    assert encode_int(256) == b'\x01\x00', "Large int encoding failed"
    print("✓ Integer encoding")

    # Test address encoding
    addr = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
    addr_bytes = encode_address(addr)
    assert len(addr_bytes) == 20, "Address encoding failed"
    print("✓ Address encoding")

    # Test decoding
    assert decode(b'\x83dog') == b'dog', "Decoding failed"
    print("✓ Decoding")

    print("\n✓ All RLP encoding tests passed!")


def test_ethereum_transaction():
    """Test Ethereum transaction creation and serialization"""
    print("\n" + "="*70)
    print("TEST 2: Ethereum Transaction")
    print("="*70)

    # Create a test transaction
    tx = EthereumTransactionBuilder.build_transfer_transaction(
        sender_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        recipient_address="0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
        amount_eth=0.1,
        nonce=0,
        chain_id=1337,
        max_priority_fee_gwei=2.0,
        max_fee_gwei=100.0
    )
    print("✓ Created EIP-1559 transaction")

    # Test signing hash
    signing_hash = tx.get_signing_hash()
    assert len(signing_hash) == 32, "Signing hash should be 32 bytes"
    print(f"✓ Computed signing hash: 0x{signing_hash.hex()[:32]}...")

    # Test signature setting
    tx.set_signature(v=0, r=12345, s=67890)
    print("✓ Set signature components")

    # Test serialization
    serialized = tx.serialize()
    assert serialized[0] == 0x02, "Should start with EIP-1559 type byte"
    assert len(serialized) > 0, "Serialization failed"
    print(f"✓ Serialized transaction: {len(serialized)} bytes")

    # Test to_dict
    tx_dict = tx.to_dict()
    assert tx_dict['chainId'] == 1337, "Chain ID mismatch"
    assert tx_dict['value'] == int(0.1 * 10**18), "Value mismatch"
    assert tx_dict['nonce'] == 0, "Nonce mismatch"
    print("✓ Converted to dictionary")

    print("\n✓ All Ethereum transaction tests passed!")


def test_threshold_signing_with_ethereum():
    """Test threshold signing and v-parameter recovery for Ethereum"""
    print("\n" + "="*70)
    print("TEST 3: Threshold Signing with Ethereum")
    print("="*70)

    # Generate key shares
    num_parties = 3
    key_shares, master_pubkey = ThresholdKeyGeneration.generate_shares(num_parties)
    print(f"✓ Generated {num_parties} key shares")
    print(f"  Master public key: {master_pubkey.hex()[:32]}...")

    # Create a test transaction
    tx = EthereumTransactionBuilder.build_transfer_transaction(
        sender_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        recipient_address="0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
        amount_eth=0.1,
        nonce=0,
        chain_id=1337
    )

    # Get signing hash
    message_hash = tx.get_signing_hash()
    print(f"✓ Transaction signing hash: 0x{message_hash.hex()[:32]}...")

    # Import signing workflow
    from guardianvault.threshold_signing import ThresholdSigningWorkflow

    # Sign the message
    print("\n  Performing threshold signing...")
    signature = ThresholdSigningWorkflow.sign_message(
        key_shares=key_shares,
        message=message_hash,
        public_key=master_pubkey,
        prehashed=True
    )

    print(f"\n✓ Generated threshold signature")
    print(f"  r: {hex(signature.r)[:32]}...")
    print(f"  s: {hex(signature.s)[:32]}...")

    # Verify signature
    is_valid = ThresholdSigner.verify_signature(
        public_key=master_pubkey,
        message_hash=message_hash,
        signature=signature
    )
    assert is_valid, "Signature verification failed"
    print("✓ Signature verified")

    # Recover v parameter
    print("\n  Recovering Ethereum v parameter...")
    try:
        v = ThresholdSigner.recover_ethereum_v(
            public_key=master_pubkey,
            message_hash=message_hash,
            signature=signature
        )
        print(f"✓ Recovered v parameter: {v}")
        assert v in [0, 1], "v should be 0 or 1 for EIP-1559"
    except Exception as e:
        print(f"✗ Failed to recover v parameter: {e}")
        return False

    # Set signature on transaction
    tx.set_signature(v=v, r=signature.r, s=signature.s)
    print("✓ Signature set on transaction")

    # Serialize complete transaction
    serialized = tx.serialize()
    print(f"✓ Serialized signed transaction: {len(serialized)} bytes")
    print(f"  Hex: 0x{serialized.hex()[:64]}...")

    print("\n✓ All threshold signing tests passed!")
    return True


def test_integration():
    """Test complete integration of all components"""
    print("\n" + "="*70)
    print("TEST 4: Complete Integration Test")
    print("="*70)

    # This simulates the complete flow without requiring a live network

    # Step 1: Generate threshold keys
    print("\nStep 1: Generate threshold keys...")
    num_parties = 2
    key_shares, master_pubkey = ThresholdKeyGeneration.generate_shares(num_parties)
    print(f"✓ Generated {num_parties}-of-{num_parties} threshold key")

    # Step 2: Derive Ethereum address
    print("\nStep 2: Derive Ethereum address...")
    from guardianvault.threshold_addresses import EthereumAddressGenerator

    sender_address = EthereumAddressGenerator.pubkey_to_address(master_pubkey)
    print(f"✓ Sender address: {sender_address}")

    # Step 3: Create transaction
    print("\nStep 3: Create Ethereum transaction...")
    recipient = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
    tx = EthereumTransactionBuilder.build_transfer_transaction(
        sender_address=sender_address,
        recipient_address=recipient,
        amount_eth=0.5,
        nonce=0,
        chain_id=1337,
        max_priority_fee_gwei=2.0,
        max_fee_gwei=100.0,
        gas_limit=21000
    )
    print(f"✓ Transaction created:")
    print(f"  From: {sender_address}")
    print(f"  To: {recipient}")
    print(f"  Amount: 0.5 ETH")
    print(f"  Chain ID: 1337")

    # Step 4: Get signing hash
    print("\nStep 4: Compute signing hash...")
    signing_hash = tx.get_signing_hash()
    print(f"✓ Signing hash: 0x{signing_hash.hex()}")

    # Step 5: MPC signing
    print("\nStep 5: Perform MPC signing...")
    from guardianvault.threshold_signing import ThresholdSigningWorkflow

    signature = ThresholdSigningWorkflow.sign_message(
        key_shares=key_shares,
        message=signing_hash,
        public_key=master_pubkey,
        prehashed=True
    )
    print(f"\n✓ MPC signature generated")

    # Step 6: Recover v parameter
    print("\nStep 6: Recover Ethereum v parameter...")
    v = ThresholdSigner.recover_ethereum_v(
        public_key=master_pubkey,
        message_hash=signing_hash,
        signature=signature
    )
    print(f"✓ Recovery ID: {v}")

    # Step 7: Complete transaction
    print("\nStep 7: Finalize transaction...")
    tx.set_signature(v=v, r=signature.r, s=signature.s)
    serialized = tx.serialize()
    print(f"✓ Signed transaction ready for broadcast")
    print(f"  Size: {len(serialized)} bytes")
    print(f"  Hex: 0x{serialized.hex()}")

    print("\n" + "="*70)
    print("✓ Complete integration test passed!")
    print("="*70)

    return True


def main():
    print("\n" + "="*70)
    print("ETHEREUM IMPLEMENTATION TEST SUITE")
    print("="*70)

    all_passed = True

    try:
        test_rlp_encoding()
    except Exception as e:
        print(f"\n✗ RLP encoding tests failed: {e}")
        all_passed = False

    try:
        test_ethereum_transaction()
    except Exception as e:
        print(f"\n✗ Ethereum transaction tests failed: {e}")
        all_passed = False

    try:
        test_threshold_signing_with_ethereum()
    except Exception as e:
        print(f"\n✗ Threshold signing tests failed: {e}")
        all_passed = False

    try:
        test_integration()
    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("="*70)
        print("\nEthereum implementation is ready!")
        print("\nNext steps:")
        print("1. Start a local Ethereum node (Ganache or Hardhat)")
        print("2. Start the coordination server")
        print("3. Register guardians")
        print("4. Create and broadcast Ethereum transactions")
        print("\nExample:")
        print("  python3 cli_create_ethereum_transaction.py \\")
        print("    --vault-id <vault-id> \\")
        print("    --config <config-file> \\")
        print("    --recipient 0x... \\")
        print("    --amount 0.1")
    else:
        print("✗ SOME TESTS FAILED")
        print("="*70)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
