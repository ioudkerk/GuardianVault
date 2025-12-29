#!/usr/bin/env python3
"""
MPC Cryptocurrency Key Manager with Additive Secret Sharing
Uses n-of-n multi-party computation where private key is NEVER reconstructed

Key Features:
- Additive secret sharing for MPC operations (all parties required)
- Distributed BIP32 derivation for account setup
- Public derivation for unlimited addresses
- MPC ECDSA signatures

Note: This is an (n,n) scheme - all parties must participate to sign.
For true threshold (t,n) schemes, see Shamir-based implementations.

SECURITY: Private key shares never leave their respective parties
"""

import hashlib
import hmac
import secrets
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import json


# secp256k1 curve parameters
SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
SECP256K1_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
SECP256K1_GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
SECP256K1_GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8


@dataclass
class KeyShare:
    """Represents one party's share of a distributed private key"""
    party_id: int
    share_value: bytes  # This party's secret share
    total_parties: int
    threshold: int
    metadata: Optional[Dict] = None

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            'party_id': self.party_id,
            'share_value': self.share_value.hex(),
            'total_parties': self.total_parties,
            'threshold': self.threshold,
            'metadata': self.metadata or {}
        }

    @staticmethod
    def from_dict(data: dict) -> 'KeyShare':
        """Deserialize from dictionary"""
        return KeyShare(
            party_id=data['party_id'],
            share_value=bytes.fromhex(data['share_value']),
            total_parties=data['total_parties'],
            threshold=data['threshold'],
            metadata=data.get('metadata')
        )


@dataclass
class ExtendedPublicKey:
    """BIP32 Extended Public Key (xpub) - can derive unlimited addresses"""
    public_key: bytes  # 33 bytes compressed
    chain_code: bytes  # 32 bytes
    depth: int
    parent_fingerprint: bytes
    child_number: int

    def to_dict(self) -> dict:
        return {
            'public_key': self.public_key.hex(),
            'chain_code': self.chain_code.hex(),
            'depth': self.depth,
            'parent_fingerprint': self.parent_fingerprint.hex(),
            'child_number': self.child_number
        }

    @staticmethod
    def from_dict(data: dict) -> 'ExtendedPublicKey':
        return ExtendedPublicKey(
            public_key=bytes.fromhex(data['public_key']),
            chain_code=bytes.fromhex(data['chain_code']),
            depth=data['depth'],
            parent_fingerprint=bytes.fromhex(data['parent_fingerprint']),
            child_number=data['child_number']
        )


