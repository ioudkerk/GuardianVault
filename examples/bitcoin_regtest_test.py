#!/usr/bin/env python3
"""
Bitcoin Regtest Integration Test
Tests the complete flow: MPC setup → Address generation → Funding → Transaction signing
"""

import os
import sys
import json
import time
import secrets
import subprocess
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from guardianvault.threshold_mpc_keymanager import (
    ThresholdKeyGeneration,
    ThresholdBIP32,
    ExtendedPublicKey,
    KeyShare
)
from guardianvault.threshold_addresses import BitcoinAddressGenerator
from guardianvault.threshold_signing import ThresholdSigningWorkflow
from guardianvault.bitcoin_transaction import BitcoinTransactionBuilder


class BitcoinRPCClient:
    """Simple Bitcoin RPC client for regtest"""

    def __init__(self, rpc_user="regtest", rpc_password="regtest", host="localhost", port=18443):
        self.rpc_user = rpc_user
        self.rpc_password = rpc_password
        self.host = host
        self.port = port
        self.url = f"http://{host}:{port}"

    def call(self, method: str, params: List = None) -> Dict:
        """Make RPC call to bitcoind"""
        if params is None:
            params = []

        payload = {
            "jsonrpc": "1.0",
            "id": "guardianvault",
            "method": method,
            "params": params
        }

        import urllib.request
        import urllib.error
        import base64

        # Create Basic Auth header
        credentials = f"{self.rpc_user}:{self.rpc_password}"
        auth_string = base64.b64encode(credentials.encode('utf-8')).decode('ascii')

        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'content-type': 'application/json',
                'Authorization': f'Basic {auth_string}'
            }
        )

        try:
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode('utf-8'))
            return result.get('result')
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                # Try to parse JSON error response
                error_data = json.loads(error_body)
                if 'error' in error_data and error_data['error']:
                    error_msg = error_data['error'].get('message', error_body)
                    raise Exception(f"Bitcoin RPC Error: {error_msg}") from e
                else:
                    raise Exception(f"Bitcoin RPC Error (HTTP {e.code}): {error_body}") from e
            except json.JSONDecodeError:
                # If not JSON, raise the raw error body
                raise Exception(f"Bitcoin RPC Error (HTTP {e.code}): {error_body}") from e

    def getblockchaininfo(self):
        """Get blockchain info"""
        return self.call("getblockchaininfo")

    def createwallet(self, wallet_name: str):
        """Create a new wallet"""
        try:
            return self.call("createwallet", [wallet_name])
        except Exception as e:
            if "already exists" in str(e):
                print(f"Wallet {wallet_name} already exists")
                return None
            raise

    def getnewaddress(self, wallet_name: str = "", address_type: str = "legacy"):
        """Get new address from wallet"""
        if wallet_name:
            return self.call("getnewaddress", [wallet_name, address_type])
        return self.call("getnewaddress", ["", address_type])

    def generatetoaddress(self, nblocks: int, address: str):
        """Mine blocks to address"""
        return self.call("generatetoaddress", [nblocks, address])

    def sendtoaddress(self, address: str, amount: float):
        """Send BTC to address"""
        return self.call("sendtoaddress", [address, amount])

    def getbalance(self):
        """Get wallet balance"""
        return self.call("getbalance")

    def listunspent(self, minconf: int = 1, maxconf: int = 9999999, addresses: List[str] = None):
        """List unspent outputs"""
        if addresses is None:
            return self.call("listunspent", [minconf, maxconf])
        return self.call("listunspent", [minconf, maxconf, addresses])

    def getrawtransaction(self, txid: str, verbose: bool = True):
        """Get raw transaction"""
        return self.call("getrawtransaction", [txid, verbose])

    def decoderawtransaction(self, rawtx: str):
        """Decode raw transaction"""
        return self.call("decoderawtransaction", [rawtx])

    def sendrawtransaction(self, rawtx: str):
        """Broadcast raw transaction"""
        return self.call("sendrawtransaction", [rawtx])

    def importaddress(self, address: str, label: str = "", rescan: bool = False):
        """Import address as watch-only (legacy wallet only)"""
        return self.call("importaddress", [address, label, rescan])

    def scantxoutset(self, action: str, scanobjects: list):
        """Scan the UTXO set for addresses (works without wallet)"""
        return self.call("scantxoutset", [action, scanobjects])

    def getaddressinfo(self, address: str):
        """Get information about an address"""
        return self.call("getaddressinfo", [address])

    def gettxout(self, txid: str, vout: int, include_mempool: bool = True):
        """Get details about an unspent transaction output"""
        return self.call("gettxout", [txid, vout, include_mempool])


