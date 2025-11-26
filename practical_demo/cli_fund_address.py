#!/usr/bin/env python3
"""
Unified CLI for funding addresses on Bitcoin and Ethereum networks
"""
import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.bitcoin_rpc import BitcoinRPCClient
from utils.ethereum_rpc import EthereumRPCClient


def fund_bitcoin_address(address: str, amount: float, bitcoin_rpc: BitcoinRPCClient):
    """Fund a Bitcoin address from regtest wallet"""
    print(f"\n{'='*60}")
    print(f"Funding Bitcoin Address")
    print(f"{'='*60}")
    print(f"Address: {address}")
    print(f"Amount: {amount} BTC")
    print(f"{'='*60}\n")

    try:
        # Send funds to address
        txid = bitcoin_rpc.sendtoaddress(address, amount)
        print(f"✓ Sent {amount} BTC to {address}")
        print(f"  Transaction ID: {txid}")

        # Mine blocks to confirm
        print(f"✓ Mining 1 block to confirm...")
        miner_address = bitcoin_rpc.getnewaddress()
        bitcoin_rpc.generatetoaddress(1, miner_address)
        print(f"✓ Transaction confirmed")

        # Check balance
        result = bitcoin_rpc.scantxoutset("start", [f"addr({address})"])
        balance = result.get('total_amount', 0)
        print(f"\n✓ New balance: {balance} BTC")

        return txid
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def fund_ethereum_address(address: str, amount_eth: float, rpc: EthereumRPCClient):
    """Fund an Ethereum address from Ganache test account"""
    print(f"\n{'='*60}")
    print(f"Funding Ethereum Address")
    print(f"{'='*60}")
    print(f"Address: {address}")
    print(f"Amount: {amount_eth} ETH")
    print(f"{'='*60}\n")

    try:
        # Get Ganache accounts (pre-funded test accounts)
        accounts = rpc.get_accounts()

        if not accounts:
            print("❌ No accounts found. Make sure Ganache is running.")
            return None

        # Use first account as funding source
        funding_account = accounts[0]
        print(f"From: {funding_account}")

        # Check source balance
        source_balance = rpc.get_balance_eth(funding_account)
        print(f"Source balance: {source_balance:.6f} ETH")

        if source_balance < amount_eth:
            print(f"❌ Insufficient balance in funding account!")
            return None

        # Build transaction
        nonce = rpc.get_transaction_count(funding_account)

        tx = {
            'from': funding_account,
            'to': address,
            'value': hex(int(amount_eth * 10**18)),
            'gas': hex(21000),
            'gasPrice': rpc.rpc_call('eth_gasPrice')
        }

        # Send transaction
        print("Broadcasting transaction...")
        tx_hash = rpc.rpc_call('eth_sendTransaction', [tx])
        print(f"✓ Transaction sent: {tx_hash}")

        # Wait for confirmation
        print("Waiting for confirmation...")
        receipt = rpc.wait_for_transaction(tx_hash, timeout=30)

        if int(receipt['status'], 16) == 1:
            print(f"✓ Transaction confirmed in block {int(receipt['blockNumber'], 16)}")

            # Check new balance
            new_balance = rpc.get_balance_eth(address)
            print(f"\n✓ New balance: {new_balance:.6f} ETH")
        else:
            print("❌ Transaction failed!")
            return None

        return tx_hash

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def check_bitcoin_balance(address: str, bitcoin_rpc: BitcoinRPCClient):
    """Check balance of a Bitcoin address"""
    print(f"\n{'='*60}")
    print(f"Bitcoin Balance")
    print(f"{'='*60}")
    print(f"Address: {address}")
    print(f"{'='*60}\n")

    try:
        result = bitcoin_rpc.scantxoutset("start", [f"addr({address})"])
        total = result.get('total_amount', 0)
        unspents = result.get('unspents', [])

        print(f"Balance: {total} BTC")
        if unspents:
            print(f"\nUTXOs:")
            for utxo in unspents:
                print(f"  • {utxo['txid']}:{utxo['vout']} - {utxo['amount']} BTC")

        return total
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 0


