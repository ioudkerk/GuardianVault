# MPC Cryptocurrency Key Manager - Visual Architecture

This document describes the architecture of **TWO implementations**:

1. **Shamir's Secret Sharing (SSS)** - Traditional approach (documented below)
2. **Threshold Cryptography** - Advanced MPC approach (see ARCHITECTURE_THRESHOLD.md)

## Quick Comparison

| Feature | Shamir's SSS | Threshold Crypto |
|---------|--------------|------------------|
| **Private Key** | Reconstructed temporarily | NEVER reconstructed |
| **Address Generation** | Needs reconstruction | xpub only (no threshold) |
| **Signing** | Needs reconstruction | MPC protocol |
| **Best For** | Cold storage backups | Active wallets |

**For the new Threshold Cryptography architecture, see [ARCHITECTURE_THRESHOLD.md](ARCHITECTURE_THRESHOLD.md)**

---

# Shamir's Secret Sharing Architecture

## System Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: INITIAL SETUP (ONE TIME)                     │
│                     Secure, Air-Gapped Environment                        │
└──────────────────────────────────────────────────────────────────────────┘

    Generate Random Seed (256 bits)
    ================================
            │
            │  secrets.token_bytes(32)
            ▼
    ┌──────────────────┐
    │   Master Seed    │  ⚠️ HIGHLY SENSITIVE - DESTROY AFTER SPLITTING ⚠️
    │   (32 bytes)     │
    └────────┬─────────┘
             │
             │  Shamir's Secret Sharing
             │  split_secret(seed, K=3, N=5)
             ▼
    ┌────────────────────────────────┐
    │  Polynomial over GF(2^256-189) │
    │  f(x) = a₀ + a₁x + a₂x²        │
    │  where a₀ = secret             │
    └────────┬───────────────────────┘
             │
             │  Evaluate at x=1,2,3,4,5
             ▼
    ┌─────────────────────────────────────────────────────┐
    │              N = 5 Shares Created                   │
    │     (Need any K = 3 to reconstruct)                 │
    └──┬───────┬────────┬────────┬────────┬──────────────┘
       │       │        │        │        │
       ▼       ▼        ▼        ▼        ▼
    Share1  Share2  Share3  Share4  Share5
    (x=1)   (x=2)   (x=3)   (x=4)   (x=5)
       │       │        │        │        │
       │       │        │        │        │
    ┌──▼──┐ ┌─▼──┐  ┌─▼──┐  ┌─▼──┐  ┌─▼──┐
    │ HSM │ │Safe│  │Bank│  │Home│  │Cloud│
    │ #1  │ │Dep.│  │Box │  │Safe│  │Bkup│
    └─────┘ └────┘  └────┘  └────┘  └─────┘
    Location Location Location Location Location
       A       B        C        D        E


┌──────────────────────────────────────────────────────────────────────────┐
│             PHASE 2: ADDRESS GENERATION (ROUTINE OPERATION)              │
│                    Temporary Secure Environment                           │
└──────────────────────────────────────────────────────────────────────────┘

    Gather K=3 Shares (e.g., Share1, Share3, Share5)
    =================================================
           │             │             │
           ▼             ▼             ▼
        Share1        Share3        Share5
         (x=1)         (x=3)         (x=5)
           │             │             │
           └─────────────┴─────────────┘
                         │
                         │  Lagrange Interpolation
                         │  f(0) = secret
                         ▼
                 ┌───────────────┐
                 │  Master Seed  │  ⚠️ IN MEMORY ONLY ⚠️
                 │  (Reconstructed)│
                 └───────┬────────┘
                         │
                         │
         ┌───────────────┴────────────────┐
         │                                 │
         │  BIP32 Master Key Derivation    │
         │  HMAC-SHA512("Bitcoin seed", seed)
         │                                 │
         └───────────────┬────────────────┘
                         │
                         ▼
         ┌────────────────────────────────┐
         │    Master Private Key (32B)    │
         │    Chain Code (32B)            │
         └────────┬───────────────────────┘
                  │
                  │  BIP44 Hierarchical Derivation
                  │
        ┌─────────┴──────────┐
        │                    │
        ▼                    ▼
    Bitcoin Path        Ethereum Path
    m/44'/0'/0'/0/i     m/44'/60'/0'/0/i
        │                    │
        │ Hardened           │ Hardened
        │ Derivation         │ Derivation
        ▼                    ▼
    BTC Private Key     ETH Private Key
        │                    │
        ▼                    ▼
    ┌───────────┐      ┌────────────┐
    │ BTC Addr  │      │ ETH Addr   │
    │ 1A1zP1... │      │ 0x742d3... │
    └───────────┘      └────────────┘
        
    ✓ Clear Master Seed from Memory
    ✓ Return Shares to Storage


