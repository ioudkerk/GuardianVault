#!/usr/bin/env python3
"""
CLI 4: Transaction Signing Requester
Creates transaction signing requests and broadcasts to Bitcoin regtest
"""
import sys
import os
import json
import argparse
import asyncio
import aiohttp
import requests
from typing import Dict

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardianvault.mpc_keymanager import ExtendedPublicKey, PublicKeyDerivation
from guardianvault.mpc_addresses import BitcoinAddressGenerator
from guardianvault.bitcoin_transaction import BitcoinTransactionBuilder
from utils.bitcoin_rpc import BitcoinRPCClient


class TransactionRequester:
    """Transaction signing requester"""

    def __init__(self, server_url: str, bitcoin_rpc: BitcoinRPCClient = None):
        self.server_url = server_url
        self.base_api_url = f"{server_url}/api"
        self.bitcoin_rpc = bitcoin_rpc

    async def create_transaction(self, vault_id: str, recipient: str, amount: float, fee: float, memo: str = ""):
        """Create a transaction signing request"""
        print(f"\n{'='*60}")
        print(f"Creating Transaction Request")
        print(f"{'='*60}")
        print(f"Vault ID: {vault_id}")
        print(f"Recipient: {recipient}")
        print(f"Amount: {amount} BTC")
        print(f"Fee: {fee} BTC")
        print(f"Memo: {memo}")
        print(f"{'='*60}\n")

        tx_data = {
            "vault_id": vault_id,
            "type": "send",
            "coin_type": "bitcoin",
            "amount": str(amount),
            "recipient": recipient,
            "fee": str(fee),
            "memo": memo
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_api_url}/transactions",
                    json=tx_data
                ) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        print(f"✅ Transaction created successfully!")
                        print(f"  Transaction ID: {result['transaction_id']}")
                        print(f"  Status: {result['status']}")
                        print(f"  Message Hash: {result['message_hash'][:32]}...")
                        print(f"\n{'='*60}")
                        print("Guardians will now participate in signing...")
                        print(f"{'='*60}\n")
                        return result
                    else:
                        error = await response.text()
                        print(f"❌ Failed to create transaction: {error}")
                        return None
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                return None

    async def get_transaction(self, transaction_id: str):
        """Get transaction details"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_api_url}/transactions/{transaction_id}"
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                return None

    async def wait_for_signature(self, transaction_id: str, timeout: int = 60):
        """Wait for transaction to be signed"""
        print(f"⏳ Waiting for signature (timeout: {timeout}s)...")

        for i in range(timeout):
            tx = await self.get_transaction(transaction_id)
            if not tx:
                print(f"❌ Failed to get transaction status")
                return None

            status = tx['status']
            print(f"  [{i+1}/{timeout}] Status: {status}", end='\r')

            if status == 'completed':
                print(f"\n✅ Transaction signed successfully!")
                return tx
            elif status == 'failed':
                print(f"\n❌ Transaction signing failed")
                return None

            await asyncio.sleep(1)

        print(f"\n⏱️ Timeout waiting for signature")
        return None

    async def list_transactions(self, vault_id: str = None, status: str = None):
        """List transactions"""
        print(f"\n{'='*60}")
        print(f"Transactions")
        print(f"{'='*60}\n")

        url = f"{self.base_api_url}/transactions"
        params = []
        if vault_id:
            params.append(f"vault_id={vault_id}")
        if status:
            params.append(f"status={status}")

        if params:
            url += "?" + "&".join(params)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        transactions = await response.json()
                        if not transactions:
                            print("No transactions found.")
                            return

                        for tx in transactions:
                            print(f"Transaction: {tx['transaction_id']}")
                            print(f"  Status: {tx['status']}")
                            print(f"  Type: {tx['type']}")
                            print(f"  Amount: {tx.get('amount', 'N/A')}")
                            print(f"  Recipient: {tx.get('recipient', 'N/A')}")
                            print(f"  Created: {tx['created_at']}")
                            if tx.get('final_signature'):
                                print(f"  Signature: {tx['final_signature']['rHex'][:16]}...")
                            print()
                    else:
                        error = await response.text()
                        print(f"❌ Failed to list transactions: {error}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")

    def fund_address(self, address: str, amount: float):
        """Fund an address from Bitcoin regtest"""
        print(f"\n{'='*60}")
        print(f"Funding Address from Regtest")
        print(f"{'='*60}")
        print(f"Address: {address}")
        print(f"Amount: {amount} BTC")
        print(f"{'='*60}\n")

        try:
            # Send funds to address
            txid = self.bitcoin_rpc.sendtoaddress(address, amount)
            print(f"✓ Sent {amount} BTC to {address}")
            print(f"  Transaction ID: {txid}")

            # Mine blocks to confirm
            print(f"✓ Mining 1 block to confirm...")
            miner_address = self.bitcoin_rpc.getnewaddress()
            self.bitcoin_rpc.generatetoaddress(1, miner_address)
            print(f"✓ Transaction confirmed")

            return txid
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

    def check_balance(self, address: str):
        """Check balance of an address"""
        print(f"\n{'='*60}")
        print(f"Checking Balance")
        print(f"{'='*60}")
        print(f"Address: {address}")
        print(f"{'='*60}\n")

        try:
            # Use scantxoutset to find UTXOs for the address
            result = self.bitcoin_rpc.scantxoutset("start", [f"addr({address})"])
            total = result.get('total_amount', 0)
            unspents = result.get('unspents', [])

            print(f"Balance: {total} BTC")
            if unspents:
                print(f"\nUTXOs:")
                for utxo in unspents:
                    print(f"  • {utxo['txid']}:{utxo['vout']} - {utxo['amount']} BTC")

            return total, unspents
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return 0, []

    def broadcast_transaction(self, signed_tx_hex: str):
        """Broadcast a signed transaction to Bitcoin network"""
        print(f"\n{'='*60}")
        print(f"Broadcasting Transaction")
        print(f"{'='*60}\n")

        try:
            txid = self.bitcoin_rpc.sendrawtransaction(signed_tx_hex)
            print(f"✅ Transaction broadcast successfully!")
            print(f"  Transaction ID: {txid}")

            # Mine a block to confirm
            print(f"\n✓ Mining 1 block to confirm...")
            miner_address = self.bitcoin_rpc.getnewaddress()
            self.bitcoin_rpc.generatetoaddress(1, miner_address)
            print(f"✓ Transaction confirmed in block")

            # Get transaction details
            tx_details = self.bitcoin_rpc.getrawtransaction(txid, True)
            print(f"\nTransaction Details:")
            print(f"  Confirmations: {tx_details.get('confirmations', 0)}")
            print(f"  Size: {tx_details.get('size', 0)} bytes")

            return txid
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None


async def main():
    parser = argparse.ArgumentParser(
        description="Transaction signing requester and Bitcoin broadcaster",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fund an address from Bitcoin regtest
  python3 cli_transaction_requester.py fund-address \\
      --address bcrt1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh \\
      --amount 1.0

  # Check address balance
  python3 cli_transaction_requester.py check-balance \\
      --address bcrt1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh

  # Create transaction signing request
  python3 cli_transaction_requester.py create-transaction \\
      --vault-id vault_abc123 \\
      --recipient bcrt1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh \\
      --amount 0.5 \\
      --fee 0.0001 \\
      --memo "Demo payment"

  # Wait for transaction to be signed
  python3 cli_transaction_requester.py wait-for-signature \\
      --transaction-id tx_abc123

  # List transactions
  python3 cli_transaction_requester.py list-transactions --vault-id vault_abc123

  # Broadcast signed transaction
  python3 cli_transaction_requester.py broadcast \\
      --transaction-hex 0200000001abcd...
        """
    )

    parser.add_argument('--server', '-s', type=str, default='http://localhost:8000',
                       help='Coordination server URL')
    parser.add_argument('--bitcoin-host', type=str, default='localhost',
                       help='Bitcoin RPC host')
    parser.add_argument('--bitcoin-port', type=int, default=18443,
                       help='Bitcoin RPC port')
    parser.add_argument('--bitcoin-user', type=str, default='regtest',
                       help='Bitcoin RPC username')
    parser.add_argument('--bitcoin-password', type=str, default='regtest',
                       help='Bitcoin RPC password')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Fund address
    fund_parser = subparsers.add_parser('fund-address', help='Fund address from regtest')
    fund_parser.add_argument('--address', '-a', type=str, required=True,
                            help='Bitcoin address')
    fund_parser.add_argument('--amount', type=float, required=True,
                            help='Amount in BTC')

    # Check balance
    balance_parser = subparsers.add_parser('check-balance', help='Check address balance')
    balance_parser.add_argument('--address', '-a', type=str, required=True,
                               help='Bitcoin address')

    # Create transaction
    create_parser = subparsers.add_parser('create-transaction', help='Create transaction')
    create_parser.add_argument('--vault-id', '-v', type=str, required=True,
                              help='Vault ID')
    create_parser.add_argument('--recipient', '-r', type=str, required=True,
                              help='Recipient address')
    create_parser.add_argument('--amount', '-a', type=float, required=True,
                              help='Amount in BTC')
    create_parser.add_argument('--fee', '-f', type=float, required=True,
                              help='Fee in BTC')
    create_parser.add_argument('--memo', '-m', type=str, default='',
                              help='Transaction memo')

    # Wait for signature
    wait_parser = subparsers.add_parser('wait-for-signature', help='Wait for transaction signature')
    wait_parser.add_argument('--transaction-id', '-t', type=str, required=True,
                            help='Transaction ID')
    wait_parser.add_argument('--timeout', type=int, default=60,
                            help='Timeout in seconds')

    # List transactions
    list_parser = subparsers.add_parser('list-transactions', help='List transactions')
    list_parser.add_argument('--vault-id', '-v', type=str,
                            help='Filter by vault ID')
    list_parser.add_argument('--status', type=str,
                            help='Filter by status')

    # Broadcast transaction
    broadcast_parser = subparsers.add_parser('broadcast', help='Broadcast signed transaction')
    broadcast_parser.add_argument('--transaction-hex', '-t', type=str, required=True,
                                 help='Signed transaction hex')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize Bitcoin RPC client
    bitcoin_rpc = BitcoinRPCClient(
        host=args.bitcoin_host,
        port=args.bitcoin_port,
        user=args.bitcoin_user,
        password=args.bitcoin_password
    )

    requester = TransactionRequester(args.server, bitcoin_rpc)

    try:
        if args.command == 'fund-address':
            requester.fund_address(args.address, args.amount)
        elif args.command == 'check-balance':
            requester.check_balance(args.address)
        elif args.command == 'create-transaction':
            await requester.create_transaction(
                args.vault_id, args.recipient, args.amount, args.fee, args.memo
            )
        elif args.command == 'wait-for-signature':
            await requester.wait_for_signature(args.transaction_id, args.timeout)
        elif args.command == 'list-transactions':
            await requester.list_transactions(args.vault_id, args.status)
        elif args.command == 'broadcast':
            requester.broadcast_transaction(args.transaction_hex)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
