import sys
sys.path.insert(0, '/Users/ivan/projects/personal/GuardianVault')

import json
import requests
from guardianvault.bitcoin_transaction import BitcoinTransactionBuilder
from guardianvault.threshold_mpc_keymanager import ExtendedPublicKey, PublicKeyDerivation

# Get transaction from server
tx_resp = requests.get("http://localhost:8000/api/transactions/tx_QwKiG6Qg7Xes")
tx = tx_resp.json()

# Load vault config
with open('demo_output/vault_config.json', 'r') as f:
    vault_config = json.load(f)

# Derive pubkey
xpub = ExtendedPublicKey.from_dict(vault_config['bitcoin']['xpub'])
pubkeys = PublicKeyDerivation.derive_address_public_keys(xpub, change=0, num_addresses=3)
pubkey = pubkeys[2]

# Build transaction
tx_builder, script_code, sender_type, utxo_amount_sats = BitcoinTransactionBuilder.build_p2pkh_transaction(
    utxo_txid=tx['utxo_txid'],
    utxo_vout=tx['utxo_vout'],
    utxo_amount_btc=float(tx['utxo_amount']),
    sender_address=tx['sender_address'],
    recipient_address=tx['recipient'],
    send_amount_btc=float(tx['amount']),
    fee_btc=float(tx['fee'])
)

# Sign with actual signature
sig_der = bytes.fromhex(tx['final_signature']['der'])

signed_tx = BitcoinTransactionBuilder.sign_transaction(
    tx_builder,
    input_index=0,
    script_code=script_code,
    signature_der=sig_der,
    public_key=pubkey,
    sender_type=sender_type
)

raw_tx_hex = signed_tx.serialize().hex()

# Try broadcasting
rpc_response = requests.post(
    "http://regtest:regtest@localhost:18443",
    json={
        "jsonrpc": "1.0",
        "id": "test",
        "method": "sendrawtransaction",
        "params": [raw_tx_hex]
    }
)

result = rpc_response.json()

print("Broadcasting result:")
print(json.dumps(result, indent=2))

if result.get('error'):
    print(f"\n❌ Failed: {result['error']['message']}")
    
    # Let's try with Bitcoin Core's own signature
    print("\n" + "=" * 70)
    print("Let me try signing with Bitcoin Core to compare...")
    print("=" * 70)
    
    # Import the private key to Bitcoin Core
    # (We can't do this with MPC keys, but let's see what a valid P2WPKH looks like)
else:
    print(f"\n✅ Success! TXID: {result['result']}")
