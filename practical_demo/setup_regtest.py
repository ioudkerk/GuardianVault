#!/usr/bin/env python3
"""
Bitcoin Regtest Setup Script
Initializes the Bitcoin regtest environment with wallet and initial blocks
"""
import sys
import os
import time

# Add utils to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.bitcoin_rpc import BitcoinRPCClient as BaseRPCClient


class BitcoinRPCClient(BaseRPCClient):
    """Extended Bitcoin RPC client for setup script with error handling"""

    def rpc_call_safe(self, method, params=[], use_wallet=False):
        """Make RPC call with error handling for setup script"""
        try:
            result = self.rpc_call(method, params, use_wallet)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def getblockchaininfo(self):
        return self.rpc_call_safe("getblockchaininfo")

    def listwallets(self):
        return self.rpc_call_safe("listwallets")

    def createwallet(self, wallet_name, disable_private_keys=False, blank=False, passphrase="",
                     avoid_reuse=False, descriptors=True, load_on_startup=True):
        return self.rpc_call_safe("createwallet", [
            wallet_name,
            disable_private_keys,
            blank,
            passphrase,
            avoid_reuse,
            descriptors,
            load_on_startup
        ])

    def loadwallet(self, wallet_name):
        return self.rpc_call_safe("loadwallet", [wallet_name])

    def getnewaddress(self, label="", address_type="bech32"):
        return self.rpc_call_safe("getnewaddress", [label, address_type], use_wallet=True)

    def generatetoaddress(self, nblocks, address):
        return self.rpc_call_safe("generatetoaddress", [nblocks, address])

    def getbalance(self):
        return self.rpc_call_safe("getbalance", use_wallet=True)

    def getblockcount(self):
        return self.rpc_call_safe("getblockcount")


def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_step(step, title):
    """Print step header"""
    print(f"{'─'*70}")
    print(f"Step {step}: {title}")
    print(f"{'─'*70}")


def setup_regtest():
    """Setup Bitcoin regtest environment"""
    print_header("Bitcoin Regtest Setup")

    rpc = BitcoinRPCClient()

    # Step 1: Check connection
    print_step(1, "Checking Bitcoin Core connection")
    result = rpc.getblockchaininfo()
    if not result["success"]:
        print(f"❌ Failed to connect to Bitcoin Core")
        print(f"   Error: {result['error']}")
        print(f"\n   Make sure Bitcoin regtest is running:")
        print(f"   docker compose -f ../docker-compose.regtest.yml up -d")
        return False

    info = result["result"]
    print(f"✓ Connected to Bitcoin Core")
    print(f"  Chain: {info['chain']}")
    print(f"  Blocks: {info['blocks']}")
    print()

    # Step 2: Check/Create wallet
    print_step(2, "Setting up wallet")

    # List existing wallets
    wallets_result = rpc.listwallets()
    if not wallets_result["success"]:
        print(f"❌ Failed to list wallets: {wallets_result['error']}")
        return False

    existing_wallets = wallets_result["result"]
    wallet_name = "regtest_wallet"

    if wallet_name in existing_wallets:
        print(f"✓ Wallet '{wallet_name}' is already loaded")
    else:
        # Try to load wallet first (in case it exists but isn't loaded)
        print(f"  Attempting to load existing wallet '{wallet_name}'...")
        load_result = rpc.loadwallet(wallet_name)

        if load_result["success"]:
            print(f"✓ Loaded existing wallet '{wallet_name}'")
        else:
            # Wallet doesn't exist, create it
            print(f"  Creating new wallet '{wallet_name}'...")
            create_result = rpc.createwallet(
                wallet_name=wallet_name,
                disable_private_keys=False,
                blank=False,
                descriptors=True,
                load_on_startup=True
            )

            if not create_result["success"]:
                print(f"❌ Failed to create wallet: {create_result['error']}")
                return False

            print(f"✓ Created new wallet '{wallet_name}'")
    print()

    # Step 3: Check block count and generate initial blocks if needed
    print_step(3, "Generating initial blocks")

    blockcount_result = rpc.getblockcount()
    if not blockcount_result["success"]:
        print(f"❌ Failed to get block count: {blockcount_result['error']}")
        return False

    current_blocks = blockcount_result["result"]
    print(f"  Current blocks: {current_blocks}")

    # Need at least 101 blocks for coinbase maturity (100 confirmations)
    if current_blocks < 101:
        blocks_needed = 101 - current_blocks
        print(f"  Generating {blocks_needed} blocks for coinbase maturity...")

        addr_result = rpc.getnewaddress()
        if not addr_result["success"]:
            print(f"❌ Failed to get address: {addr_result['error']}")
            return False

        address = addr_result["result"]

        generate_result = rpc.generatetoaddress(blocks_needed, address)
        if not generate_result["success"]:
            print(f"❌ Failed to generate blocks: {generate_result['error']}")
            return False

        print(f"✓ Generated {blocks_needed} blocks to address {address}")
    else:
        print(f"✓ Sufficient blocks already generated")
    print()

    # Step 4: Check wallet balance
    print_step(4, "Checking wallet balance")

    balance_result = rpc.getbalance()
    if not balance_result["success"]:
        print(f"❌ Failed to get balance: {balance_result['error']}")
        return False

    balance = balance_result["result"]
    print(f"✓ Wallet balance: {balance} BTC")

    if balance == 0:
        print(f"  Generating 10 more blocks to get some BTC...")
        addr_result = rpc.getnewaddress()
        if addr_result["success"]:
            generate_result = rpc.generatetoaddress(10, addr_result["result"])
            if generate_result["success"]:
                balance_result = rpc.getbalance()
                if balance_result["success"]:
                    balance = balance_result["result"]
                    print(f"✓ New balance: {balance} BTC")
    print()

    # Step 5: Summary
    print_header("Setup Complete!")
    print("Your Bitcoin regtest environment is ready!")
    print()
    print("Summary:")
    print(f"  ✓ Wallet loaded: {wallet_name}")
    print(f"  ✓ Current blocks: {current_blocks + (101 - current_blocks if current_blocks < 101 else 0)}")
    print(f"  ✓ Available balance: {balance} BTC")
    print()
    print("You can now:")
    print("  1. Fund addresses using:")
    print("     python3 cli_transaction_requester.py fund-address -a <ADDRESS> --amount 1.0")
    print()
    print("  2. Check balances:")
    print("     python3 cli_transaction_requester.py check-balance -a <ADDRESS>")
    print()
    print(f"{'='*70}\n")

    return True


def main():
    """Main function"""
    print("\nBitcoin Regtest Environment Setup")
    print("This script will:")
    print("  1. Check connection to Bitcoin Core")
    print("  2. Create/load a regtest wallet")
    print("  3. Generate initial blocks (if needed)")
    print("  4. Ensure the wallet has funds")
    print()

    try:
        success = setup_regtest()
        if success:
            sys.exit(0)
        else:
            print("\n❌ Setup failed. Please check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
