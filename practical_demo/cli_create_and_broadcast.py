#!/usr/bin/env python3
"""
Complete Transaction Flow: Create with UTXO, Sign with MPC, Broadcast
All-in-one command for demo convenience
"""
import sys
import os
import json
import argparse
import asyncio
import aiohttp
import requests
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardianvault.threshold_mpc_keymanager import ExtendedPublicKey, PublicKeyDerivation
from guardianvault.threshold_addresses import BitcoinAddressGenerator
from guardianvault.bitcoin_transaction import BitcoinTransactionBuilder


class BitcoinRPCClient:
    """Bitcoin RPC client"""

    def __init__(self, host="localhost", port=18443, user="regtest", password="regtest", wallet="regtest_wallet"):
        self.base_url = f"http://{user}:{password}@{host}:{port}"
        self.wallet_url = f"{self.base_url}/wallet/{wallet}"

    def rpc_call(self, method, params=[], use_wallet=False):
        url = self.wallet_url if use_wallet else self.base_url
        response = requests.post(url, json={
            "jsonrpc": "1.0",
            "id": "guardianvault",
            "method": method,
            "params": params
        })
        result = response.json()
        if 'error' in result and result['error']:
            raise Exception(f"RPC Error: {result['error']}")
        return result['result']

    def scantxoutset(self, action, scanobjects):
        return self.rpc_call("scantxoutset", [action, scanobjects])

    def sendrawtransaction(self, hexstring):
        return self.rpc_call("sendrawtransaction", [hexstring])

    def generatetoaddress(self, nblocks, address):
        return self.rpc_call("generatetoaddress", [nblocks, address])

    def getnewaddress(self, label="", address_type="bech32"):
        return self.rpc_call("getnewaddress", [label, address_type], use_wallet=True)

    def getrawtransaction(self, txid, verbose=True):
        return self.rpc_call("getrawtransaction", [txid, verbose])


def get_address_type_from_tracking(vault_config_file: str, address_index: int) -> str:
    """Get address type from tracking file if it exists"""
    tracking_file = vault_config_file.replace('vault_config.json', 'bitcoin_addresses.json')

    if os.path.exists(tracking_file):
        try:
            with open(tracking_file, 'r') as f:
                data = json.load(f)
                addresses = data.get('addresses', [])

                # Find address with matching index
                for addr in addresses:
                    if addr.get('index') == address_index:
                        return addr.get('address_type', 'p2pkh')
        except Exception as e:
            print(f"  Warning: Could not read tracking file: {e}")

    return None


