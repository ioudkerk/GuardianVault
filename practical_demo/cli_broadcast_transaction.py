#!/usr/bin/env python3
"""
CLI for Broadcasting Signed Transactions
Takes a completed MPC signature and broadcasts to Bitcoin network
"""
import sys
import os
import json
import argparse
import asyncio
import aiohttp
import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardianvault.threshold_mpc_keymanager import ExtendedPublicKey, PublicKeyDerivation
from guardianvault.threshold_addresses import BitcoinAddressGenerator
from guardianvault.bitcoin_transaction import BitcoinTransactionBuilder, BitcoinTransaction


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


async def get_transaction_details(server_url: str, transaction_id: str):
    """Get transaction details from coordination server"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{server_url}/api/transactions/{transaction_id}") as response:
            if response.status == 200:
                return await response.json()
            else:
                return None


async def broadcast_signed_transaction(
    server_url: str,
    transaction_id: str,
    vault_config_file: str,
    utxo_txid: str,
    utxo_vout: int,
    utxo_amount: float,
    address_index: int = 0
):
    """Complete and broadcast a signed transaction"""

    print(f"\n{'='*70}")
    print(f"Broadcasting Signed Transaction")
    print(f"{'='*70}")
    print(f"Transaction ID: {transaction_id}")
    print(f"{'='*70}\n")

    # Step 1: Get transaction from coordination server
    print("Step 1: Fetching transaction from coordination server...")
    tx = await get_transaction_details(server_url, transaction_id)

    if not tx:
        print("❌ Transaction not found")
        return False

    if tx['status'] != 'completed':
        print(f"❌ Transaction not completed yet (status: {tx['status']})")
        return False

    if not tx.get('final_signature'):
        print("❌ No signature found")
        return False

    print(f"✓ Transaction found")
    print(f"  Status: {tx['status']}")
    print(f"  Recipient: {tx['recipient']}")
    print(f"  Amount: {tx['amount']} BTC")
    print()

    # Step 2: Load vault configuration
    print("Step 2: Loading vault configuration...")
    with open(vault_config_file, 'r') as f:
        vault_config = json.load(f)

    xpub = ExtendedPublicKey.from_dict(vault_config['bitcoin']['xpub'])

    # Derive sender address
    pubkeys = PublicKeyDerivation.derive_address_public_keys(xpub, change=0, num_addresses=address_index + 1)
    sender_pubkey = pubkeys[address_index]
    sender_address = BitcoinAddressGenerator.pubkey_to_address(sender_pubkey, network="regtest")

    print(f"✓ Sender address: {sender_address} (index {address_index})")
    print()

    # Step 3: Build Bitcoin transaction
    print("Step 3: Building Bitcoin transaction...")

    tx_builder, script_code = BitcoinTransactionBuilder.build_p2pkh_transaction(
        utxo_txid=utxo_txid,
        utxo_vout=utxo_vout,
        utxo_amount_btc=utxo_amount,
        sender_address=sender_address,
        recipient_address=tx['recipient'],
        send_amount_btc=float(tx['amount']),
        fee_btc=float(tx['fee'])
    )

    print(f"✓ Transaction built")
    print(f"  Input: {utxo_txid}:{utxo_vout} ({utxo_amount} BTC)")
    print(f"  Output 1: {tx['recipient']} ({tx['amount']} BTC)")
    change_amount = utxo_amount - float(tx['amount']) - float(tx['fee'])
    if change_amount > 0:
        print(f"  Output 2: {sender_address} ({change_amount} BTC - change)")
    print(f"  Fee: {tx['fee']} BTC")
    print()

    # Step 4: Add signature to transaction
    print("Step 4: Adding MPC signature...")

    signature = tx['final_signature']
    signature_der = bytes.fromhex(signature['der'])

    signed_tx = BitcoinTransactionBuilder.sign_transaction(
        tx_builder,
        input_index=0,
        script_code=script_code,
        signature_der=signature_der,
        public_key=sender_pubkey
    )

    print(f"✓ Signature added")
    print(f"  r: {signature['rHex'][:32]}...")
    print(f"  s: {signature['sHex'][:32]}...")
    print()

    # Step 5: Serialize and broadcast
    print("Step 5: Broadcasting to Bitcoin network...")

    raw_tx_hex = signed_tx.serialize().hex()
    print(f"  Raw transaction: {raw_tx_hex[:64]}...")

    rpc = BitcoinRPCClient()

    try:
        txid = rpc.sendrawtransaction(raw_tx_hex)
        print(f"\n✅ Transaction broadcast successfully!")
        print(f"  TXID: {txid}")

        # Mine a block to confirm
        print(f"\n  Mining 1 block to confirm...")
        miner_address = rpc.getnewaddress()
        rpc.generatetoaddress(1, miner_address)

        # Get confirmation
        tx_details = rpc.getrawtransaction(txid, True)
        print(f"  ✓ Transaction confirmed in block")
        print(f"  Confirmations: {tx_details.get('confirmations', 0)}")

        print(f"\n{'='*70}")
        print("Broadcast Complete!")
        print(f"{'='*70}\n")

        return True

    except Exception as e:
        print(f"\n❌ Broadcast failed: {str(e)}")
        return False


async def main():
    parser = argparse.ArgumentParser(
        description="Broadcast signed transactions to Bitcoin network",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example workflow:

1. Find a completed transaction:
   python3 cli_transaction_requester.py list-transactions --vault-id vault_abc123

2. Find UTXOs for the sender address:
   python3 cli_transaction_requester.py check-balance --address <SENDER_ADDRESS>

3. Broadcast the signed transaction:
   python3 cli_broadcast_transaction.py \\
       --transaction-id tx_abc123 \\
       --vault-config demo_shares/vault_config.json \\
       --utxo-txid <TXID> \\
       --utxo-vout 0 \\
       --utxo-amount 2.0 \\
       --address-index 0
        """
    )

    parser.add_argument('--server', '-s', type=str, default='http://localhost:8000',
                       help='Coordination server URL')
    parser.add_argument('--transaction-id', '-t', type=str, required=True,
                       help='Transaction ID from coordination server')
    parser.add_argument('--vault-config', '-c', type=str, required=True,
                       help='Path to vault configuration file')
    parser.add_argument('--utxo-txid', type=str, required=True,
                       help='UTXO transaction ID to spend')
    parser.add_argument('--utxo-vout', type=int, required=True,
                       help='UTXO output index')
    parser.add_argument('--utxo-amount', type=float, required=True,
                       help='UTXO amount in BTC')
    parser.add_argument('--address-index', type=int, default=0,
                       help='Sender address derivation index (default: 0)')

    args = parser.parse_args()

    try:
        success = await broadcast_signed_transaction(
            server_url=args.server,
            transaction_id=args.transaction_id,
            vault_config_file=args.vault_config,
            utxo_txid=args.utxo_txid,
            utxo_vout=args.utxo_vout,
            utxo_amount=args.utxo_amount,
            address_index=args.address_index
        )

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
