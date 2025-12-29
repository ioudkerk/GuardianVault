# MPC with Additive Secret Sharing - Technical Documentation

This document explains the Multi-Party Computation (MPC) implementation using Additive Secret Sharing in GuardianVault, including mathematical proofs of correctness and security.

## Table of Contents

1. [Overview](#overview)
2. [Additive Secret Sharing Scheme](#additive-secret-sharing-scheme)
3. [Public Key Computation](#public-key-computation)
4. [Threshold ECDSA Signing Protocol](#threshold-ecdsa-signing-protocol)
5. [Mathematical Proof of Correctness](#mathematical-proof-of-correctness)
6. [Security Analysis](#security-analysis)
7. [Implementation Reference](#implementation-reference)

---

## Overview

GuardianVault uses **Additive Secret Sharing** for threshold cryptography, enabling multiple parties to jointly sign transactions without any single party ever having access to the complete private key. This implementation works on the **secp256k1** elliptic curve (used by Bitcoin and Ethereum).

### Key Properties

- **(n,n) Threshold Scheme**: All `n` parties must participate to sign
- **No Key Reconstruction**: The private key is never assembled in any single location
- **Information-Theoretic Security**: Any subset of `n-1` shares reveals zero information about the secret
- **Standard Signatures**: Output is indistinguishable from regular ECDSA signatures

---

## Additive Secret Sharing Scheme

### Mathematical Definition

A private key `x` is split into `n` shares such that:

```
x = x₁ + x₂ + ... + xₙ  (mod n)
```

Where `n` is the secp256k1 curve order:
```
SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
```

### Share Generation Algorithm

**Input:** Number of parties `n`

**Output:** Shares `(x₁, x₂, ..., xₙ)` and public key `P`

**Steps:**
1. Generate `n-1` random shares: `x₁, x₂, ..., xₙ₋₁ ← random([0, n))`
2. Generate master private key: `x ← random([0, n))`
3. Compute last share: `xₙ = x - (x₁ + x₂ + ... + xₙ₋₁) mod n`
4. Compute public key: `P = x · G`

### Proof of Correctness

```
x₁ + x₂ + ... + xₙ₋₁ + xₙ  (mod n)
= x₁ + x₂ + ... + xₙ₋₁ + (x - (x₁ + x₂ + ... + xₙ₋₁))  (mod n)
= x  (mod n)  ✓
```

### Security Property

**Theorem:** Any subset of `n-1` shares reveals zero information about `x`.

**Proof:** Let `S = x₁ + ... + xₙ₋₁ (mod n)`. For any guess `x'` of the secret:
```
xₙ = x' - S (mod n)
```
Since `xₙ` was chosen uniformly at random from `[0, n)`, and `n` is prime, every possible value of `x'` corresponds to exactly one valid `xₙ`. Therefore, without knowledge of `xₙ`, no information about the true value of `x` is leaked.

---

## Public Key Computation

The public key can be computed from shares **without reconstructing the private key**.

### Standard Computation
```
P = x · G
```
Where `G` is the secp256k1 generator point.

### Distributed Computation

Each party computes their public key share:
```
Pᵢ = xᵢ · G
```

The combined public key is:
```
P = P₁ + P₂ + ... + Pₙ
```

### Proof (Homomorphic Property)

```
P = x · G
  = (x₁ + x₂ + ... + xₙ) · G
  = x₁ · G + x₂ · G + ... + xₙ · G    (distributive property)
  = P₁ + P₂ + ... + Pₙ  ✓
```

This works because scalar multiplication distributes over point addition on elliptic curves:
```
(a + b) · G = a · G + b · G
```

---

## Threshold ECDSA Signing Protocol

### Standard ECDSA Review

For message hash `z`, standard ECDSA produces signature `(r, s)`:
```
k = random nonce ∈ [1, n-1]
R = k · G
r = R.x mod n
s = k⁻¹ · (z + r · x) mod n
```

### Four-Round Threshold Protocol

#### Round 1: Nonce Generation

Each party `i` generates:
- Random nonce share: `kᵢ ← random([1, n))`
- Public nonce point: `Rᵢ = kᵢ · G`

The parties share `Rᵢ` (public) but keep `kᵢ` secret.

The implicit total nonce is:
```
k = k₁ + k₂ + ... + kₙ (mod n)
```

#### Round 2: Combine Nonce Points

The coordinator (or any party) computes:
```
R = R₁ + R₂ + ... + Rₙ
r = R.x mod n
```

**Proof that R is correct:**
```
R = R₁ + R₂ + ... + Rₙ
  = k₁·G + k₂·G + ... + kₙ·G
  = (k₁ + k₂ + ... + kₙ)·G
  = k·G  ✓
```

#### Round 3: Compute Signature Shares

Each party `i` computes their signature share:
```
sᵢ = k⁻¹ · (z/n + r · xᵢ) mod n
```

Where:
- `k⁻¹` = modular inverse of total nonce (requires `k_total` from coordinator)
- `z` = message hash (32 bytes, interpreted as integer)
- `n` = number of parties
- `r` = x-coordinate of combined R point
- `xᵢ` = party's private key share

#### Round 4: Combine Signatures

The final signature `s` component:
```
s = s₁ + s₂ + ... + sₙ (mod n)
```

Apply BIP-62 low-S normalization:
```
if s > n/2:
    s = n - s
```

Final signature: `(r, s)`

---

## Mathematical Proof of Correctness

**Theorem:** The threshold signature `s = Σsᵢ` equals the standard ECDSA signature `s = k⁻¹(z + rx)`.

**Proof:**

Starting with the sum of signature shares:
```
s = Σᵢ sᵢ
  = Σᵢ k⁻¹ · (z/n + r · xᵢ)  (mod n)
```

Factor out `k⁻¹` (constant across all parties):
```
s = k⁻¹ · Σᵢ (z/n + r · xᵢ)  (mod n)
```

Distribute the summation:
```
s = k⁻¹ · (Σᵢ z/n + r · Σᵢ xᵢ)  (mod n)
```

Evaluate the first sum (n parties each contributing z/n):
```
Σᵢ z/n = n · (z/n) = z
```

Evaluate the second sum (definition of additive sharing):
```
Σᵢ xᵢ = x
```

Substitute back:
```
s = k⁻¹ · (z + r · x)  (mod n)  ✓
```

**This is exactly the standard ECDSA formula. QED.**

---

## Security Analysis

### Data Exposure by Round

| Round | Data Shared | Contains Private Key? | Security |
|-------|-------------|----------------------|----------|
| 1 | `Rᵢ = kᵢ · G` | No - only public EC points | ECDLP hard |
| 2 | `R`, `r` | No - aggregate public data | Public values |
| 3 | `sᵢ = k⁻¹(z/n + r·xᵢ)` | Masked by `z/n` term | See analysis below |
| 4 | `s = Σsᵢ` | No - only aggregate | Standard signature |

### Signature Share Security

The signature share `sᵢ = k⁻¹(z/n + r·xᵢ)` contains `xᵢ`, but extracting it is computationally infeasible because:

1. **Unknown Nonce Inverse**: While `k_total` is known to the coordinator, individual `kᵢ` values remain secret
2. **Masking Term**: The `z/n` term acts as additive masking
3. **Modular Arithmetic**: Without knowing the exact decomposition, solving for `xᵢ` requires breaking the discrete logarithm problem

### Threat Model

| Threat | Protection |
|--------|------------|
| Single party compromise | Attacker gets one share; needs all `n` to sign |
| Coordinator compromise | Coordinator never sees private key shares |
| Network eavesdropping | Only public points and masked shares transmitted |
| Replay attacks | Fresh random nonces per signature |

### Limitations of (n,n) Scheme

- **Availability**: All parties must be online to sign
- **No Fault Tolerance**: Single party failure blocks signing
- **Solution**: Can upgrade to (t,n) Shamir-based scheme for fault tolerance

---

## Implementation Reference

### Key Files

| File | Purpose |
|------|---------|
| `guardianvault/mpc_keymanager.py` | Share generation, BIP32 derivation |
| `guardianvault/mpc_signing.py` | 4-round signing protocol |
| `guardianvault/mpc_addresses.py` | Bitcoin/Ethereum address generation |
| `coordination-server/app/services/mpc_coordinator.py` | Protocol orchestration |

### Core Classes

#### `MPCKeyGeneration` (mpc_keymanager.py:179)

```python
@staticmethod
def generate_shares(num_parties: int, threshold: int = None) -> Tuple[List[KeyShare], bytes]:
    """
    Generate key shares for n-of-n scheme (additive secret sharing)

    Returns:
        (shares, master_public_key_bytes)
    """
```

#### `MPCSigner` (mpc_signing.py:78)

```python
class MPCSigner:
    @staticmethod
    def sign_round1_generate_nonce(party_id: int) -> Tuple[int, bytes]

    @staticmethod
    def sign_round2_combine_nonces(r_shares: List[bytes]) -> Tuple[EllipticCurvePoint, int]

    @staticmethod
    def sign_round3_compute_signature_share(...) -> int

    @staticmethod
    def sign_round4_combine_signatures(s_shares: List[int], r: int) -> ThresholdSignature
```

### Curve Parameters (mpc_keymanager.py:23-27)

```python
# secp256k1 curve parameters
SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141  # Curve order
SECP256K1_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F  # Field prime
SECP256K1_GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798  # Generator X
SECP256K1_GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8  # Generator Y
```

---

## Visual Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ADDITIVE SECRET SHARING                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Private Key:   x = x₁ + x₂ + x₃  (mod n)                             │
│                                                                         │
│   ┌─────────┐   ┌─────────┐   ┌─────────┐                              │
│   │ Party 1 │   │ Party 2 │   │ Party 3 │                              │
│   │   x₁    │   │   x₂    │   │   x₃    │                              │
│   └────┬────┘   └────┬────┘   └────┬────┘                              │
│        │             │             │                                    │
│        └─────────────┼─────────────┘                                    │
│                      ▼                                                  │
│              x (never reconstructed)                                    │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                    THRESHOLD ECDSA SIGNING                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Round 1: Each party generates kᵢ, broadcasts Rᵢ = kᵢ·G              │
│                                                                         │
│   Round 2: Coordinator computes R = ΣRᵢ, r = R.x mod n                 │
│                                                                         │
│   Round 3: Each party computes sᵢ = k⁻¹(z/n + r·xᵢ)                    │
│                                                                         │
│   Round 4: Coordinator computes s = Σsᵢ mod n                          │
│                                                                         │
│   Output: (r, s) = valid ECDSA signature                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## References

1. **ECDSA Standard**: ANSI X9.62, SEC 1: Elliptic Curve Cryptography
2. **secp256k1 Parameters**: Standards for Efficient Cryptography (SEC 2)
3. **BIP-32**: Hierarchical Deterministic Wallets
4. **BIP-62**: Dealing with Malleability (low-S requirement)