async def complete_transaction_flow(
    server_url: str,
    vault_id: str,
    vault_config_file: str,
    recipient: str,
    amount: float,
    fee: float,
    address_index: int,
    memo: str,
    address_type: str = None
):
    """Complete flow: Create transaction with UTXO, wait for signing, broadcast"""

    print(f"\n{'='*70}")
    print(f"Complete Transaction Flow")
    print(f"{'='*70}\n")

    # Step 1: Load vault config and derive sender address
    print("Step 1: Loading vault configuration...")
    with open(vault_config_file, 'r') as f:
        vault_config = json.load(f)

    # Determine address type
    if address_type is None:
        # Try to read from tracking file
        address_type = get_address_type_from_tracking(vault_config_file, address_index)
        if address_type:
            print(f"  ℹ️  Found address type '{address_type}' for index {address_index} in tracking file")
        else:
            # Default to p2pkh
            address_type = 'p2pkh'
            print(f"  ℹ️  No address type specified, defaulting to '{address_type}'")
    else:
        print(f"  ℹ️  Using specified address type: '{address_type}'")

    # Check if we're trying to spend from P2TR
    if address_type == 'p2tr':
        print(f"\n❌ ERROR: Cannot spend from P2TR (Taproot) addresses")
        print(f"   Taproot requires Schnorr signatures, but GuardianVault currently uses ECDSA")
        print(f"   You can:")
        print(f"   - Use a P2PKH or P2WPKH address for spending (--address-type p2pkh or p2wpkh)")
        print(f"   - Generate a new P2WPKH address: python3 cli_generate_address.py --coin bitcoin --type p2wpkh")
        print(f"   - Send TO Taproot addresses (as recipient), but cannot spend FROM them yet")
        return False

    xpub = ExtendedPublicKey.from_dict(vault_config['bitcoin']['xpub'])
    pubkeys = PublicKeyDerivation.derive_address_public_keys(xpub, change=0, num_addresses=address_index + 1)
    sender_pubkey = pubkeys[address_index]
    sender_address = BitcoinAddressGenerator.pubkey_to_address(
        sender_pubkey,
        network="regtest",
        address_type=address_type
    )

    print(f"✓ Sender address: {sender_address} (index {address_index}, type: {address_type})")

    # Step 2: Find UTXO for sender address
    print("\nStep 2: Finding UTXO...")
    rpc = BitcoinRPCClient()

    result = rpc.scantxoutset("start", [f"addr({sender_address})"])
    unspents = result.get('unspents', [])

    if not unspents:
        print(f"❌ No UTXOs found for {sender_address}")
        print(f"   Please fund this address first:")
        print(f"   python3 cli_transaction_requester.py fund-address -a {sender_address} --amount 2.0")
        return False

    # Use first UTXO
    utxo = unspents[0]
    print(f"✓ Found UTXO: {utxo['txid']}:{utxo['vout']} ({utxo['amount']} BTC)")

    # Step 3: Create transaction with UTXO details
    print("\nStep 3: Creating transaction with MPC signing request...")

    tx_data = {
        "vault_id": vault_id,
        "type": "send",
        "coin_type": "bitcoin",
        "amount": str(amount),
        "recipient": recipient,
        "fee": str(fee),
        "memo": memo,
        # Bitcoin-specific fields for proper sighash
        "utxo_txid": utxo['txid'],
        "utxo_vout": utxo['vout'],
        "utxo_amount": str(utxo['amount']),
        "sender_address": sender_address,
        "address_index": address_index
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

    # Step 4: Wait for MPC signing
    print("\nStep 4: Waiting for MPC signing...")
    print("  (Guardians must be connected and will automatically participate)")

    max_wait = 60
    for i in range(max_wait):
        await asyncio.sleep(1)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{server_url}/api/transactions/{transaction_id}") as response:
                if response.status == 200:
                    tx = await response.json()
                    status = tx['status']

                    print(f"  [{i+1}/{max_wait}] Status: {status}", end='\r')

                    if status == 'completed':
                        print(f"\n✓ Transaction signed!")
                        break
                    elif status == 'failed':
                        print(f"\n❌ Transaction signing failed")
                        return False
    else:
        print(f"\n⏱️ Timeout waiting for signature")
        return False

    # Step 5: Broadcast the signed transaction
    print("\nStep 5: Broadcasting to Bitcoin network...")

    # Build transaction using the EXACT parameters that were signed
    # (from the transaction stored in database)
    tx_builder, script_code = BitcoinTransactionBuilder.build_p2pkh_transaction(
        utxo_txid=tx['utxo_txid'],
        utxo_vout=tx['utxo_vout'],
        utxo_amount_btc=float(tx['utxo_amount']),
        sender_address=tx['sender_address'],
        recipient_address=tx['recipient'],
        send_amount_btc=float(tx['amount']),
        fee_btc=float(tx['fee'])
    )

    # Verify the sighash matches
    computed_sighash = tx_builder.get_sighash(input_index=0, script_code=script_code)
    expected_sighash = bytes.fromhex(tx['message_hash'])

    if computed_sighash != expected_sighash:
        print(f"❌ SIGHASH MISMATCH!")
        print(f"  Expected: {expected_sighash.hex()}")
        print(f"  Computed: {computed_sighash.hex()}")
        return False

    print(f"✓ Sighash verified: {computed_sighash.hex()[:32]}...")

    # Add MPC signature
    # Derive the correct pubkey for the address index used
    address_idx = tx.get('address_index', 0)
    xpub = ExtendedPublicKey.from_dict(vault_config['bitcoin']['xpub'])
    pubkeys = PublicKeyDerivation.derive_address_public_keys(xpub, change=0, num_addresses=address_idx + 1)
    correct_pubkey = pubkeys[address_idx]

    signature = tx['final_signature']
    signature_der = bytes.fromhex(signature['der'])

    signed_tx = BitcoinTransactionBuilder.sign_transaction(
        tx_builder,
        input_index=0,
        script_code=script_code,
        signature_der=signature_der,
        public_key=correct_pubkey
    )

    # Broadcast
    raw_tx_hex = signed_tx.serialize().hex()

    try:
        txid = rpc.sendrawtransaction(raw_tx_hex)
        print(f"✓ Transaction broadcast successfully!")
        print(f"  TXID: {txid}")

        # Mine a block
        print(f"\n  Mining 1 block to confirm...")
        miner_address = rpc.getnewaddress()
        rpc.generatetoaddress(1, miner_address)

        tx_details = rpc.getrawtransaction(txid, True)
        print(f"  ✓ Confirmed in block")
        print(f"  Confirmations: {tx_details.get('confirmations', 0)}")

        print(f"\n{'='*70}")
        print("Transaction Complete!")
        print(f"{'='*70}")
        print(f"From: {sender_address}")
        print(f"To: {recipient}")
        print(f"Amount: {amount} BTC")
        print(f"Fee: {fee} BTC")
        print(f"TXID: {txid}")
        print(f"{'='*70}\n")

        return True

    except Exception as e:
        print(f"\n❌ Broadcast failed: {str(e)}")
        return False


async def main():
    parser = argparse.ArgumentParser(
        description="Complete transaction flow: create, sign with MPC, broadcast",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use address from tracking file (auto-detects type)
  python3 cli_create_and_broadcast.py \\
      --vault-id vault_abc123 \\
      --vault-config demo_output/vault_config.json \\
      --recipient bcrt1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh \\
      --amount 0.5 \\
      --address-index 5

  # Explicitly specify P2WPKH sender address
  python3 cli_create_and_broadcast.py \\
      --vault-id vault_abc123 \\
      --vault-config demo_output/vault_config.json \\
      --recipient bcrt1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh \\
      --amount 0.5 \\
      --address-index 6 \\
      --address-type p2wpkh \\
      --memo "SegWit payment"

  # Send to Taproot address (P2TR recipient is supported)
  python3 cli_create_and_broadcast.py \\
      --vault-id vault_abc123 \\
      --vault-config demo_output/vault_config.json \\
      --recipient bcrt1p... \\
      --amount 0.5 \\
      --address-index 3 \\
      --address-type p2pkh

This will:
  1. Detect or use specified sender address type
  2. Find UTXO for sender address
  3. Create transaction with proper Bitcoin sighash
  4. Wait for guardians to sign via MPC
  5. Broadcast to Bitcoin network

Note: Spending FROM P2TR addresses is not yet supported (requires Schnorr signatures).
      You can send TO P2TR addresses, but must use P2PKH or P2WPKH for spending.
        """
    )

    parser.add_argument('--server', '-s', type=str, default='http://localhost:8000',
                       help='Coordination server URL')
    parser.add_argument('--vault-id', '-v', type=str, required=True,
                       help='Vault ID')
    parser.add_argument('--vault-config', '-c', type=str, required=True,
                       help='Path to vault configuration file')
    parser.add_argument('--recipient', '-r', type=str, required=True,
                       help='Recipient Bitcoin address')
    parser.add_argument('--amount', '-a', type=float, required=True,
                       help='Amount in BTC')
    parser.add_argument('--fee', '-f', type=float, default=0.0001,
                       help='Fee in BTC (default: 0.0001)')
    parser.add_argument('--address-index', type=int, default=0,
                       help='Sender address derivation index (default: 0)')
    parser.add_argument('--address-type', '-t', type=str, choices=['p2pkh', 'p2wpkh', 'p2tr'],
                       help='Address type (p2pkh, p2wpkh, p2tr). If not specified, reads from bitcoin_addresses.json or defaults to p2pkh. Note: P2TR spending not yet supported.')
    parser.add_argument('--memo', '-m', type=str, default='',
                       help='Transaction memo')

    args = parser.parse_args()

    try:
        success = await complete_transaction_flow(
            server_url=args.server,
            vault_id=args.vault_id,
            vault_config_file=args.vault_config,
            recipient=args.recipient,
            amount=args.amount,
            fee=args.fee,
            address_index=args.address_index,
            memo=args.memo,
            address_type=args.address_type
        )

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
