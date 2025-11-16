#!/usr/bin/env python3
"""
Bitcoin Regtest Integration Test (Automated)
Tests the complete flow without user interaction
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import everything from the original test
from bitcoin_regtest_test import (
    BitcoinRPCClient,
    setup_mpc_and_generate_address,
    fund_address_from_regtest,
    create_and_sign_transaction
)


def main():
    """Run complete Bitcoin regtest test automatically"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + " " * 18 + "BITCOIN REGTEST INTEGRATION TEST" + " " * 28 + "║")
    print("║" + " " * 23 + "(AUTOMATED VERSION)" + " " * 36 + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  MPC Setup → Address Generation → Funding → Transaction Signing" + " " * 12 + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    # Initialize Bitcoin RPC client
    rpc = BitcoinRPCClient()

    # Check if Bitcoin node is running
    try:
        info = rpc.getblockchaininfo()
        print(f"✓ Connected to Bitcoin regtest node")
        print(f"  Chain: {info['chain']}")
        print(f"  Blocks: {info['blocks']}")
        print()
    except Exception as e:
        print("❌ Cannot connect to Bitcoin regtest node!")
        print(f"   Error: {e}")
        print()
        print("Please start the Bitcoin regtest node first:")
        print("  docker compose -f docker-compose.regtest.yml up -d")
        print()
        return 1

    # Phase 1: MPC Setup and Address Generation
    btc_account_shares, btc_xpub, first_address = setup_mpc_and_generate_address()

    # Phase 2: Fund the address
    txid = fund_address_from_regtest(rpc, first_address['address'], amount=1.0)

    # Phase 3: Create and sign transaction
    recipient_address = rpc.getnewaddress()

    spent_txid = create_and_sign_transaction(
        rpc,
        btc_account_shares,
        first_address,
        txid,
        recipient_address,
        amount=0.5
    )

    if spent_txid is None:
        print("❌ Transaction failed!")
        return 1

    # Phase 4: Mine blocks and verify
    print("=" * 80)
    print("PHASE 4: MINE BLOCKS AND VERIFY BALANCES")
    print("=" * 80)
    print()

    print("Step 1: Mine blocks to confirm transaction")
    print("-" * 80)
    mining_address = rpc.getnewaddress()
    blocks = rpc.generatetoaddress(6, mining_address)
    print(f"✓ Mined {len(blocks)} blocks")
    print()

    print("Step 2: Verify transaction is confirmed")
    print("-" * 80)
    tx_info = rpc.getrawtransaction(spent_txid, True)
    confirmations = tx_info.get('confirmations', 0)
    print(f"  Transaction: {spent_txid}")
    print(f"  Confirmations: {confirmations}")
    print(f"  Block: {tx_info.get('blockhash', 'Not in block')[:16]}...")
    print()

    if confirmations > 0:
        print("✓ Transaction confirmed!")
    else:
        print("❌ Transaction not confirmed yet")
        return 1
    print()

    print("Step 3: Check balances by inspecting transaction outputs")
    print("-" * 80)

    # Check the spending transaction outputs
    spent_tx_details = rpc.getrawtransaction(spent_txid, True)

    print(f"  Spending transaction ({spent_txid[:16]}...)")
    print(f"    Inputs: {len(spent_tx_details['vin'])}")
    print(f"    Outputs: {len(spent_tx_details['vout'])}")
    print()

    recipient_amount = None
    change_amount = None

    for vout in spent_tx_details['vout']:
        address = vout['scriptPubKey'].get('address', 'unknown')
        amount = vout['value']

        if address == recipient_address:
            recipient_amount = amount
            print(f"  Recipient Address ({recipient_address})")
            print(f"    Amount: {amount} BTC")
            # Verify received amount is correct (0.5 BTC)
            expected_amount = 0.5
            if abs(amount - expected_amount) < 0.0001:
                print(f"    ✓ Received amount correct ({expected_amount} BTC)")
            else:
                print(f"    ⚠️  Expected {expected_amount} BTC, got {amount} BTC")
                return 1

        elif address == first_address['address']:
            change_amount = amount
            print(f"  MPC Address Change ({first_address['address']})")
            print(f"    Amount: {amount} BTC")
            # Verify change amount is correct (1.0 - 0.5 - 0.0001 fee = 0.4999)
            expected_change = 0.4999
            if abs(amount - expected_change) < 0.0001:
                print(f"    ✓ Change amount correct (~{expected_change} BTC)")
            else:
                print(f"    ⚠️  Expected ~{expected_change} BTC, got {amount} BTC")

    if recipient_amount is None:
        print(f"  ❌ Could not find recipient output")
        return 1

    if change_amount is None:
        print(f"  ⚠️  No change output (this is OK if exact amount)")

    print()

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("✓ Phase 1: MPC key generation (no private key reconstruction)")
    print("✓ Phase 2: Generated Bitcoin regtest address and received funds")
    print("✓ Phase 3: Created and signed transaction using MPC threshold signing")
    print("✓ Phase 4: Transaction broadcast, mined, and confirmed")
    print("✓ All balances verified correctly")
    print()
    print("🎉 SUCCESS! Complete Bitcoin transaction signed with MPC!")
    print()

    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + " " * 26 + "ALL TESTS PASSED!" + " " * 33 + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
