#!/usr/bin/env python3
"""
Quick script to fund an Ethereum address from a Ganache test account
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardianvault.ethereum_rpc import EthereumRPCClient

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fund_ethereum_address.py <address> [amount_in_eth]")
        print("Example: python3 fund_ethereum_address.py 0x123... 10")
        sys.exit(1)

    target_address = sys.argv[1]
    amount_eth = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0

    # Connect to local Ganache
    rpc = EthereumRPCClient(host="localhost", port=8545)

    # Get Ganache accounts (pre-funded test accounts)
    accounts = rpc.get_accounts()

    if not accounts:
        print("❌ No accounts found. Make sure Ganache is running.")
        sys.exit(1)

    # Use first account as funding source
    funding_account = accounts[0]

    print(f"\nFunding Ethereum Address")
    print("=" * 70)
    print(f"From: {funding_account}")
    print(f"To: {target_address}")
    print(f"Amount: {amount_eth} ETH")
    print()

    # Check source balance
    source_balance = rpc.get_balance_eth(funding_account)
    print(f"Source balance: {source_balance:.6f} ETH")

    if source_balance < amount_eth:
        print(f"❌ Insufficient balance in funding account!")
        sys.exit(1)

    # Build transaction
    nonce = rpc.get_transaction_count(funding_account)

    tx = {
        'from': funding_account,
        'to': target_address,
        'value': hex(int(amount_eth * 10**18)),
        'gas': hex(21000),
        'gasPrice': rpc.rpc_call('eth_gasPrice')
    }

    # Send transaction
    print("Broadcasting transaction...")
    try:
        tx_hash = rpc.rpc_call('eth_sendTransaction', [tx])
        print(f"✓ Transaction sent: {tx_hash}")

        # Wait for confirmation
        print("Waiting for confirmation...")
        receipt = rpc.wait_for_transaction(tx_hash, timeout=30)

        if int(receipt['status'], 16) == 1:
            print(f"✓ Transaction confirmed in block {int(receipt['blockNumber'], 16)}")

            # Check new balance
            new_balance = rpc.get_balance_eth(target_address)
            print(f"\n✓ New balance: {new_balance:.6f} ETH")
        else:
            print("❌ Transaction failed!")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    print("\n✓ Funding complete!")


if __name__ == "__main__":
    main()