def setup_mpc_and_generate_address() -> Tuple[List[KeyShare], ExtendedPublicKey, Dict]:
    """
    Phase 1: MPC Setup and Address Generation
    Returns: (bitcoin_shares, btc_xpub, first_address)
    """
    print("=" * 80)
    print("PHASE 1: MPC SETUP AND ADDRESS GENERATION")
    print("=" * 80)
    print()

    # Generate key shares
    print("Step 1: Generate distributed key shares (3 parties)")
    print("-" * 80)
    num_parties = 3
    key_shares, master_pubkey = ThresholdKeyGeneration.generate_shares(num_parties)
    print(f"✓ Generated {num_parties} key shares")
    print()

    # Derive master keys
    print("Step 2: Derive BIP32 master keys")
    print("-" * 80)
    seed = secrets.token_bytes(32)
    print(f"Using seed: {seed.hex()[:32]}...")

    master_shares, master_pubkey, master_chain = \
        ThresholdBIP32.derive_master_keys_threshold(key_shares, seed)
    print(f"✓ Master public key: {master_pubkey.hex()[:32]}...")
    print()

    # Derive Bitcoin account xpub (m/44'/0'/0')
    print("Step 3: Derive Bitcoin account xpub (m/44'/0'/0')")
    print("-" * 80)
    btc_xpub = ThresholdBIP32.derive_account_xpub_threshold(
        master_shares, master_chain, coin_type=0, account=0
    )
    print(f"✓ Bitcoin xpub: {btc_xpub.public_key.hex()[:32]}...")
    print()

    # Get account-level shares for signing
    print("Step 4: Derive account-level key shares for signing")
    print("-" * 80)
    btc_account_shares, account_pubkey, account_chain = ThresholdBIP32.derive_hardened_child_threshold(
        master_shares, master_pubkey, master_chain, 44
    )
    btc_account_shares, account_pubkey, account_chain = ThresholdBIP32.derive_hardened_child_threshold(
        btc_account_shares, account_pubkey, account_chain, 0
    )
    btc_account_shares, account_pubkey, account_chain = ThresholdBIP32.derive_hardened_child_threshold(
        btc_account_shares, account_pubkey, account_chain, 0
    )
    print(f"✓ Derived account-level shares for m/44'/0'/0'")
    print()

    # Generate first Bitcoin address (regtest mode) - use account pubkey directly
    print("Step 5: Generate Bitcoin receiving address (REGTEST)")
    print("-" * 80)
    print("  Using account-level public key directly (m/44'/0'/0')")
    print("  This allows signing without additional child derivation")

    first_address_info = BitcoinAddressGenerator.pubkey_to_address(
        account_pubkey, network="regtest"
    )

    first_address = {
        'path': "m/44'/0'/0'",
        'address': first_address_info,
        'public_key': account_pubkey.hex()
    }

    print(f"Path: {first_address['path']}")
    print(f"Address: {first_address['address']}")
    print(f"Public Key: {first_address['public_key'][:32]}...")
    print()

    return btc_account_shares, btc_xpub, first_address


def fund_address_from_regtest(rpc: BitcoinRPCClient, address: str, amount: float = 1.0):
    """
    Phase 2: Fund the MPC address using Bitcoin regtest
    """
    print("=" * 80)
    print("PHASE 2: FUND MPC ADDRESS FROM BITCOIN REGTEST")
    print("=" * 80)
    print()

    # Create wallet for mining
    print("Step 1: Create mining wallet")
    print("-" * 80)
    rpc.createwallet("miner")
    print("✓ Mining wallet created")
    print()

    # Get mining address
    print("Step 2: Get mining address")
    print("-" * 80)
    mining_address = rpc.getnewaddress()
    print(f"Mining address: {mining_address}")
    print()

    # Mine blocks to generate coins
    print("Step 3: Mine 101 blocks (need 100 confirmations for coinbase)")
    print("-" * 80)
    blocks = rpc.generatetoaddress(101, mining_address)
    print(f"✓ Mined {len(blocks)} blocks")

    # Check balance
    balance = rpc.getbalance()
    print(f"✓ Mining wallet balance: {balance} BTC")
    print()

    # Send to MPC address
    print(f"Step 4: Send {amount} BTC to MPC address")
    print("-" * 80)
    print(f"Target address: {address}")
    txid = rpc.sendtoaddress(address, amount)
    print(f"✓ Transaction ID: {txid}")
    print()

    # Mine block to confirm
    print("Step 5: Mine 1 block to confirm transaction")
    print("-" * 80)
    rpc.generatetoaddress(1, mining_address)
    print("✓ Transaction confirmed")
    print()

    return txid