def check_ethereum_balance(address: str, rpc: EthereumRPCClient):
    """Check balance of an Ethereum address"""
    print(f"\n{'='*60}")
    print(f"Ethereum Balance")
    print(f"{'='*60}")
    print(f"Address: {address}")
    print(f"{'='*60}\n")

    try:
        balance_eth = rpc.get_balance_eth(address)
        print(f"Balance: {balance_eth:.6f} ETH")
        return balance_eth
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Fund addresses on Bitcoin and Ethereum networks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fund Bitcoin address
  python3 cli_fund_address.py bitcoin \\
      --address bcrt1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh \\
      --amount 1.0

  # Fund Ethereum address
  python3 cli_fund_address.py ethereum \\
      --address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb \\
      --amount 10.0

  # Check Bitcoin balance
  python3 cli_fund_address.py bitcoin --check-balance \\
      --address bcrt1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh

  # Check Ethereum balance
  python3 cli_fund_address.py ethereum --check-balance \\
      --address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
        """
    )

    subparsers = parser.add_subparsers(dest='coin', help='Coin type', required=True)

    # Bitcoin subcommand
    bitcoin_parser = subparsers.add_parser('bitcoin', help='Bitcoin operations')
    bitcoin_parser.add_argument('--address', '-a', type=str, required=True,
                               help='Bitcoin address')
    bitcoin_parser.add_argument('--amount', type=float,
                               help='Amount in BTC (required for funding)')
    bitcoin_parser.add_argument('--check-balance', action='store_true',
                               help='Check address balance')
    bitcoin_parser.add_argument('--bitcoin-host', type=str, default='localhost',
                               help='Bitcoin RPC host (default: localhost)')
    bitcoin_parser.add_argument('--bitcoin-port', type=int, default=18443,
                               help='Bitcoin RPC port (default: 18443)')
    bitcoin_parser.add_argument('--bitcoin-user', type=str, default='regtest',
                               help='Bitcoin RPC username (default: regtest)')
    bitcoin_parser.add_argument('--bitcoin-password', type=str, default='regtest',
                               help='Bitcoin RPC password (default: regtest)')

    # Ethereum subcommand
    ethereum_parser = subparsers.add_parser('ethereum', help='Ethereum operations')
    ethereum_parser.add_argument('--address', '-a', type=str, required=True,
                                help='Ethereum address')
    ethereum_parser.add_argument('--amount', type=float,
                                help='Amount in ETH (required for funding)')
    ethereum_parser.add_argument('--check-balance', action='store_true',
                                help='Check address balance')
    ethereum_parser.add_argument('--rpc-host', type=str, default='localhost',
                                help='Ethereum RPC host (default: localhost)')
    ethereum_parser.add_argument('--rpc-port', type=int, default=8545,
                                help='Ethereum RPC port (default: 8545)')

    args = parser.parse_args()

    try:
        if args.coin == 'bitcoin':
            bitcoin_rpc = BitcoinRPCClient(
                host=args.bitcoin_host,
                port=args.bitcoin_port,
                user=args.bitcoin_user,
                password=args.bitcoin_password
            )

            if args.check_balance:
                check_bitcoin_balance(args.address, bitcoin_rpc)
            else:
                if not args.amount:
                    print("❌ Error: --amount is required for funding")
                    sys.exit(1)
                fund_bitcoin_address(args.address, args.amount, bitcoin_rpc)

        elif args.coin == 'ethereum':
            eth_rpc = EthereumRPCClient(
                host=args.rpc_host,
                port=args.rpc_port
            )

            if args.check_balance:
                check_ethereum_balance(args.address, eth_rpc)
            else:
                if not args.amount:
                    print("❌ Error: --amount is required for funding")
                    sys.exit(1)
                fund_ethereum_address(args.address, args.amount, eth_rpc)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