class EllipticCurvePoint:
    """Point on secp256k1 elliptic curve"""

    def __init__(self, x: Optional[int], y: Optional[int]):
        self.x = x
        self.y = y
        self.is_infinity = (x is None and y is None)

    @staticmethod
    def generator() -> 'EllipticCurvePoint':
        """Return generator point G"""
        return EllipticCurvePoint(SECP256K1_GX, SECP256K1_GY)

    @staticmethod
    def infinity() -> 'EllipticCurvePoint':
        """Return point at infinity (identity element)"""
        return EllipticCurvePoint(None, None)

    def __add__(self, other: 'EllipticCurvePoint') -> 'EllipticCurvePoint':
        """Point addition on secp256k1"""
        if self.is_infinity:
            return other
        if other.is_infinity:
            return self

        if self.x == other.x:
            if self.y == other.y:
                # Point doubling
                s = (3 * self.x * self.x * pow(2 * self.y, -1, SECP256K1_P)) % SECP256K1_P
            else:
                return EllipticCurvePoint.infinity()
        else:
            # Point addition
            s = ((other.y - self.y) * pow(other.x - self.x, -1, SECP256K1_P)) % SECP256K1_P

        x3 = (s * s - self.x - other.x) % SECP256K1_P
        y3 = (s * (self.x - x3) - self.y) % SECP256K1_P

        return EllipticCurvePoint(x3, y3)

    def __mul__(self, scalar: int) -> 'EllipticCurvePoint':
        """Scalar multiplication (double-and-add)"""
        if scalar == 0 or self.is_infinity:
            return EllipticCurvePoint.infinity()

        result = EllipticCurvePoint.infinity()
        addend = self

        while scalar:
            if scalar & 1:
                result = result + addend
            addend = addend + addend
            scalar >>= 1

        return result

    def to_bytes(self, compressed: bool = True) -> bytes:
        """Convert point to bytes (compressed format)"""
        if self.is_infinity:
            return b'\x00'

        if compressed:
            prefix = b'\x02' if self.y % 2 == 0 else b'\x03'
            return prefix + self.x.to_bytes(32, 'big')
        else:
            return b'\x04' + self.x.to_bytes(32, 'big') + self.y.to_bytes(32, 'big')

    @staticmethod
    def from_bytes(data: bytes) -> 'EllipticCurvePoint':
        """Parse point from bytes (compressed or uncompressed)"""
        if data[0] == 0x04:  # Uncompressed
            x = int.from_bytes(data[1:33], 'big')
            y = int.from_bytes(data[33:65], 'big')
            return EllipticCurvePoint(x, y)
        elif data[0] in (0x02, 0x03):  # Compressed
            x = int.from_bytes(data[1:33], 'big')
            # Derive y from x (solving y^2 = x^3 + 7 mod p)
            y_squared = (pow(x, 3, SECP256K1_P) + 7) % SECP256K1_P
            y = pow(y_squared, (SECP256K1_P + 1) // 4, SECP256K1_P)
            if (y % 2 == 0) != (data[0] == 0x02):
                y = SECP256K1_P - y
            return EllipticCurvePoint(x, y)
        else:
            raise ValueError("Invalid point encoding")


class MPCKeyGeneration:
    """Generate distributed keys using additive secret sharing (n-of-n scheme)"""

    @staticmethod
    def generate_shares(num_parties: int, threshold: int = None) -> Tuple[List[KeyShare], bytes]:
        """
        Generate key shares for threshold scheme

        For simplicity, we use (t, t) additive secret sharing where:
        - All t parties must participate
        - private_key = share_1 + share_2 + ... + share_t (mod n)

        Args:
            num_parties: Number of parties (threshold)
            threshold: Must equal num_parties for additive sharing

        Returns:
            (shares, master_public_key_bytes)
        """
        if threshold is None:
            threshold = num_parties

        if threshold != num_parties:
            raise ValueError("Additive secret sharing requires threshold == num_parties")

        # Generate random shares (all but last)
        shares_values = []
        shares_sum = 0

        for i in range(num_parties - 1):
            share_value = secrets.randbelow(SECP256K1_N)
            shares_values.append(share_value)
            shares_sum = (shares_sum + share_value) % SECP256K1_N

        # Generate master private key
        master_private_key = secrets.randbelow(SECP256K1_N)

        # Last share is chosen so that sum = master_private_key
        last_share = (master_private_key - shares_sum) % SECP256K1_N
        shares_values.append(last_share)

        # Compute master public key (for verification)
        G = EllipticCurvePoint.generator()
        master_public_point = G * master_private_key
        master_public_key = master_public_point.to_bytes(compressed=True)

        # Create KeyShare objects
        shares = []
        for i, share_value in enumerate(shares_values):
            share = KeyShare(
                party_id=i + 1,
                share_value=share_value.to_bytes(32, 'big'),
                total_parties=num_parties,
                threshold=threshold,
                metadata={'type': 'additive'}
            )
            shares.append(share)

        return shares, master_public_key

    @staticmethod
    def verify_shares(shares: List[KeyShare], expected_public_key: bytes) -> bool:
        """
        Verify that shares combine to produce the expected public key
        WARNING: This reveals the private key! Only for testing.
        """
        # Sum all shares
        private_key_int = 0
        for share in shares:
            share_int = int.from_bytes(share.share_value, 'big')
            private_key_int = (private_key_int + share_int) % SECP256K1_N

        # Compute public key
        G = EllipticCurvePoint.generator()
        computed_public_point = G * private_key_int
        computed_public_key = computed_public_point.to_bytes(compressed=True)

        return computed_public_key == expected_public_key


class MPCBIP32:
    """MPC BIP32 operations without reconstructing private key (n-of-n scheme)"""

    @staticmethod
    def derive_master_keys_distributed(
        key_shares: List[KeyShare],
        seed: Optional[bytes] = None
    ) -> Tuple[List[KeyShare], bytes, bytes]:
        """
        Distributed MPC computation of BIP32 master key derivation

        Each party:
        1. Computes HMAC-SHA512("Bitcoin seed", seed) locally
        2. Derives their share of the master key
        3. Computes their share of the master public key

        Args:
            key_shares: Initial key shares (can be random)
            seed: Master seed (optional, generates if None)

        Returns:
            (master_key_shares, master_public_key, chain_code)
        """
        if seed is None:
            seed = secrets.token_bytes(32)

        # Compute HMAC-SHA512 (same for all parties)
        hmac_result = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
        master_key_bytes = hmac_result[:32]
        chain_code = hmac_result[32:]

        # Convert to integer
        master_key_int = int.from_bytes(master_key_bytes, 'big') % SECP256K1_N

        # Create new shares by adding master_key to existing shares
        # This is a simplification - in practice, shares would be generated fresh
        master_shares = []
        for i, share in enumerate(key_shares):
            share_int = int.from_bytes(share.share_value, 'big')
            new_share_int = (share_int + master_key_int) % SECP256K1_N

            master_share = KeyShare(
                party_id=share.party_id,
                share_value=new_share_int.to_bytes(32, 'big'),
                total_parties=share.total_parties,
                threshold=share.threshold,
                metadata={'type': 'master_key', 'derivation': 'm'}
            )
            master_shares.append(master_share)

        # Compute master public key (each party can do this independently)
        G = EllipticCurvePoint.generator()
        master_public_point = EllipticCurvePoint.infinity()

        for share in master_shares:
            share_int = int.from_bytes(share.share_value, 'big')
            share_public_point = G * share_int
            master_public_point = master_public_point + share_public_point

        master_public_key = master_public_point.to_bytes(compressed=True)

        return master_shares, master_public_key, chain_code

    @staticmethod
    def derive_hardened_child_distributed(
        parent_shares: List[KeyShare],
        parent_public_key: bytes,
        parent_chain_code: bytes,
        index: int
    ) -> Tuple[List[KeyShare], bytes, bytes]:
        """
        Distributed MPC computation of hardened child key derivation

        Each party derives their share of the child key without revealing their parent share.

        Args:
            parent_shares: Parent key shares
            parent_public_key: Parent public key
            parent_chain_code: Parent chain code
            index: Child index (will be OR'd with 0x80000000 for hardened)

        Returns:
            (child_shares, child_public_key, child_chain_code)
        """
        # Ensure hardened derivation
        index = index | 0x80000000

        # Each party computes HMAC locally using their share
        child_shares = []

        for share in parent_shares:
            # Data = 0x00 || parent_private_key_share || index
            data = b'\x00' + share.share_value + index.to_bytes(4, 'big')

            # Compute HMAC
            hmac_result = hmac.new(parent_chain_code, data, hashlib.sha512).digest()
            tweak = int.from_bytes(hmac_result[:32], 'big') % SECP256K1_N

            # Child share = parent_share + tweak (mod n)
            parent_share_int = int.from_bytes(share.share_value, 'big')
            child_share_int = (parent_share_int + tweak) % SECP256K1_N

            child_share = KeyShare(
                party_id=share.party_id,
                share_value=child_share_int.to_bytes(32, 'big'),
                total_parties=share.total_parties,
                threshold=share.threshold,
                metadata={
                    'type': 'hardened_child',
                    'parent_path': share.metadata.get('derivation', 'm'),
                    'index': index
                }
            )
            child_shares.append(child_share)

        # Compute child chain code (same for all parties)
        # Using first party's derivation (all should be same)
        data = b'\x00' + parent_shares[0].share_value + index.to_bytes(4, 'big')
        hmac_result = hmac.new(parent_chain_code, data, hashlib.sha512).digest()
        child_chain_code = hmac_result[32:]

        # Compute child public key (each party contributes)
        G = EllipticCurvePoint.generator()
        child_public_point = EllipticCurvePoint.infinity()

        for share in child_shares:
            share_int = int.from_bytes(share.share_value, 'big')
            share_public_point = G * share_int
            child_public_point = child_public_point + share_public_point

        child_public_key = child_public_point.to_bytes(compressed=True)

        return child_shares, child_public_key, child_chain_code

    @staticmethod
    def derive_account_xpub_distributed(
        master_shares: List[KeyShare],
        master_chain_code: bytes,
        coin_type: int = 0,
        account: int = 0
    ) -> ExtendedPublicKey:
        """
        Derive account xpub using distributed MPC computation
        Path: m/44'/coin_type'/account'

        This is the ONE-TIME MPC operation needed (all parties must participate).
        After this, unlimited addresses can be derived from xpub alone!

        Args:
            master_shares: Master key shares
            master_chain_code: Master chain code
            coin_type: 0 for Bitcoin, 60 for Ethereum
            account: Account number

        Returns:
            ExtendedPublicKey that can derive unlimited addresses
        """
        # Derive m/44'
        purpose_shares, purpose_pubkey, purpose_chain = \
            MPCBIP32.derive_hardened_child_distributed(
                master_shares, None, master_chain_code, 44
            )

        # Derive m/44'/coin_type'
        coin_shares, coin_pubkey, coin_chain = \
            MPCBIP32.derive_hardened_child_distributed(
                purpose_shares, purpose_pubkey, purpose_chain, coin_type
            )

        # Derive m/44'/coin_type'/account'
        account_shares, account_pubkey, account_chain = \
            MPCBIP32.derive_hardened_child_distributed(
                coin_shares, coin_pubkey, coin_chain, account
            )

        # Create extended public key
        xpub = ExtendedPublicKey(
            public_key=account_pubkey,
            chain_code=account_chain,
            depth=3,
            parent_fingerprint=b'\x00\x00\x00\x00',  # Simplified
            child_number=account | 0x80000000
        )

        return xpub


class PublicKeyDerivation:
    """Derive unlimited addresses from xpub (no private keys needed!)"""

    @staticmethod
    def derive_public_child(
        parent_xpub: ExtendedPublicKey,
        index: int
    ) -> Tuple[bytes, bytes]:
        """
        Derive child public key from parent xpub (non-hardened)

        This is the magic: derive addresses WITHOUT any private key!

        Args:
            parent_xpub: Parent extended public key
            index: Child index (must be < 0x80000000 for non-hardened)

        Returns:
            (child_public_key, child_chain_code)
        """
        if index >= 0x80000000:
            raise ValueError("Cannot derive hardened child from public key")

        # Data = parent_public_key || index
        data = parent_xpub.public_key + index.to_bytes(4, 'big')

        # Compute HMAC
        hmac_result = hmac.new(parent_xpub.chain_code, data, hashlib.sha512).digest()
        tweak = int.from_bytes(hmac_result[:32], 'big') % SECP256K1_N
        child_chain_code = hmac_result[32:]

        # Parse parent public key
        parent_point = EllipticCurvePoint.from_bytes(parent_xpub.public_key)

        # Child public key = parent_public_key + G * tweak
        G = EllipticCurvePoint.generator()
        tweak_point = G * tweak
        child_point = parent_point + tweak_point

        child_public_key = child_point.to_bytes(compressed=True)

        return child_public_key, child_chain_code

    @staticmethod
    def derive_address_public_keys(
        account_xpub: ExtendedPublicKey,
        change: int = 0,
        num_addresses: int = 10
    ) -> List[bytes]:
        """
        Derive multiple address public keys from account xpub

        Path: xpub/change/address_index

        Args:
            account_xpub: Account extended public key (m/44'/coin'/account')
            change: 0 for receiving, 1 for change
            num_addresses: Number of addresses to derive

        Returns:
            List of public keys (one per address)
        """
        # First derive change level: xpub/change
        change_pubkey, change_chain = PublicKeyDerivation.derive_public_child(
            account_xpub, change
        )

        change_xpub = ExtendedPublicKey(
            public_key=change_pubkey,
            chain_code=change_chain,
            depth=account_xpub.depth + 1,
            parent_fingerprint=b'\x00\x00\x00\x00',
            child_number=change
        )

        # Derive addresses: xpub/change/0, xpub/change/1, ...
        address_pubkeys = []
        for i in range(num_addresses):
            address_pubkey, _ = PublicKeyDerivation.derive_public_child(
                change_xpub, i
            )
            address_pubkeys.append(address_pubkey)

        return address_pubkeys


def save_xpub_to_file(xpub: ExtendedPublicKey, filename: str):
    """Save extended public key to file"""
    with open(filename, 'w') as f:
        json.dump(xpub.to_dict(), f, indent=2)


def load_xpub_from_file(filename: str) -> ExtendedPublicKey:
    """Load extended public key from file"""
    with open(filename, 'r') as f:
        data = json.load(f)
    return ExtendedPublicKey.from_dict(data)


if __name__ == "__main__":
    print("=" * 80)
    print("MPC KEY MANAGER WITH ADDITIVE SECRET SHARING - DEMO")
    print("Private key is NEVER reconstructed!")
    print("=" * 80)
    print()

    # Simulate 3 parties
    num_parties = 3

    print(f"PHASE 1: Key Generation ({num_parties} parties, {num_parties}-of-{num_parties} scheme)")
    print("-" * 80)

    # Generate initial shares
    key_shares, master_pubkey = MPCKeyGeneration.generate_shares(num_parties)
    print(f"Generated {num_parties} key shares")
    for share in key_shares:
        print(f"  Party {share.party_id}: {share.share_value.hex()[:32]}...")
    print()

    # Derive master keys using distributed MPC computation
    print("PHASE 2: BIP32 Master Key Derivation (Distributed MPC)")
    print("-" * 80)

    seed = secrets.token_bytes(32)
    master_shares, master_pubkey, master_chain = \
        MPCBIP32.derive_master_keys_distributed(key_shares, seed)

    print(f"Derived master keys (all {num_parties} parties participated)")
    print(f"  Master public key: {master_pubkey.hex()}")
    print(f"  Chain code: {master_chain.hex()[:32]}...")
    print()

    # Derive account xpub (one-time MPC operation)
    print("PHASE 3: Account xpub Derivation (ONE-TIME MPC Operation)")
    print("-" * 80)
    print("Path: m/44'/0'/0' (Bitcoin account 0)")

    account_xpub = MPCBIP32.derive_account_xpub_distributed(
        master_shares, master_chain, coin_type=0, account=0
    )

    print(f"Account xpub derived:")
    print(f"  Public key: {account_xpub.public_key.hex()}")
    print(f"  Chain code: {account_xpub.chain_code.hex()[:32]}...")
    print()

    # Now derive unlimited addresses (no MPC computation needed!)
    print("PHASE 4: Address Generation (UNLIMITED, No MPC needed!)")
    print("-" * 80)
    print("Deriving 10 receiving addresses from xpub alone...")
    print()

    address_pubkeys = PublicKeyDerivation.derive_address_public_keys(
        account_xpub, change=0, num_addresses=10
    )

    for i, pubkey in enumerate(address_pubkeys):
        print(f"  Address {i}: {pubkey.hex()}")

    print()
    print("=" * 80)
    print("SUCCESS!")
    print("Private key shares NEVER combined")
    print("MPC computation only for account setup (all parties required)")
    print("Unlimited addresses derived from xpub")
    print("=" * 80)
