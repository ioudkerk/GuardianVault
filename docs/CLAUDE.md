# CLAUDE.md - Developer Guide for GuardianVault

> **Multiple Guardians, One Secure Vault**

This file provides guidance to Claude Code (claude.ai/code) and other AI assistants when working with GuardianVault code.

## Project Overview

**GuardianVault** - Enterprise-Grade Cryptocurrency Custody for SMEs

A Python implementation for securely managing Bitcoin and Ethereum private keys for small and medium enterprises using **two different approaches**:

1. **Shamir's Secret Sharing (SSS)** - Traditional approach where guardian shares reconstruct keys temporarily
2. **Threshold Cryptography (RECOMMENDED)** - Advanced approach where private key is NEVER reconstructed

**Core Concept**: Distribute key control across multiple trusted guardians. No single guardian has access to the complete private key.

## Development Commands

### Testing and Running

```bash
# Install dependencies
pip install -r requirements.txt

# SHAMIR'S SECRET SHARING (Original Implementation)
# Run core implementation demo
python crypto_mpc_keymanager.py

# Run enhanced version with address generation
python enhanced_crypto_mpc.py

# Run practical workflow simulation
python mpc_workflow_example.py

# THRESHOLD CRYPTOGRAPHY (NEW - No Key Reconstruction)
# Run threshold key generation demo
python threshold_mpc_keymanager.py

# Run threshold address generation
python threshold_addresses.py

# Run threshold signing demo
python threshold_signing.py

# Run complete workflow (setup → addresses → signing)
python complete_mpc_workflow.py

# Run tests (if pytest is installed)
pytest

# Run with coverage
pytest --cov
```

### CLI Usage

```bash
# Generate and split a master seed (3-of-5 scheme)
python mpc_cli.py generate -t 3 -n 5 -o ./shares

# Derive Bitcoin addresses from shares
python mpc_cli.py derive -c bitcoin -s ./shares/share_1.json ./shares/share_2.json ./shares/share_3.json --count 5

# Derive Ethereum addresses
python mpc_cli.py derive -c ethereum -s ./shares/share_*.json --count 3

# Verify shares can reconstruct correctly
python mpc_cli.py verify -s ./shares/share_*.json

# Display share information
python mpc_cli.py info -s ./shares/share_1.json
```

## Architecture

### File Structure

#### Shamir's Secret Sharing Implementation (Original)

- **crypto_mpc_keymanager.py** (~600 lines): Core implementation
  - `ShamirSecretSharing`: Split/reconstruct secrets using finite field arithmetic
  - `HDWalletDerivation`: BIP32/BIP44 hierarchical key derivation
  - `DistributedKeyManager`: Main API combining both systems
  - `KeyShare`: Dataclass for share storage/serialization

- **enhanced_crypto_mpc.py** (~400 lines): Address generation layer
  - `BitcoinAddress`: P2PKH address generation, WIF encoding, Base58
  - `EthereumAddress`: EIP-55 checksummed addresses, Keccak256
  - `EnhancedDistributedKeyManager`: Full workflow integration

- **mpc_cli.py** (~300 lines): Command-line interface
  - Commands: generate, derive, verify, info
  - User-friendly wrapper around core functionality

- **mpc_workflow_example.py** (~300 lines): Practical demonstration
  - Simulates corporate treasury scenario
  - Shows multi-party share distribution
  - Demonstrates reconstruction workflow

#### Threshold Cryptography Implementation (NEW)

- **threshold_mpc_keymanager.py** (~600 lines): Threshold key generation and derivation
  - `ThresholdKeyGeneration`: Additive secret sharing (t-of-t scheme)
  - `ThresholdBIP32`: Threshold BIP32 operations without key reconstruction
  - `PublicKeyDerivation`: Derive unlimited addresses from xpub alone
  - `EllipticCurvePoint`: Pure Python secp256k1 implementation
  - `ExtendedPublicKey`: BIP32 xpub for public derivation

- **threshold_addresses.py** (~300 lines): Address generation from public keys
  - `BitcoinAddressGenerator`: Generate Bitcoin addresses from xpub
  - `EthereumAddressGenerator`: Generate Ethereum addresses from xpub
  - No private keys required!

- **threshold_signing.py** (~400 lines): Threshold ECDSA signing
  - `ThresholdSigner`: 4-round MPC signing protocol
  - `ThresholdSignature`: DER and compact signature formats
  - `ThresholdSigningWorkflow`: Complete signing workflow
  - Signatures created WITHOUT reconstructing private key

- **complete_mpc_workflow.py** (~400 lines): End-to-end demonstration
  - Phase 1: Setup with threshold computation (one-time)
  - Phase 2: Unlimited address generation (no threshold)
  - Phase 3: Transaction signing with threshold protocol
  - Simulates async multi-party operations

### Key Architectural Concepts

#### Approach 1: Shamir's Secret Sharing (Original)

