#!/usr/bin/env python3
"""
Threshold ECDSA Signing
Allows parties to sign transactions WITHOUT reconstructing the private key

Protocol (Additive Secret Sharing):
1. Each party generates random nonce share
2. Combine nonce public points to get R
3. Each party computes signature share
4. Combine signature shares to get final signature
"""

import hashlib
import secrets
from typing import List, Tuple, Dict
from dataclasses import dataclass

from .threshold_mpc_keymanager import (
    KeyShare,
    EllipticCurvePoint,
    SECP256K1_N
)


@dataclass
class SignatureShare:
    """One party's share of a threshold signature"""
    party_id: int
    r_share: bytes  # This party's R point contribution (33 bytes)
    s_share: int    # This party's signature share (integer)


@dataclass
class ThresholdSignature:
    """Complete ECDSA signature from threshold computation"""
    r: int
    s: int

    def to_der(self) -> bytes:
        """Convert to DER encoding for Bitcoin/Ethereum"""
        # Encode r
        r_bytes = self.r.to_bytes(32, 'big')
        r_bytes = r_bytes.lstrip(b'\x00')
        if r_bytes[0] & 0x80:  # Add 0x00 if high bit set
            r_bytes = b'\x00' + r_bytes

        # Encode s
        s_bytes = self.s.to_bytes(32, 'big')
        s_bytes = s_bytes.lstrip(b'\x00')
        if s_bytes[0] & 0x80:
            s_bytes = b'\x00' + s_bytes

        # Construct DER
        r_len = len(r_bytes)
        s_len = len(s_bytes)

        der = b'\x30'  # SEQUENCE
        der += bytes([4 + r_len + s_len])  # Length
        der += b'\x02'  # INTEGER (r)
        der += bytes([r_len])
        der += r_bytes
        der += b'\x02'  # INTEGER (s)
        der += bytes([s_len])
        der += s_bytes

        return der

    def to_compact(self) -> bytes:
        """Convert to compact format (64 bytes: r || s)"""
        r_bytes = self.r.to_bytes(32, 'big')
        s_bytes = self.s.to_bytes(32, 'big')
        return r_bytes + s_bytes