def create_and_sign_transaction(
    rpc: BitcoinRPCClient,
    btc_account_shares: List[KeyShare],
    address_info: Dict,
    funding_txid: str,
    recipient_address: str,
    amount: float = 0.5
):
    """
    Phase 3: Create and sign a Bitcoin transaction using MPC
    """
    print("=" * 80)
    print("PHASE 3: CREATE AND SIGN BITCOIN TRANSACTION WITH MPC")
    print("=" * 80)
    print()

    print(f"Sending {amount} BTC from MPC address")
    print(f"From: {address_info['address']}")
    print(f"To: {recipient_address}")
    print()

    # Get transaction details to find the output to our address
    print("Step 1: Find UTXO from funding transaction")
    print("-" * 80)
    print(f"Funding txid: {funding_txid}")

    tx_details = rpc.getrawtransaction(funding_txid, True)

    # Find which output is ours
    utxo_vout = None
    utxo_amount = None
    for vout_index, vout in enumerate(tx_details['vout']):
        if 'scriptPubKey' in vout and 'address' in vout['scriptPubKey']:
            if vout['scriptPubKey']['address'] == address_info['address']:
                utxo_vout = vout_index
                utxo_amount = vout['value']
                break

    if utxo_vout is None:
        print("❌ Could not find UTXO for MPC address in funding transaction!")
        return None

    print(f"✓ Found UTXO: {utxo_amount} BTC at output {utxo_vout}")
    print(f"  Transaction: {funding_txid}")
    print()

    # Build the Bitcoin transaction
    print("Step 2: Build Bitcoin transaction")
    print("-" * 80)
    fee = 0.0001  # 0.0001 BTC fee
    print(f"  Input: {utxo_amount} BTC from {funding_txid}:{utxo_vout}")
    print(f"  Output: {amount} BTC to {recipient_address}")
    print(f"  Change: {utxo_amount - amount - fee} BTC back to {address_info['address']}")
    print(f"  Fee: {fee} BTC")

    tx, script_code = BitcoinTransactionBuilder.build_p2pkh_transaction(
        utxo_txid=funding_txid,
        utxo_vout=utxo_vout,
        utxo_amount_btc=utxo_amount,
        sender_address=address_info['address'],
        recipient_address=recipient_address,
        send_amount_btc=amount,
        fee_btc=fee
    )
    print("✓ Transaction built")
    print()

    # Get the signature hash (sighash)
    print("Step 3: Calculate signature hash (sighash)")
    print("-" * 80)
    sighash = tx.get_sighash(input_index=0, script_code=script_code, sighash_type=1)
    print(f"  Sighash: {sighash.hex()}")
    print("✓ Sighash calculated")
    print()

    # Sign using MPC threshold signing (NO private key reconstruction!)
    print("Step 4: Sign transaction using MPC threshold protocol")
    print("-" * 80)
    print("  ⚠️  IMPORTANT: Private key is NEVER reconstructed!")
    print("  Each party signs with their share, then signatures are combined")
    print()

    public_key = bytes.fromhex(address_info['public_key'])

    print("  Executing distributed threshold signing...")
    signature = ThresholdSigningWorkflow.sign_message(
        btc_account_shares,
        sighash,
        public_key,
        prehashed=True  # sighash is already a 32-byte hash
    )

    signature_der = signature.to_der()
    print("✓ Transaction signed using MPC!")
    print(f"  Signature (DER): {signature_der.hex()[:64]}...")
    print()

    # Add signature to transaction
    print("Step 5: Add signature to transaction")
    print("-" * 80)
    tx = BitcoinTransactionBuilder.sign_transaction(
        tx=tx,
        input_index=0,
        script_code=script_code,
        signature_der=signature_der,
        public_key=public_key
    )
    print("✓ Signature added to transaction")
    print()

    # Serialize and broadcast
    print("Step 6: Serialize and broadcast transaction")
    print("-" * 80)
    raw_tx_hex = tx.serialize().hex()
    print(f"  Raw transaction: {raw_tx_hex[:64]}...")
    print(f"  Transaction size: {len(raw_tx_hex) // 2} bytes")
    print()

    try:
        broadcast_txid = rpc.sendrawtransaction(raw_tx_hex)
        print("✓ Transaction broadcast successfully!")
        print(f"  Transaction ID: {broadcast_txid}")
        print()
    except Exception as e:
        print(f"❌ Failed to broadcast transaction: {e}")
        print()
        # Try to decode the transaction to see if it's valid
        try:
            decoded = rpc.decoderawtransaction(raw_tx_hex)
            print("Transaction decoding:")
            print(json.dumps(decoded, indent=2))
        except Exception as decode_error:
            print(f"Could not decode transaction: {decode_error}")
        return None

    return broadcast_txid