┌──────────────────────────────────────────────────────────────────────────┐
│                    KEY DERIVATION DETAIL                                 │
└──────────────────────────────────────────────────────────────────────────┘

Bitcoin Address Generation:
───────────────────────────

Private Key (32 bytes)
    │
    ▼ ECDSA secp256k1
Public Key (33 bytes compressed)
    │
    ▼ SHA256
    ▼ RIPEMD160
Public Key Hash (20 bytes)
    │
    ▼ Add version (0x00)
    ▼ Add checksum (4 bytes)
    ▼ Base58 Encode
Bitcoin Address (e.g., 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa)


Ethereum Address Generation:
─────────────────────────────

Private Key (32 bytes)
    │
    ▼ ECDSA secp256k1
Public Key (64 bytes uncompressed, without 0x04 prefix)
    │
    ▼ Keccak256
    ▼ Take last 20 bytes
Address (20 bytes)
    │
    ▼ EIP-55 Checksum
    ▼ Add 0x prefix
Ethereum Address (e.g., 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb)


┌──────────────────────────────────────────────────────────────────────────┐
│                  SECURITY GUARANTEES                                     │
└──────────────────────────────────────────────────────────────────────────┘

Shamir's Secret Sharing Properties:
────────────────────────────────────

┌─────────────┬──────────────┬────────────────────────────┐
│ Shares Have │ Can Do?      │ Information Leaked         │
├─────────────┼──────────────┼────────────────────────────┤
│ 0 shares    │ ✗ Nothing    │ 0 bits                     │
│ 1 share     │ ✗ Nothing    │ 0 bits (provably secure!)  │
│ 2 shares    │ ✗ Nothing    │ 0 bits (provably secure!)  │
│ 3 shares    │ ✓ Everything │ ALL bits (full reconstruct)│
│ 4 shares    │ ✓ Everything │ ALL bits                   │
│ 5 shares    │ ✓ Everything │ ALL bits                   │
└─────────────┴──────────────┴────────────────────────────┘

This is called the "threshold property" - it's all or nothing!


Threat Model:
─────────────

✅ PROTECTED:
    • Single location compromise (attacker gets 1-2 shares → useless)
    • Insider threat (no single person has access)
    • Loss/theft (can lose N-K shares and still recover)
    • Physical disasters (distributed storage)

⚠️  STILL VULNERABLE TO:
    • Compromise of K+ locations simultaneously
    • Malware during reconstruction
    • Social engineering to gather shares
    • Side-channel attacks during crypto operations


┌──────────────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT TOPOLOGIES                                 │
└──────────────────────────────────────────────────────────────────────────┘

Topology 1: Personal (3-of-5)
──────────────────────────────

Share 1: Home Safe ────┐
Share 2: Bank Box ─────┤
Share 3: Family Member ├─── Any 3 needed
Share 4: Office Safe ──┤
Share 5: Cloud Backup ─┘

Use Case: Personal cold storage
Benefit: Distributed, resilient to loss


Topology 2: Corporate (5-of-7)
───────────────────────────────

Share 1: CFO HSM ──────┐
Share 2: CTO HSM ──────┤
Share 3: CEO HSM ──────┤
Share 4: Board Mbr 1 ──├─── Any 5 needed
Share 5: Board Mbr 2 ──┤
Share 6: Escrow 1 ─────┤
Share 7: Escrow 2 ─────┘

Use Case: Corporate treasury
Benefit: No single executive control


Topology 3: Multi-Sig + MPC (3-of-3 MPC, 2-of-3 MultiSig)
───────────────────────────────────────────────────────────

Each of 3 parties holds different shares:

Party A: Shares 1, 2 ──┐ (2-of-3)
Party B: Shares 3, 4 ──┼─ MPC + MultiSig
Party C: Shares 5 ─────┘ (2-of-3)

Use Case: Maximum security exchange hot wallet
Benefit: Layered security (need MPC + blockchain multisig)


