#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/ivan/projects/personal/GuardianVault')

import json
import requests

# Step 1: Create a P2WPKH transaction with Bitcoin Core
print("=" * 70)
print("Creating reference P2WPKH transaction with Bitcoin Core")
print("=" * 70)

# Get a new address from Core wallet
response = requests.post(
    "http://regtest:regtest@localhost:18443/wallet/regtest_wallet",
    json={"jsonrpc": "1.0", "id": "test", "method": "getnewaddress", "params": ["", "bech32"]}
)
core_address = response.json()['result']
print(f"\nCore wallet P2WPKH address: {core_address}")

# Send 0.5 BTC to it
response = requests.post(
    "http://regtest:regtest@localhost:18443/wallet/regtest_wallet",
    json={"jsonrpc": "1.0", "id": "test", "method": "sendtoaddress", "params": [core_address, 0.5]}
)
funding_txid = response.json()['result']
print(f"Funding TXID: {funding_txid}")

# Mine a block
response = requests.post(
    "http://regtest:regtest@localhost:18443/wallet/regtest_wallet",
    json={"jsonrpc": "1.0", "id": "test", "method": "getnewaddress", "params": []}
)
miner_addr = response.json()['result']

response = requests.post(
    "http://regtest:regtest@localhost:18443",
    json={"jsonrpc": "1.0", "id": "test", "method": "generatetoaddress", "params": [1, miner_addr]}
)
print("Mined 1 block")

# Now create a transaction spending from this UTXO
recipient = "bcrt1qylv06qrwvq2j2yzwum8gk0xspm894k83gag2tj"

# Get the UTXO details
response = requests.post(
    "http://regtest:regtest@localhost:18443",
    json={"jsonrpc": "1.0", "id": "test", "method": "getrawtransaction", "params": [funding_txid, True]}
)
funding_tx = response.json()['result']

# Find which vout has our address
vout_idx = None
for vout in funding_tx['vout']:
    if vout['scriptPubKey'].get('address') == core_address:
        vout_idx = vout['n']
        break

print(f"UTXO vout: {vout_idx}")

# Create raw transaction
utxo = {"txid": funding_txid, "vout": vout_idx}
outputs = {recipient: 0.3}

response = requests.post(
    "http://regtest:regtest@localhost:18443/wallet/regtest_wallet",
    json={"jsonrpc": "1.0", "id": "test", "method": "createrawtransaction", "params": [[utxo], outputs]}
)
unsigned_tx_hex = response.json()['result']
print(f"\nUnsigned tx: {unsigned_tx_hex[:80]}...")

# Sign it with wallet
response = requests.post(
    "http://regtest:regtest@localhost:18443/wallet/regtest_wallet",
    json={"jsonrpc": "1.0", "id": "test", "method": "signrawtransactionwithwallet", "params": [unsigned_tx_hex]}
)
result = response.json()['result']
signed_tx_hex = result['hex']
complete = result['complete']

print(f"Signed tx: {signed_tx_hex[:80]}...")
print(f"Complete: {complete}")

# Decode the signed transaction
response = requests.post(
    "http://regtest:regtest@localhost:18443",
    json={"jsonrpc": "1.0", "id": "test", "method": "decoderawtransaction", "params": [signed_tx_hex]}
)
decoded = response.json()['result']

print(f"\n" + "=" * 70)
print("Core wallet P2WPKH transaction structure:")
print("=" * 70)
print(json.dumps(decoded, indent=2))

# Now let's compare with our MPC transaction
print(f"\n" + "=" * 70)
print("Comparing with our MPC P2WPKH transaction:")
print("=" * 70)

tx_resp = requests.get("http://localhost:8000/api/transactions/tx_QwKiG6Qg7Xes")
our_tx = tx_resp.json()

from guardianvault.bitcoin_transaction import BitcoinTransactionBuilder
from guardianvault.threshold_mpc_keymanager import ExtendedPublicKey, PublicKeyDerivation

with open('demo_output/vault_config.json', 'r') as f:
    vault_config = json.load(f)

xpub = ExtendedPublicKey.from_dict(vault_config['bitcoin']['xpub'])
pubkeys = PublicKeyDerivation.derive_address_public_keys(xpub, change=0, num_addresses=3)
pubkey = pubkeys[2]

tx_builder, script_code, sender_type, utxo_amount_sats = BitcoinTransactionBuilder.build_p2pkh_transaction(
    utxo_txid=our_tx['utxo_txid'],
    utxo_vout=our_tx['utxo_vout'],
    utxo_amount_btc=float(our_tx['utxo_amount']),
    sender_address=our_tx['sender_address'],
    recipient_address=our_tx['recipient'],
    send_amount_btc=float(our_tx['amount']),
    fee_btc=float(our_tx['fee'])
)

sig_der = bytes.fromhex(our_tx['final_signature']['der'])

signed_tx = BitcoinTransactionBuilder.sign_transaction(
    tx_builder,
    input_index=0,
    script_code=script_code,
    signature_der=sig_der,
    public_key=pubkey,
    sender_type=sender_type
)

our_tx_hex = signed_tx.serialize().hex()
print(f"Our tx: {our_tx_hex[:80]}...")

# Decode our transaction
response = requests.post(
    "http://regtest:regtest@localhost:18443",
    json={"jsonrpc": "1.0", "id": "test", "method": "decoderawtransaction", "params": [our_tx_hex]}
)
our_decoded = response.json()['result']

print(f"\nOur MPC transaction structure:")
print(json.dumps(our_decoded, indent=2))

# Compare key fields
print(f"\n" + "=" * 70)
print("Key differences:")
print("=" * 70)

print(f"\nCore witness items: {len(decoded['vin'][0]['txinwitness'])}")
print(f"Our witness items:  {len(our_decoded['vin'][0]['txinwitness'])}")

print(f"\nCore witness[0] (sig) length: {len(decoded['vin'][0]['txinwitness'][0])//2} bytes")
print(f"Our witness[0] (sig) length:  {len(our_decoded['vin'][0]['txinwitness'][0])//2} bytes")

print(f"\nCore witness[1] (pubkey): {decoded['vin'][0]['txinwitness'][1][:40]}...")
print(f"Our witness[1] (pubkey):  {our_decoded['vin'][0]['txinwitness'][1][:40]}...")

# Test Core's transaction
print(f"\n" + "=" * 70)
print("Testing Core's transaction:")
print("=" * 70)
response = requests.post(
    "http://regtest:regtest@localhost:18443",
    json={"jsonrpc": "1.0", "id": "test", "method": "testmempoolaccept", "params": [[signed_tx_hex]]}
)
test_result = response.json()['result'][0]
print(f"Core tx accepted: {test_result['allowed']}")
if not test_result['allowed']:
    print(f"Reject reason: {test_result.get('reject-reason', 'N/A')}")

# Test our transaction
print(f"\nTesting our MPC transaction:")
response = requests.post(
    "http://regtest:regtest@localhost:18443",
    json={"jsonrpc": "1.0", "id": "test", "method": "testmempoolaccept", "params": [[our_tx_hex]]}
)
test_result = response.json()['result'][0]
print(f"Our tx accepted: {test_result['allowed']}")
if not test_result['allowed']:
    print(f"Reject reason: {test_result.get('reject-reason', 'N/A')}")