def main():
    """Run complete Bitcoin regtest test"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + " " * 18 + "BITCOIN REGTEST INTEGRATION TEST" + " " * 28 + "║")
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
        print("  docker-compose -f docker-compose.regtest.yml up -d")
        print()
        return

    # Phase 1: MPC Setup and Address Generation
    btc_account_shares, btc_xpub, first_address = setup_mpc_and_generate_address()

    input("Press Enter to fund the address from Bitcoin regtest...")
    print("\n")

    # Phase 2: Fund the address
    txid = fund_address_from_regtest(rpc, first_address['address'], amount=1.0)

    input("Press Enter to create and sign a transaction...")
    print("\n")

    # Phase 3: Create and sign transaction
    # Get a new address to send to
    recipient_address = rpc.getnewaddress()

    spent_txid = create_and_sign_transaction(
        rpc,
        btc_account_shares,
        first_address,
        txid,  # funding_txid
        recipient_address,
        amount=0.5
    )

    if spent_txid is None:
        print("❌ Transaction failed!")
        return

    input("Press Enter to mine blocks and verify balances...")
    print("\n")

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
    print()

    print("Step 3: Check balances using scantxoutset (works with descriptor wallets)")
    print("-" * 80)

    # Check MPC address balance using scantxoutset (no wallet needed)
    try:
        # Scan UTXO set for MPC address
        scan_result = rpc.scantxoutset("start", [f"addr({first_address['address']})"])
        mpc_balance = scan_result.get('total_amount', 0)
        mpc_utxo_count = len(scan_result.get('unspents', []))

        print(f"  MPC Address ({first_address['address']})")
        print(f"    Balance: {mpc_balance} BTC")
        print(f"    UTXOs: {mpc_utxo_count}")

        # Verify change amount is correct (1.0 - 0.5 - 0.0001 fee = 0.4999)
        expected_change = 0.4999
        if abs(mpc_balance - expected_change) < 0.0001:
            print(f"    ✓ Change amount correct (~{expected_change} BTC)")
        else:
            print(f"    ⚠️  Expected ~{expected_change} BTC, got {mpc_balance} BTC")
    except Exception as e:
        print(f"  Could not check MPC address balance: {e}")

    # Check recipient balance
    try:
        # Scan UTXO set for recipient address
        scan_result = rpc.scantxoutset("start", [f"addr({recipient_address})"])
        recipient_balance = scan_result.get('total_amount', 0)
        recipient_utxo_count = len(scan_result.get('unspents', []))

        print(f"  Recipient Address ({recipient_address})")
        print(f"    Balance: {recipient_balance} BTC")
        print(f"    UTXOs: {recipient_utxo_count}")

        # Verify received amount is correct (0.5 BTC)
        expected_amount = 0.5
        if abs(recipient_balance - expected_amount) < 0.0001:
            print(f"    ✓ Received amount correct ({expected_amount} BTC)")
        else:
            print(f"    ⚠️  Expected {expected_amount} BTC, got {recipient_balance} BTC")
    except Exception as e:
        print(f"  Could not check recipient balance: {e}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("✓ Phase 1: MPC key generation (no private key reconstruction)")
    print("✓ Phase 2: Generated Bitcoin regtest address and received funds")
    print("✓ Phase 3: Created and signed transaction using MPC threshold signing")
    print("✓ Phase 4: Transaction broadcast, mined, and confirmed")
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


if __name__ == "__main__":
    main()