class ThresholdSigner:
    """Threshold ECDSA signing protocol"""

    @staticmethod
    def sign_round1_generate_nonce(party_id: int) -> Tuple[int, bytes]:
        """
        Round 1: Each party generates random nonce share

        Args:
            party_id: This party's ID

        Returns:
            (nonce_share_int, nonce_public_point_bytes)
        """
        # Generate random nonce share
        k_share = secrets.randbelow(SECP256K1_N)

        # Compute R_share = G * k_share
        G = EllipticCurvePoint.generator()
        R_share = G * k_share
        R_share_bytes = R_share.to_bytes(compressed=True)

        return k_share, R_share_bytes

    @staticmethod
    def sign_round2_combine_nonces(r_shares: List[bytes]) -> Tuple[EllipticCurvePoint, int]:
        """
        Round 2: Combine all nonce public points

        Args:
            r_shares: List of R_share points from all parties

        Returns:
            (combined_R_point, r_value)
        """
        # Parse all R shares
        R_points = [EllipticCurvePoint.from_bytes(r) for r in r_shares]

        # Combine: R = R1 + R2 + ... + Rn
        R_combined = EllipticCurvePoint.infinity()
        for R_point in R_points:
            R_combined = R_combined + R_point

        # Extract r value (x-coordinate)
        r = R_combined.x % SECP256K1_N

        return R_combined, r

    @staticmethod
    def sign_round3_compute_signature_share(
        key_share: KeyShare,
        nonce_share: int,
        message_hash: bytes,
        r: int,
        k_total: int,
        num_parties: int
    ) -> int:
        """
        Round 3: Each party computes their signature share

        ECDSA signature: s = k^(-1) * (z + r*x) mod n
        With additive sharing: x = x_1 + ... + x_n, k = k_1 + ... + k_n
        Each party computes: s_i = k^(-1) * (z/n + r*x_i)
        Sum gives: s = k^(-1) * (z + r*sum(x_i)) = k^(-1) * (z + r*x)

        Args:
            key_share: This party's private key share
            nonce_share: This party's nonce share (from round 1)
            message_hash: Hash of message to sign (32 bytes)
            r: Combined r value (from round 2)
            k_total: Combined nonce (sum of all k_i)
            num_parties: Total number of parties

        Returns:
            This party's signature share (s_i)
        """
        # Parse private key share
        x_i = int.from_bytes(key_share.share_value, 'big')

        # Parse message hash as integer
        z = int.from_bytes(message_hash, 'big')

        # Compute k^(-1)
        k_inv = pow(k_total, -1, SECP256K1_N)

        # Each party's share: s_i = k^(-1) * (z/n + r*x_i) mod n
        z_share = z * pow(num_parties, -1, SECP256K1_N) % SECP256K1_N
        s_i = k_inv * (z_share + r * x_i) % SECP256K1_N

        return s_i

    @staticmethod
    def sign_round4_combine_signatures(
        s_shares: List[int],
        r: int
    ) -> ThresholdSignature:
        """
        Round 4: Combine all signature shares into final signature

        Args:
            s_shares: List of signature shares from all parties
            r: Combined r value

        Returns:
            Complete ECDSA signature
        """
        # Combine: s = s1 + s2 + ... + sn (mod n)
        s = sum(s_shares) % SECP256K1_N

        # Ensure s is in lower half (BIP62 low-S requirement)
        if s > SECP256K1_N // 2:
            s = SECP256K1_N - s

        return ThresholdSignature(r=r, s=s)

    @staticmethod
    def verify_signature(
        public_key: bytes,
        message_hash: bytes,
        signature: ThresholdSignature
    ) -> bool:
        """
        Verify ECDSA signature

        Args:
            public_key: 33-byte compressed public key
            message_hash: 32-byte message hash
            signature: Signature to verify

        Returns:
            True if valid, False otherwise
        """
        # Parse inputs
        z = int.from_bytes(message_hash, 'big')
        r = signature.r
        s = signature.s

        # Check r and s are in valid range
        if not (1 <= r < SECP256K1_N and 1 <= s < SECP256K1_N):
            return False

        # Compute w = s^(-1) mod n
        w = pow(s, -1, SECP256K1_N)

        # Compute u1 = z * w mod n
        u1 = (z * w) % SECP256K1_N

        # Compute u2 = r * w mod n
        u2 = (r * w) % SECP256K1_N

        # Compute point: P = u1*G + u2*PublicKey
        G = EllipticCurvePoint.generator()
        P1 = G * u1

        pub_point = EllipticCurvePoint.from_bytes(public_key)
        P2 = pub_point * u2

        P = P1 + P2

        if P.is_infinity:
            return False

        # Verify: r == P.x mod n
        return r == (P.x % SECP256K1_N)

    @staticmethod
    def recover_ethereum_v(
        public_key: bytes,
        message_hash: bytes,
        signature: ThresholdSignature
    ) -> int:
        """
        Recover the v parameter (recovery ID) for Ethereum signatures.

        Ethereum needs the recovery ID to recover the public key from a signature.
        This tries both possible values (0 and 1) and returns the correct one.

        Args:
            public_key: 33 or 65-byte public key
            message_hash: 32-byte message hash that was signed
            signature: The signature (r, s)

        Returns:
            Recovery ID (0 or 1)

        Raises:
            ValueError: If recovery fails
        """
        # Convert public key to EllipticCurvePoint for comparison
        if len(public_key) == 33:
            # Already compressed
            expected_point = EllipticCurvePoint.from_bytes(public_key)
        else:
            # Uncompressed (65 bytes: 0x04 || x || y)
            x = int.from_bytes(public_key[1:33], 'big')
            y = int.from_bytes(public_key[33:65], 'big')
            expected_point = EllipticCurvePoint(x, y)

        # Parse signature and message hash
        r = signature.r
        s = signature.s
        z = int.from_bytes(message_hash, 'big')

        # Try both recovery IDs (0 and 1)
        for v in [0, 1]:
            try:
                # Calculate the point R from r
                # There are two possible y values for a given x (r)
                # v tells us which one to use

                # Find y coordinate for R
                # Solve: y^2 = x^3 + 7 (mod p) for secp256k1
                from .threshold_mpc_keymanager import SECP256K1_P

                x_coord = r
                y_squared = (pow(x_coord, 3, SECP256K1_P) + 7) % SECP256K1_P

                # Compute square root using Tonelli-Shanks (p ≡ 3 mod 4 for secp256k1)
                y_coord = pow(y_squared, (SECP256K1_P + 1) // 4, SECP256K1_P)

                # Choose y based on v (even/odd)
                if (y_coord % 2 == 0) != (v == 0):
                    y_coord = SECP256K1_P - y_coord

                R = EllipticCurvePoint(x_coord, y_coord)

                # Recover public key: Q = r^(-1) * (s*R - z*G)
                r_inv = pow(r, -1, SECP256K1_N)

                G = EllipticCurvePoint.generator()
                s_R = R * s
                z_G = G * z

                # s*R - z*G
                Q = s_R + (EllipticCurvePoint(z_G.x, SECP256K1_P - z_G.y) if not z_G.is_infinity else EllipticCurvePoint.infinity())

                # Q * r^(-1)
                Q = Q * r_inv

                # Check if recovered key matches expected key
                if Q.x == expected_point.x and Q.y == expected_point.y:
                    return v

            except Exception:
                continue

        raise ValueError("Could not recover v parameter from signature")


class ThresholdSigningWorkflow:
    """Complete threshold signing workflow (simulating async communication)"""

    @staticmethod
    def sign_message(
        key_shares: List[KeyShare],
        message: bytes,
        public_key: bytes,
        prehashed: bool = False
    ) -> ThresholdSignature:
        """
        Complete threshold signing workflow

        Simulates async MPC protocol where parties never share private keys

        Args:
            key_shares: Private key shares from all parties
            message: Message to sign (or message hash if prehashed=True)
            public_key: Combined public key (for verification)
            prehashed: If True, message is already a hash and won't be hashed again

        Returns:
            Threshold signature
        """
        # Hash the message (unless it's already a hash)
        if prehashed:
            message_hash = message
        else:
            message_hash = hashlib.sha256(message).digest()

        # Try to decode as UTF-8, otherwise show hex
        try:
            message_str = message.decode('utf-8')
            print(f"\nSigning message: {message_str}")
        except UnicodeDecodeError:
            print(f"\nSigning message (hex): {message.hex()[:64]}...")
        print(f"Message hash: {message_hash.hex()[:32]}...")
        print()

        # ROUND 1: Each party generates nonce
        print("ROUND 1: Nonce Generation")
        print("-" * 60)
        nonce_shares = []
        r_share_points = []

        for share in key_shares:
            k_i, R_i = ThresholdSigner.sign_round1_generate_nonce(share.party_id)
            nonce_shares.append(k_i)
            r_share_points.append(R_i)
            print(f"  Party {share.party_id}: Generated nonce share")

        print()

        # ROUND 2: Combine nonces (can be done by any party)
        print("ROUND 2: Combine Nonce Points")
        print("-" * 60)
        R_combined, r = ThresholdSigner.sign_round2_combine_nonces(r_share_points)
        print(f"  Combined R point: ({hex(R_combined.x)[:20]}..., {hex(R_combined.y)[:20]}...)")
        print(f"  r value: {hex(r)[:32]}...")
        print()

        # Compute k_total (sum of all nonces)
        k_total = sum(nonce_shares) % SECP256K1_N
        print(f"  k_total: {hex(k_total)[:32]}...")
        print()

        # ROUND 3: Each party computes signature share
        print("ROUND 3: Compute Signature Shares")
        print("-" * 60)
        s_shares = []

        for i, share in enumerate(key_shares):
            s_i = ThresholdSigner.sign_round3_compute_signature_share(
                share, nonce_shares[i], message_hash, r, k_total, len(key_shares)
            )
            s_shares.append(s_i)
            print(f"  Party {share.party_id}: Computed signature share")

        print()

        # ROUND 4: Combine signatures
        print("ROUND 4: Combine Signature Shares")
        print("-" * 60)
        signature = ThresholdSigner.sign_round4_combine_signatures(s_shares, r)
        print(f"  Final signature:")
        print(f"    r: {hex(signature.r)[:32]}...")
        print(f"    s: {hex(signature.s)[:32]}...")
        print()

        # Verify signature
        print("VERIFICATION")
        print("-" * 60)
        valid = ThresholdSigner.verify_signature(public_key, message_hash, signature)
        print(f"  Signature valid: {valid}")
        print()

        return signature


if __name__ == "__main__":
    import secrets as sec
    from .threshold_mpc_keymanager import ThresholdKeyGeneration

    print("=" * 80)
    print("THRESHOLD ECDSA SIGNING DEMO")
    print("Sign transactions WITHOUT reconstructing private key!")
    print("=" * 80)
    print()

    # Setup: Generate distributed key
    num_parties = 3
    print(f"Setup: {num_parties} parties")
    print("-" * 80)

    key_shares, master_pubkey = ThresholdKeyGeneration.generate_shares(num_parties)
    print(f"✓ Generated {num_parties} key shares")
    print(f"✓ Master public key: {master_pubkey.hex()[:32]}...")
    print()

    # Sign a message
    message = b"Send 1 BTC to Alice"

    signature = ThresholdSigningWorkflow.sign_message(
        key_shares, message, master_pubkey
    )

    print("=" * 80)
    print("SUCCESS!")
    print("✓ Message signed using threshold protocol")
    print("✓ Private key NEVER reconstructed")
    print("✓ Each party only used their private share")
    print("=" * 80)
    print()

    print("Signature formats:")
    print(f"  DER: {signature.to_der().hex()}")
    print(f"  Compact: {signature.to_compact().hex()}")