##### 1. Shamir's Secret Sharing Flow
```
Master Seed (256-bit)
  → Polynomial over GF(2^256-189)
  → N evaluation points = N shares
  → K shares + Lagrange interpolation = reconstructed seed
```

**Critical Property**: K-1 shares reveal zero information (information-theoretically secure)

**Limitation**: Must reconstruct private key temporarily for any operation

##### 2. BIP32/BIP44 HD Derivation Paths
```
m / purpose' / coin_type' / account' / change / address_index

Bitcoin:  m/44'/0'/account'/0/index
Ethereum: m/44'/60'/account'/0/index
```

**Note**: Apostrophe (') indicates hardened derivation (index + 0x80000000)

##### 3. Two-Phase Operational Model

**Phase 1 (One-time setup)**:
- Generate master seed on air-gapped device
- Split into shares using Shamir's scheme
- Distribute shares to separate secure locations
- **DESTROY master seed** (critical!)

**Phase 2 (Regular operations)**:
- Gather K shares from distributed parties
- Temporarily reconstruct seed in secure memory
- Derive needed keys/addresses
- Clear seed from memory
- Return shares to storage

---

#### Approach 2: Threshold Cryptography (NEW - Recommended)

**Core Innovation**: Private key NEVER reconstructed - not even temporarily!

##### 1. Additive Secret Sharing

```
Private Key = share_1 + share_2 + share_3 (mod n)
Public Key = G × share_1 + G × share_2 + G × share_3
```

**Properties**:
- All parties must participate (t-of-t scheme)
- Public key computed without combining private shares
- Each party only uses their secret share in computations

##### 2. Three-Phase Operational Model

**Phase 1: One-Time Setup (Threshold Computation)**
```
Parties collaborate using threshold BIP32 to derive:
  m → m/44' → m/44'/coin' → m/44'/coin'/account'

Output: Extended Public Key (xpub) for account

✓ Private key shares NEVER combined
✓ Each party derives their share independently
✓ xpub published for public use
```

**Phase 2: Address Generation (NO Threshold!)**
```
Anyone with xpub can derive unlimited addresses:
  xpub/0/0, xpub/0/1, xpub/0/2, ...

Using non-hardened BIP32 derivation from public key:
  child_pubkey = parent_pubkey + G × HMAC(...)

✓ No private keys needed
✓ No threshold computation
✓ No party communication required
✓ Can be done by untrusted party (e.g., payment processor)
```

**Phase 3: Transaction Signing (Threshold Computation)**
```
4-Round MPC Protocol:
  Round 1: Each party generates nonce share k_i
  Round 2: Combine R = G×k_1 + G×k_2 + G×k_3, extract r
  Round 3: Each party computes signature share s_i
  Round 4: Combine s = s_1 + s_2 + s_3

Output: Valid ECDSA signature (r, s)

✓ Private key shares NEVER combined
✓ Can be async (parties don't need realtime communication)
✓ Each party only reveals R_i and s_i (safe to reveal)
```

##### 3. Key Insight: Hardened vs Non-Hardened Derivation

**BIP44 path**: `m/44'/0'/0'/0/0`

- **Hardened levels** (with `'`): m, 44', 0', 0'
  - Require private key for derivation
  - Need threshold computation
  - Done ONCE during setup

- **Non-hardened levels**: 0, 0
  - Can derive from public key only!
  - No threshold computation needed
  - Unlimited addresses

**This is why we can generate unlimited addresses after one-time setup!**

##### 4. Threshold ECDSA Signing Protocol

Standard ECDSA: `s = k^(-1) × (z + r×x) mod n`

With additive sharing where `x = x_1 + x_2 + x_3` and `k = k_1 + k_2 + k_3`:

```
Each party computes:
  s_i = k^(-1) × (z/n + r×x_i) mod n

Combined signature:
  s = s_1 + s_2 + s_3
    = k^(-1) × (z + r×(x_1+x_2+x_3))
    = k^(-1) × (z + r×x)  ✓ Valid ECDSA signature!
```

**Security**: No party ever learns k or x, only their shares k_i and x_i

### Cryptographic Components

#### Finite Field Arithmetic
- Prime: 2^256 - 189 (256-bit field)
- Polynomial evaluation using Horner's method
- Modular multiplicative inverse via Fermat's little theorem: a^(p-2) mod p

#### Key Derivation (BIP32)
- HMAC-SHA512 for master key: `HMAC-SHA512("Bitcoin seed", seed)`
- Child derivation: `HMAC-SHA512(parent_chain_code, 0x00 || parent_key || index)`
- secp256k1 curve operations

#### Address Generation
- **Bitcoin**: Private key → ECDSA secp256k1 → SHA256 → RIPEMD160 → Base58Check
- **Ethereum**: Private key → ECDSA secp256k1 → Keccak256 → last 20 bytes → EIP-55 checksum

## Choosing Between Approaches

| Feature | Shamir's SSS | Threshold Crypto |
|---------|--------------|------------------|
| **Private key reconstruction** | Temporary (during use) | Never |
| **Address generation** | Requires threshold | xpub only (no threshold) |
| **Transaction signing** | Requires reconstruction | Threshold protocol |
| **Threshold flexibility** | Flexible (K-of-N) | All parties (t-of-t) |
| **Setup complexity** | Simple | Moderate |
| **Operational security** | Good | Excellent |
| **Best for** | Simple backups | Active use (exchanges, wallets) |

**Recommendation**: Use Threshold Cryptography for production systems where keys are actively used. Use Shamir's SSS for cold storage backup scenarios.

## Security Considerations

### When Writing Code

1. **Never log or print full private keys or shares** - Use truncated hex (`key.hex()[:32]...`) for display
2. **Memory clearing**: Use `del` and ensure no sensitive data lingers
3. **Input validation**: Verify all inputs, especially for cryptographic operations
4. **Share separation**: Never store threshold-enabling shares in same location
5. **Constant-time operations**: Avoid timing attacks in sensitive operations
6. **Nonce generation**: Always use cryptographically secure random (secrets module)

### Key Management Rules

**For Shamir's SSS**:
- Master seed should only exist in memory during initial split or temporary reconstruction
- Shares should be JSON-serialized with metadata (threshold, share_id, total_shares)
- Use `secrets.token_bytes(32)` for cryptographically secure random generation
- Implement secure deletion (beyond Python's `del`) for production use

**For Threshold Cryptography**:
- Private key shares NEVER combined - not even in memory
- Each party stores their share securely (HSM recommended)
- xpub can be public (used for address generation)
- Nonces must be unique per signature (critical!)
- Parties should verify R point before signing round 3

### Threat Model Awareness

**Shamir's SSS - Protected against**:
- Single location compromise (need K shares)
- Partial share leakage (K-1 shares = zero bits of information)
- Loss/theft of N-K shares

**Shamir's SSS - Still vulnerable to**:
- Compromise of K+ share locations
- Malware during reconstruction
- Social engineering to gather shares
- Side-channel attacks during crypto operations

**Threshold Crypto - Protected against**:
- ✓ Key reconstruction attacks (key never exists)
- ✓ Single party compromise (all parties needed)
- ✓ Malware on individual machines (only sees one share)
- ✓ Memory dump attacks (no complete key in memory)

**Threshold Crypto - Still vulnerable to**:
- Compromise of ALL parties simultaneously
- Nonce reuse attacks (must ensure k_i unique per signature)
- Network interception of signature shares (use encrypted channels)
- Social engineering to sign malicious transactions

## Testing Approach

When adding features or debugging:

1. **Unit test each component**:
   - Test Shamir's SSS with various thresholds (2-of-3, 3-of-5, 5-of-7)
   - Verify reconstruction with exactly K, K+1, and all N shares
   - Confirm K-1 shares fail to reconstruct
   - Test HD derivation matches BIP32 test vectors

2. **Integration test workflows**:
   - Generate → Split → Save → Load → Reconstruct → Derive
   - Test with both Bitcoin and Ethereum paths
   - Verify WIF and EIP-55 address formats

3. **Security test edge cases**:
   - Attempt reconstruction with insufficient shares
   - Verify shares from different seeds don't combine
   - Test with maximum threshold values

## Common Patterns

### Adding Support for New Cryptocurrencies

1. Add coin type constant to `HDWalletDerivation`:
```python
COIN_TYPES = {
    'bitcoin': 0,
    'ethereum': 60,
    'litecoin': 2,  # Add new coin
}
```

2. Create derivation method in `DistributedKeyManager`:
```python
def derive_litecoin_address_key(self, master_seed, account, address_index):
    return self.hd_derivation.derive_bip44_path(
        master_seed, coin_type=2, account=account,
        change=0, address_index=address_index
    )
```

3. Implement address generation in `enhanced_crypto_mpc.py` following Bitcoin/Ethereum patterns

### Working with Shares

```python
# Always verify threshold before reconstruction
if len(shares) < shares[0].threshold:
    raise ValueError(f"Need {shares[0].threshold} shares, got {len(shares)}")

# Load shares with error handling
try:
    share = manager.load_share_from_file(path)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Failed to load share: {e}")
```

## Dependencies

- **ecdsa** (≥0.18.0): ECDSA signatures with secp256k1 curve
- **base58** (≥2.1.1): Bitcoin address encoding
- **eth-hash[pycryptodome]** (≥0.5.2): Keccak256 for Ethereum addresses
- **cryptography** (≥41.0.0): Optional, recommended for production
- **pytest** (≥7.4.0): Testing framework

## Important Notes

- This is an **educational implementation** - requires security audit before production use
- Not a "Model Context Protocol" (MCP) despite directory name - implements Multi-Party Computation for key management
- Uses pure Python for Shamir's SSS (no external dependencies for core secret sharing)
- Follows BIP32/BIP44/BIP39 standards for HD wallet compatibility
- No blockchain interaction - purely cryptographic key management
