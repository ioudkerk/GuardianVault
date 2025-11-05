# GuardianVault Core Library

The core Python library for threshold cryptography and multi-party computation (MPC) for cryptocurrency key management.

## Overview

GuardianVault provides a secure way to manage cryptocurrency keys using threshold cryptography, where the private key is split into multiple shares and never reconstructed. This library implements:

- Threshold key generation (Shamir's Secret Sharing)
- BIP32 hierarchical deterministic key derivation
- Threshold ECDSA signing (without reconstructing private keys)
- Bitcoin and Ethereum address generation

## Modules

### `threshold_mpc_keymanager.py`
Core threshold key management functionality:
- `ThresholdKeyGeneration` - Generate and manage threshold key shares
- `ThresholdBIP32` - BIP32 hierarchical key derivation for threshold keys
- `KeyShare` - Data class representing a key share
- `ExtendedPublicKey` - Extended public key (xpub) functionality

### `threshold_signing.py`
Threshold ECDSA signing without key reconstruction:
- `ThresholdSigner` - 4-round MPC signing protocol
- `ThresholdSigningWorkflow` - High-level signing workflow

### `threshold_addresses.py`
Cryptocurrency address generation from public keys:
- `BitcoinAddressGenerator` - Generate Bitcoin addresses (P2PKH, P2SH, Bech32)
- `EthereumAddressGenerator` - Generate Ethereum addresses

### `crypto_mpc_keymanager.py`
Basic distributed key manager:
- `DistributedKeyManager` - Simple secret sharing implementation
- Basic Shamir's Secret Sharing utilities

### `enhanced_crypto_mpc.py`
Enhanced crypto utilities with address generation:
- Extended Bitcoin and Ethereum utilities
- Wallet Import Format (WIF) support

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Generate Threshold Keys

```python
from guardianvault import ThresholdKeyGeneration, ThresholdBIP32

# Generate key shares for 3 parties with 3-of-3 threshold
shares, master_pubkey = ThresholdKeyGeneration.generate_shares(
    num_parties=3,
    threshold=3
)

# Derive BIP32 master keys
seed = secrets.token_bytes(32)
master_shares, master_pub, chain = ThresholdBIP32.derive_master_keys_threshold(
    shares,
    seed
)
```

### Generate Addresses

```python
from guardianvault import BitcoinAddressGenerator

# Generate Bitcoin address from public key
address = BitcoinAddressGenerator.pubkey_to_address(
    public_key_bytes,
    testnet=False
)
```

### Sign Transactions

```python
from guardianvault import ThresholdSigner

# Each party generates nonce share (Round 1)
nonce_share, r_point = ThresholdSigner.sign_round1_generate_nonce(party_id)

# Server combines R points (Round 2)
# ...

# Each party computes signature share (Round 3)
sig_share = ThresholdSigner.sign_round3_compute_signature_share(
    key_share=key_share,
    nonce_share=nonce_share,
    message_hash=msg_hash,
    r=r,
    k_total=k_total,
    num_parties=3
)

# Server combines signature shares (Round 4)
# ...
```

## Security Features

- Private keys are NEVER reconstructed
- Each party only holds a share of the private key
- Requires threshold number of parties to sign
- BIP32 derivation works on shares (no key reconstruction needed)
- Secure random number generation using `secrets` module

## Examples

See the `examples/` directory for complete usage examples:
- `complete_mpc_workflow.py` - Full workflow demonstration
- `mpc_cli.py` - Command-line interface
- `mpc_workflow_example.py` - Practical MPC scenario

## Testing

Run the coordination server test:

```bash
cd tests
python test_coordination_server.py
```

## License

See LICENSE file in the project root.