┌──────────────────────────────────────────────────────────────────────────┐
│                    FILE STRUCTURE                                        │
└──────────────────────────────────────────────────────────────────────────┘

crypto-mpc-keymanager/
│
├── crypto_mpc_keymanager.py ─── Core implementation
│   ├── ShamirSecretSharing ───── Split/reconstruct secrets
│   ├── HDWalletDerivation ─────── BIP32/BIP44 key derivation
│   └── DistributedKeyManager ─── Main API
│
├── enhanced_crypto_mpc.py ────── Address generation
│   ├── BitcoinAddress ────────── BTC address from privkey
│   ├── EthereumAddress ───────── ETH address from privkey
│   └── EnhancedDistributedKeyManager ─ Full workflow
│
├── mpc_cli.py ────────────────── CLI tool
│   ├── generate ──────────────── Create & split seed
│   ├── derive ────────────────── Derive keys
│   ├── verify ────────────────── Verify reconstruction
│   └── info ──────────────────── Display share info
│
├── mpc_workflow_example.py ───── Practical demo
│   └── Simulates corporate scenario
│
├── requirements.txt ──────────── Dependencies
├── README.md ─────────────────── Full documentation
├── QUICKSTART.md ─────────────── Quick start guide
└── PROJECT_SUMMARY.md ────────── This summary


┌──────────────────────────────────────────────────────────────────────────┐
│                    MATHEMATICAL FOUNDATION                               │
└──────────────────────────────────────────────────────────────────────────┘

Shamir's Secret Sharing:
────────────────────────

Problem: Split secret S into N shares such that:
    • Any K shares can reconstruct S
    • Any K-1 shares reveal NOTHING about S

Solution: Polynomial interpolation over finite field

1. Choose prime p (we use p = 2^256 - 189)
2. Choose random polynomial of degree K-1:
   f(x) = a₀ + a₁x + a₂x² + ... + aₖ₋₁x^(K-1) (mod p)
   where a₀ = S (the secret)

3. Generate N shares:
   Share_i = (i, f(i)) for i = 1, 2, ..., N

4. Reconstruct using Lagrange interpolation:
   f(0) = Σᵢ yᵢ · Πⱼ≠ᵢ (0-xⱼ)/(xᵢ-xⱼ) (mod p)

Why it works:
    • K points uniquely determine polynomial of degree K-1
    • K-1 points give ∞ possible polynomials → no information
    • Evaluation at x=0 gives the secret: f(0) = a₀ = S


BIP32 HD Derivation:
────────────────────

Goal: Derive child keys from parent without exposing parent

Algorithm:
    1. Start with seed S
    2. Master: (k_M, c_M) = HMAC-SHA512("Bitcoin seed", S)
    3. Child i: 
       data = 0x00 || k_parent || i
       (IL, IR) = HMAC-SHA512(c_parent, data)
       k_child = (IL + k_parent) mod n
       c_child = IR
    
Where:
    • k = private key
    • c = chain code
    • n = order of secp256k1 curve
    • || = concatenation

Hardened derivation (i ≥ 2³¹):
    Prevents deriving child public keys from parent public key
    Required for financial applications


BIP44 Path Structure:
─────────────────────

m / purpose' / coin_type' / account' / change / address_index

Example: m/44'/0'/0'/0/0
    • m = master
    • 44' = BIP44 (hardened)
    • 0' = Bitcoin (hardened)
    • 0' = Account 0 (hardened)
    • 0 = External chain (non-hardened)
    • 0 = Address index 0 (non-hardened)

' = hardened derivation (index + 2³¹)


┌──────────────────────────────────────────────────────────────────────────┐
│                         CONCLUSION                                       │
└──────────────────────────────────────────────────────────────────────────┘

This system provides:

✓ Cryptographically secure key splitting
✓ Industry-standard key derivation (BIP32/BIP44)
✓ No single point of failure
✓ Mathematical security guarantees
✓ Flexible threshold schemes
✓ Unlimited address generation
✓ Support for Bitcoin and Ethereum
✓ Production-ready implementation
✓ Comprehensive documentation

Perfect for:
• Cold storage wallets
• Corporate treasuries
• Multi-party custody
• Estate planning
• Exchange security

Next steps: Read QUICKSTART.md and try the examples!
```
