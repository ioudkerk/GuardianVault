#!/usr/bin/env python3
"""
Ethereum Transaction Flow: Create, Sign with MPC, Broadcast
Complete workflow for Ethereum EIP-1559 transactions
"""
import sys
import os
import json
import argparse
import asyncio
import aiohttp

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardianvault.threshold_mpc_keymanager import ExtendedPublicKey, PublicKeyDerivation
from guardianvault.threshold_addresses import EthereumAddressGenerator
from guardianvault.ethereum_transaction import EthereumTransactionBuilder, EthereumTransaction, LegacyEthereumTransaction
from guardianvault.ethereum_rpc import EthereumRPCClient


def get_ethereum_address_from_tracking(vault_config_file: str, address_index: int) -> str:
    """Get Ethereum address from tracking file if it exists"""
    tracking_file = vault_config_file.replace('vault_config.json', 'ethereum_addresses.json')

    if os.path.exists(tracking_file):
        try:
            with open(tracking_file, 'r') as f:
                data = json.load(f)
                addresses = data.get('addresses', [])

                # Find address with matching index
                for addr in addresses:
                    if addr.get('index') == address_index:
                        return addr.get('address')
        except Exception as e:
            print(f"  Warning: Could not read tracking file: {e}")

    return None


async def complete_ethereum_transaction_flow(
    server_url: str,
    vault_id: str,
    vault_config_file: str,
    recipient: str,
    amount_eth: float,
    address_index: int,
    memo: str,
    rpc_host: str = "localhost",
    rpc_port: int = 8545,
    chain_id: int = None,
    max_priority_fee_gwei: float = None,
    max_fee_gwei: float = None,
    gas_limit: int = 21000,
    legacy: bool = False
):
    """Complete Ethereum transaction flow: Create, Sign with MPC, Broadcast"""

    print(f"\n{'='*70}")
    if legacy:
        print(f"Ethereum Transaction Flow (Legacy/Type 0)")
    else:
        print(f"Ethereum Transaction Flow (EIP-1559/Type 2)")
    print(f"{'='*70}\n")

    # Step 1: Load vault config and derive sender address
    print("Step 1: Loading vault configuration...")
    with open(vault_config_file, 'r') as f:
        vault_config = json.load(f)

    # Derive sender address
    xpub = ExtendedPublicKey.from_dict(vault_config['ethereum']['xpub'])
    pubkeys = PublicKeyDerivation.derive_address_public_keys(
        xpub,
        change=0,
        num_addresses=address_index + 1
    )
    sender_pubkey = pubkeys[address_index]
    sender_address = EthereumAddressGenerator.pubkey_to_address(sender_pubkey)

    print(f"✓ Sender address: {sender_address} (index {address_index})")
    print(f"  Public key: {sender_pubkey.hex()}")

    # Step 2: Connect to Ethereum node and get account state
    print("\nStep 2: Querying Ethereum node...")
    rpc = EthereumRPCClient(host=rpc_host, port=rpc_port)

    try:
        # Get chain ID if not specified
        if chain_id is None:
            chain_id = rpc.get_chain_id()
            print(f"✓ Chain ID: {chain_id}")

        # Get current nonce
        nonce = rpc.get_transaction_count(sender_address)
        print(f"✓ Current nonce: {nonce}")

        # Get balance
        balance_wei = rpc.get_balance(sender_address)
        balance_eth = balance_wei / 10**18
        print(f"✓ Balance: {balance_eth:.6f} ETH")

        # Check if account has sufficient balance
        if balance_eth < amount_eth:
            print(f"\n❌ Insufficient balance!")
            print(f"   Balance: {balance_eth:.6f} ETH")
            print(f"   Required: {amount_eth:.6f} ETH")
            print(f"\n   Please fund this address first:")
            print(f"   {sender_address}")
            return False

        # Get fee data if not specified
        if max_priority_fee_gwei is None or max_fee_gwei is None:
            print("\n  Fetching current fee data...")
            fee_data = rpc.get_fee_data()

            if max_priority_fee_gwei is None:
                max_priority_fee_gwei = fee_data['maxPriorityFeePerGas'] / 10**9
                print(f"  ✓ Max priority fee: {max_priority_fee_gwei:.2f} Gwei (from node)")

            if max_fee_gwei is None:
                max_fee_gwei = fee_data['maxFeePerGas'] / 10**9
                print(f"  ✓ Max fee per gas: {max_fee_gwei:.2f} Gwei (from node)")

    except Exception as e:
        print(f"❌ Failed to connect to Ethereum node: {e}")
        print(f"\n   Make sure your Ethereum node is running:")
        print(f"   - Ganache: ganache-cli --port {rpc_port}")
        print(f"   - Hardhat: npx hardhat node")
        return False

    # Step 3: Build transaction
    tx_type = "legacy" if legacy else "EIP-1559"
    print(f"\nStep 3: Building {tx_type} transaction...")
    tx = EthereumTransactionBuilder.build_transfer_transaction(
        sender_address=sender_address,
        recipient_address=recipient,
        amount_eth=amount_eth,
        nonce=nonce,
        chain_id=chain_id,
        max_priority_fee_gwei=max_priority_fee_gwei,
        max_fee_gwei=max_fee_gwei,
        gas_limit=gas_limit,
        legacy=legacy
    )

    # Compute signing hash
    signing_hash = tx.get_signing_hash()
    print(f"✓ Transaction created")
    print(f"  To: {recipient}")
    print(f"  Amount: {amount_eth} ETH")
    print(f"  Nonce: {nonce}")
    print(f"  Gas limit: {gas_limit}")
    if legacy:
        print(f"  Gas price: {max_fee_gwei:.2f} Gwei")
    else:
        print(f"  Max priority fee: {max_priority_fee_gwei:.2f} Gwei")
        print(f"  Max fee: {max_fee_gwei:.2f} Gwei")
    print(f"  Signing hash: {signing_hash.hex()}")

    # Step 4: Send to coordination server for MPC signing
    print("\nStep 4: Requesting MPC signature from coordination server...")

    tx_data = {
        "vault_id": vault_id,
        "type": "send",
        "coin_type": "ethereum",
        "amount": str(amount_eth),
        "recipient": recipient,
        "memo": memo,
        # Ethereum-specific fields
        "message_hash": signing_hash.hex(),
        "sender_address": sender_address,
        "address_index": address_index,
        "nonce": nonce,
        "chain_id": chain_id,
        "max_priority_fee_per_gas": int(max_priority_fee_gwei * 10**9),
        "max_fee_per_gas": int(max_fee_gwei * 10**9),
        "gas_limit": gas_limit,
        "tx_data": tx.data.hex() if tx.data else ""
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{server_url}/api/transactions",
            json=tx_data
        ) as response:
            if response.status not in [200, 201]:
                error = await response.text()
                print(f"❌ Failed to create transaction: {error}")
                return False

            result = await response.json()
            transaction_id = result['transaction_id']
            print(f"✓ Transaction created: {transaction_id}")
            print(f"  Status: {result['status']}")
            print(f"  Guardians will now sign...")

    # Step 5: Wait for MPC signing
    print("\nStep 5: Waiting for MPC signing...")
    print("  (Guardians must be connected and will automatically participate)")

    max_wait = 60
    signed_tx = None

    for i in range(max_wait):
        await asyncio.sleep(1)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{server_url}/api/transactions/{transaction_id}") as response:
                if response.status == 200:
                    tx_status = await response.json()
                    status = tx_status['status']

                    print(f"  [{i+1}/{max_wait}] Status: {status}", end='\r')

                    if status == 'completed':
                        print(f"\n✓ Transaction signed!")
                        signed_tx = tx_status
                        break
                    elif status == 'failed':
                        print(f"\n❌ Transaction signing failed")
                        return False
    else:
        print(f"\n⏱️ Timeout waiting for signature")
        return False

    # Step 6: Verify and add signature to transaction
    print("\nStep 6: Verifying signature...")

    signature = signed_tx['final_signature']
    r = int(signature['r'])
    s = int(signature['s'])

    # IMPORTANT: Use the message hash that was actually signed (from server)
    # not the one we computed locally, in case they differ
    signed_message_hash = bytes.fromhex(signed_tx['message_hash'])

    # Recover v parameter for Ethereum
    from guardianvault.threshold_signing import ThresholdSignature, ThresholdSigner

    threshold_sig = ThresholdSignature(r=r, s=s)

    print(f"  r: {hex(r)[:32]}...")
    print(f"  s: {hex(s)[:32]}...")

    # Recover v parameter
    try:
        print(f"  Attempting v-parameter recovery...")
        print(f"  Public key: {sender_pubkey.hex()[:64]}...")
        print(f"  Message hash (from server): {signed_message_hash.hex()}")
        print(f"  Message hash (local): {signing_hash.hex()}")

        if signed_message_hash != signing_hash:
            print(f"  ⚠️  WARNING: Message hashes differ! Using server's hash.")

        print(f"  Signature r: {hex(r)}")
        print(f"  Signature s: {hex(s)}")

        v = ThresholdSigner.recover_ethereum_v(
            public_key=sender_pubkey,
            message_hash=signed_message_hash,  # Use the hash that was actually signed
            signature=threshold_sig
        )
        print(f"  v: {v}")
        print(f"✓ Signature recovery parameter found")
    except Exception as e:
        print(f"❌ Failed to recover v parameter: {e}")
        print(f"\n  This might be because:")
        print(f"  1. The signature was created with a different message hash")
        print(f"  2. The public key doesn't match the private key that signed")
        print(f"  3. There's an issue with the elliptic curve math")
        print(f"\n  Trying basic signature verification first...")

        # Try basic verification to see if signature is valid
        is_valid_basic = ThresholdSigner.verify_signature(
            public_key=sender_pubkey,
            message_hash=signed_message_hash,
            signature=threshold_sig
        )

        if is_valid_basic:
            print(f"  ✓ Signature verifies correctly with ECDSA")
            print(f"  But v-recovery still fails - this is unexpected")
        else:
            print(f"  ✗ Signature doesn't verify - wrong message hash or key?")

        return False

    # Verify signature
    is_valid = ThresholdSigner.verify_signature(
        public_key=sender_pubkey,
        message_hash=signed_message_hash,
        signature=threshold_sig
    )

    if not is_valid:
        print(f"❌ Signature verification failed!")
        return False

    print(f"✓ Signature verified")

    # Set signature on transaction
    tx.set_signature(v=v, r=r, s=s)

    # Step 7: Serialize and broadcast
    print("\nStep 7: Broadcasting to Ethereum network...")

    # Debug: Show transaction details before serialization
    print(f"  Debug: Transaction details before serialization:")
    print(f"    chain_id: {tx.chain_id}")
    print(f"    nonce: {tx.nonce}")
    print(f"    to: {tx.to}")
    print(f"    value: {tx.value} Wei ({tx.value / 10**18} ETH)")
    print(f"    gas_limit: {tx.gas_limit}")
    if isinstance(tx, LegacyEthereumTransaction):
        print(f"    gas_price: {tx.gas_price} Wei ({tx.gas_price / 10**9} Gwei)")
    else:
        print(f"    max_priority_fee: {tx.max_priority_fee_per_gas} Wei ({tx.max_priority_fee_per_gas / 10**9} Gwei)")
        print(f"    max_fee: {tx.max_fee_per_gas} Wei ({tx.max_fee_per_gas / 10**9} Gwei)")
    print(f"    v: {tx.v}, r: {tx.r}, s: {tx.s}")

    # Recompute signing hash to verify it matches
    test_hash = tx.get_signing_hash()
    print(f"  Debug: Recomputed signing hash: {test_hash.hex()}")
    print(f"  Debug: Original signing hash: {signing_hash.hex()}")
    print(f"  Debug: Server's hash: {signed_message_hash.hex()}")

    if test_hash != signing_hash:
        print(f"  ⚠️  WARNING: Recomputed hash doesn't match original!")
        print(f"  This transaction will fail to broadcast.")

    serialized_tx = tx.serialize()
    tx_hex = serialized_tx.hex()

    print(f"\n  Transaction size: {len(serialized_tx)} bytes")
    print(f"  Serialized tx: 0x{tx_hex[:64]}...")
    print(f"  Full serialized tx: 0x{tx_hex}")

    try:
        tx_hash = rpc.send_raw_transaction(tx_hex)
        print(f"\n✓ Transaction broadcast successful!")
        print(f"  Transaction hash: {tx_hash}")

        # Wait for transaction to be mined
        print(f"\n  Waiting for transaction to be mined...")
        try:
            receipt = rpc.wait_for_transaction(tx_hash, timeout=30, poll_interval=2)
            print(f"\n✓ Transaction mined!")
            print(f"  Block number: {int(receipt['blockNumber'], 16)}")
            print(f"  Gas used: {int(receipt['gasUsed'], 16)}")
            print(f"  Status: {'Success' if int(receipt['status'], 16) == 1 else 'Failed'}")

            # Check final balance
            new_balance = rpc.get_balance_eth(sender_address)
            print(f"\n  New balance: {new_balance:.6f} ETH")

        except TimeoutError:
            print(f"\n⏱️ Transaction not mined yet (still pending)")
            print(f"  Transaction hash: {tx_hash}")

    except Exception as e:
        print(f"❌ Failed to broadcast transaction: {e}")
        return False

    print(f"\n{'='*70}")
    print("✓ Ethereum transaction flow completed successfully!")
    print(f"{'='*70}\n")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Create and broadcast Ethereum transaction with MPC signing"
    )
    parser.add_argument("--server", default="http://localhost:8000", help="Coordination server URL")
    parser.add_argument("--vault-id", required=True, help="Vault ID")
    parser.add_argument("--config", required=True, help="Path to vault config file")
    parser.add_argument("--recipient", required=True, help="Recipient Ethereum address")
    parser.add_argument("--amount", type=float, required=True, help="Amount in ETH")
    parser.add_argument("--address-index", type=int, default=0, help="Address derivation index")
    parser.add_argument("--memo", default="", help="Transaction memo")
    parser.add_argument("--rpc-host", default="localhost", help="Ethereum RPC host")
    parser.add_argument("--rpc-port", type=int, default=8545, help="Ethereum RPC port")
    parser.add_argument("--chain-id", type=int, help="Network chain ID (auto-detect if not specified)")
    parser.add_argument("--max-priority-fee", type=float, help="Max priority fee in Gwei (EIP-1559 only, auto if not specified)")
    parser.add_argument("--max-fee", type=float, help="Max fee per gas in Gwei (auto if not specified)")
    parser.add_argument("--gas-limit", type=int, default=21000, help="Gas limit (default: 21000)")
    parser.add_argument("--legacy", action="store_true", help="Use legacy (Type 0) transactions instead of EIP-1559 (for Ganache CLI v6)")

    args = parser.parse_args()

    # Run async flow
    result = asyncio.run(complete_ethereum_transaction_flow(
        server_url=args.server,
        vault_id=args.vault_id,
        vault_config_file=args.config,
        recipient=args.recipient,
        amount_eth=args.amount,
        address_index=args.address_index,
        memo=args.memo,
        rpc_host=args.rpc_host,
        rpc_port=args.rpc_port,
        chain_id=args.chain_id,
        max_priority_fee_gwei=args.max_priority_fee,
        max_fee_gwei=args.max_fee,
        gas_limit=args.gas_limit,
        legacy=args.legacy
    ))

    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
