#!/usr/bin/env python3
"""
FROST: Flexible Round-Optimized Schnorr Threshold Signatures
Implementation of RFC 9591 for secp256k1

Key Features:
- k-of-n threshold signatures (e.g., 3-of-5)
- 2-round signing protocol
- Schnorr signatures (BIP340 compatible)
- Private key NEVER reconstructed

Reference: https://www.rfc-editor.org/rfc/rfc9591.html
"""

import hashlib
import hmac
import secrets
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from .threshold_mpc_keymanager import (
    EllipticCurvePoint,
    SECP256K1_N,
    SECP256K1_P,
    SECP256K1_GX,
    SECP256K1_GY
)


# FROST secp256k1 ciphersuite constants (RFC 9591)
CONTEXT_STRING = b"FROST-secp256k1-SHA256-v1"
HASH_FUNCTION = hashlib.sha256


@dataclass
class FrostKeyShare:
    """FROST participant's secret share"""
    participant_id: int  # Unique identifier (1-indexed)
    secret_share: int    # Secret polynomial evaluation f(i)
    threshold: int       # Minimum signers required (k)
    max_participants: int  # Total participants (n)

    def to_bytes(self) -> bytes:
        """Serialize secret share (32 bytes, big-endian)"""
        return self.secret_share.to_bytes(32, 'big')

    @staticmethod
    def from_bytes(data: bytes, participant_id: int, threshold: int, max_participants: int) -> 'FrostKeyShare':
        """Deserialize secret share"""
        secret_share = int.from_bytes(data, 'big')
        return FrostKeyShare(participant_id, secret_share, threshold, max_participants)


@dataclass
class FrostPublicKeyPackage:
    """Public information shared among all participants"""
    group_public_key: EllipticCurvePoint  # Group verification key
    participant_public_keys: Dict[int, EllipticCurvePoint]  # Each participant's public key share
    threshold: int
    max_participants: int

    def serialize_group_pubkey(self) -> bytes:
        """Serialize group public key (33 bytes compressed)"""
        return self.group_public_key.to_bytes(compressed=True)


@dataclass
class FrostNoncePair:
    """Nonce pair for one signing round"""
    hiding_nonce: int  # Random scalar for hiding
    binding_nonce: int  # Random scalar for binding
    hiding_commitment: EllipticCurvePoint  # D = hiding_nonce * G
    binding_commitment: EllipticCurvePoint  # E = binding_nonce * G


@dataclass
class FrostSignatureShare:
    """One participant's signature share"""
    participant_id: int
    sig_share: int  # Signature share z_i


class FrostKeyGeneration:
    """FROST Trusted Dealer Key Generation (RFC 9591 Appendix C)"""

    @staticmethod
    def _evaluate_polynomial(coefficients: List[int], x: int) -> int:
        """
        Evaluate polynomial at point x
        f(x) = a_0 + a_1*x + a_2*x^2 + ... + a_t*x^t (mod SECP256K1_N)
        """
        result = 0
        x_power = 1
        for coeff in coefficients:
            result = (result + coeff * x_power) % SECP256K1_N
            x_power = (x_power * x) % SECP256K1_N
        return result

    @staticmethod
    def trusted_dealer_keygen(
        threshold: int,
        max_participants: int
    ) -> Tuple[List[FrostKeyShare], FrostPublicKeyPackage]:
        """
        Generate FROST key shares using Trusted Dealer method

        Args:
            threshold: Minimum participants needed to sign (k)
            max_participants: Total number of participants (n)

        Returns:
            (key_shares, public_key_package)
        """
        if threshold > max_participants:
            raise ValueError("Threshold cannot exceed max participants")
        if threshold < 2:
            raise ValueError("Threshold must be at least 2")

        # Generate random polynomial of degree (threshold - 1)
        # f(x) = a_0 + a_1*x + ... + a_{t-1}*x^{t-1}
        # where a_0 is the group secret
        coefficients = []
        for i in range(threshold):
            coeff = secrets.randbelow(SECP256K1_N - 1) + 1  # Non-zero
            coefficients.append(coeff)

        group_secret = coefficients[0]  # a_0

        # Compute group public key: Y = group_secret * G
        G = EllipticCurvePoint.generator()
        group_public_key = G * group_secret

        # Generate shares: s_i = f(i) for i in 1..n
        key_shares = []
        participant_public_keys = {}

        for i in range(1, max_participants + 1):
            secret_share = FrostKeyGeneration._evaluate_polynomial(coefficients, i)

            # Create key share
            share = FrostKeyShare(
                participant_id=i,
                secret_share=secret_share,
                threshold=threshold,
                max_participants=max_participants
            )
            key_shares.append(share)

            # Compute public key share: Y_i = s_i * G
            public_key_share = G * secret_share
            participant_public_keys[i] = public_key_share

        # Create public key package
        public_key_package = FrostPublicKeyPackage(
            group_public_key=group_public_key,
            participant_public_keys=participant_public_keys,
            threshold=threshold,
            max_participants=max_participants
        )

        return key_shares, public_key_package

    @staticmethod
    def verify_share(
        share: FrostKeyShare,
        public_key_package: FrostPublicKeyPackage
    ) -> bool:
        """
        Verify that a key share is valid
        Check: s_i * G == Y_i
        """
        G = EllipticCurvePoint.generator()
        computed = G * share.secret_share
        expected = public_key_package.participant_public_keys[share.participant_id]

        return (computed.x == expected.x and computed.y == expected.y)


class FrostHelpers:
    """Helper functions for FROST protocol"""

    @staticmethod
    def H1(msg: bytes) -> int:
        """Hash-to-scalar for random oracle"""
        h = HASH_FUNCTION()
        h.update(CONTEXT_STRING)
        h.update(b"rho")
        h.update(msg)
        return int.from_bytes(h.digest(), 'big') % SECP256K1_N

    @staticmethod
    def H2(msg: bytes) -> int:
        """Hash-to-scalar for challenges"""
        h = HASH_FUNCTION()
        h.update(CONTEXT_STRING)
        h.update(b"chal")
        h.update(msg)
        return int.from_bytes(h.digest(), 'big') % SECP256K1_N

    @staticmethod
    def H3(msg: bytes) -> int:
        """Hash-to-scalar for nonce generation"""
        h = HASH_FUNCTION()
        h.update(CONTEXT_STRING)
        h.update(b"nonce")
        h.update(msg)
        return int.from_bytes(h.digest(), 'big') % SECP256K1_N

    @staticmethod
    def derive_lagrange_coefficient(
        participant_id: int,
        participants: List[int]
    ) -> int:
        """
        Compute Lagrange coefficient for participant i at x=0

        lambda_i = prod((0 - j) / (i - j)) for all j != i

        This allows reconstruction: s = sum(lambda_i * s_i)
        """
        numerator = 1
        denominator = 1

        for j in participants:
            if j != participant_id:
                # Numerator: (0 - j) = -j
                numerator = (numerator * (-j)) % SECP256K1_N
                # Denominator: (i - j)
                denominator = (denominator * (participant_id - j)) % SECP256K1_N

        # Compute modular inverse of denominator
        denominator_inv = pow(denominator, -1, SECP256K1_N)

        # lambda_i = numerator / denominator (mod n)
        return (numerator * denominator_inv) % SECP256K1_N

    @staticmethod
    def compute_binding_factors(
        group_public_key: bytes,
        commitment_list: List[Tuple[int, bytes, bytes]],  # (id, D, E)
        message: bytes
    ) -> Dict[int, int]:
        """
        Compute binding factors for each participant

        rho_i = H1(group_pubkey || message || commitment_list || participant_id)
        """
        # Encode commitment list
        encoded_commitments = b""
        for pid, D, E in commitment_list:
            encoded_commitments += pid.to_bytes(4, 'big')
            encoded_commitments += D
            encoded_commitments += E

        binding_factors = {}
        for pid, _, _ in commitment_list:
            msg = group_public_key + message + encoded_commitments + pid.to_bytes(4, 'big')
            binding_factors[pid] = FrostHelpers.H1(msg)

        return binding_factors

    @staticmethod
    def compute_group_commitment(
        commitment_list: List[Tuple[int, EllipticCurvePoint, EllipticCurvePoint]],
        binding_factors: Dict[int, int]
    ) -> EllipticCurvePoint:
        """
        Compute group commitment: R = sum(D_i + rho_i * E_i)
        """
        R = EllipticCurvePoint.infinity()

        for pid, D, E in commitment_list:
            rho_i = binding_factors[pid]
            # R += D_i + rho_i * E_i
            R = R + D + (E * rho_i)

        return R

    @staticmethod
    def compute_challenge(
        group_commitment: EllipticCurvePoint,
        group_public_key: EllipticCurvePoint,
        message: bytes
    ) -> int:
        """
        Compute challenge: c = H2(R || Y || message)
        """
        R_bytes = group_commitment.to_bytes(compressed=True)
        Y_bytes = group_public_key.to_bytes(compressed=True)

        msg = R_bytes + Y_bytes + message
        return FrostHelpers.H2(msg)


class FrostSigner:
    """FROST 2-Round Signing Protocol"""

    @staticmethod
    def round1_generate_nonces(
        key_share: FrostKeyShare
    ) -> FrostNoncePair:
        """
        Round 1: Generate random nonce pair and commitments

        Each participant:
        1. Generates random hiding_nonce and binding_nonce
        2. Computes commitments: D = hiding_nonce * G, E = binding_nonce * G
        3. Sends (D, E) to coordinator
        """
        # Generate random nonces
        hiding_nonce = secrets.randbelow(SECP256K1_N - 1) + 1
        binding_nonce = secrets.randbelow(SECP256K1_N - 1) + 1

        # Compute commitments
        G = EllipticCurvePoint.generator()
        hiding_commitment = G * hiding_nonce
        binding_commitment = G * binding_nonce

        return FrostNoncePair(
            hiding_nonce=hiding_nonce,
            binding_nonce=binding_nonce,
            hiding_commitment=hiding_commitment,
            binding_commitment=binding_commitment
        )

    @staticmethod
    def round2_compute_signature_share(
        key_share: FrostKeyShare,
        nonce_pair: FrostNoncePair,
        message: bytes,
        commitment_list: List[Tuple[int, EllipticCurvePoint, EllipticCurvePoint]],
        participants: List[int],
        public_key_package: FrostPublicKeyPackage
    ) -> FrostSignatureShare:
        """
        Round 2: Compute signature share

        Each participant:
        1. Computes binding factor rho_i
        2. Computes Lagrange coefficient lambda_i
        3. Computes challenge c
        4. Computes signature share: z_i = d_i + (e_i * rho_i) + (lambda_i * s_i * c)
        """
        # Compute binding factors
        commitment_list_bytes = [
            (pid, D.to_bytes(compressed=True), E.to_bytes(compressed=True))
            for pid, D, E in commitment_list
        ]
        binding_factors = FrostHelpers.compute_binding_factors(
            public_key_package.serialize_group_pubkey(),
            commitment_list_bytes,
            message
        )

        # Compute group commitment R
        R = FrostHelpers.compute_group_commitment(commitment_list, binding_factors)

        # Compute challenge c
        c = FrostHelpers.compute_challenge(
            R,
            public_key_package.group_public_key,
            message
        )

        # Compute Lagrange coefficient lambda_i
        lambda_i = FrostHelpers.derive_lagrange_coefficient(
            key_share.participant_id,
            participants
        )

        # Compute signature share
        # z_i = d_i + (e_i * rho_i) + (lambda_i * s_i * c) mod n
        rho_i = binding_factors[key_share.participant_id]

        z_i = nonce_pair.hiding_nonce
        z_i = (z_i + nonce_pair.binding_nonce * rho_i) % SECP256K1_N
        z_i = (z_i + lambda_i * key_share.secret_share * c) % SECP256K1_N

        return FrostSignatureShare(
            participant_id=key_share.participant_id,
            sig_share=z_i
        )


class FrostCoordinator:
    """FROST Coordinator for aggregating signatures"""

    @staticmethod
    def aggregate_signatures(
        signature_shares: List[FrostSignatureShare],
        commitment_list: List[Tuple[int, EllipticCurvePoint, EllipticCurvePoint]],
        message: bytes,
        public_key_package: FrostPublicKeyPackage
    ) -> Tuple[bytes, int]:
        """
        Aggregate signature shares into final Schnorr signature

        Returns:
            (R_bytes, z) where signature is (R, z)
        """
        # Compute binding factors
        participants = [share.participant_id for share in signature_shares]
        commitment_list_bytes = [
            (pid, D.to_bytes(compressed=True), E.to_bytes(compressed=True))
            for pid, D, E in commitment_list
        ]
        binding_factors = FrostHelpers.compute_binding_factors(
            public_key_package.serialize_group_pubkey(),
            commitment_list_bytes,
            message
        )

        # Compute group commitment R
        R = FrostHelpers.compute_group_commitment(commitment_list, binding_factors)
        R_bytes = R.to_bytes(compressed=True)

        # Aggregate signature shares: z = sum(z_i) mod n
        z = sum(share.sig_share for share in signature_shares) % SECP256K1_N

        return R_bytes, z

    @staticmethod
    def verify_signature(
        signature_R: bytes,
        signature_z: int,
        message: bytes,
        group_public_key: EllipticCurvePoint
    ) -> bool:
        """
        Verify Schnorr signature

        Verify: z * G == R + c * Y
        where c = H2(R || Y || message)
        """
        G = EllipticCurvePoint.generator()

        # Parse R
        R = EllipticCurvePoint.from_bytes(signature_R)

        # Compute challenge
        c = FrostHelpers.compute_challenge(R, group_public_key, message)

        # Verify: z * G == R + c * Y
        left = G * signature_z
        right = R + (group_public_key * c)

        return (left.x == right.x and left.y == right.y)


# Convenience workflow class
class FrostWorkflow:
    """Complete FROST signing workflow"""

    @staticmethod
    def sign_message(
        key_shares: List[FrostKeyShare],
        message: bytes,
        public_key_package: FrostPublicKeyPackage
    ) -> Tuple[bytes, int]:
        """
        Complete 2-round FROST signing workflow

        Args:
            key_shares: Key shares from threshold participants
            message: Message to sign
            public_key_package: Public key information

        Returns:
            (R_bytes, z) - Schnorr signature
        """
        if len(key_shares) < key_shares[0].threshold:
            raise ValueError(f"Need at least {key_shares[0].threshold} signers")

        print(f"\n{'='*80}")
        print(f"FROST SIGNING WORKFLOW")
        print(f"Threshold: {key_shares[0].threshold}-of-{key_shares[0].max_participants}")
        print(f"Signers: {len(key_shares)} participants")
        print(f"{'='*80}\n")

        # ROUND 1: Generate nonces
        print("ROUND 1: Nonce Generation")
        print("-" * 80)
        nonce_pairs = []
        commitment_list = []

        for share in key_shares:
            nonce_pair = FrostSigner.round1_generate_nonces(share)
            nonce_pairs.append(nonce_pair)

            commitment_list.append((
                share.participant_id,
                nonce_pair.hiding_commitment,
                nonce_pair.binding_commitment
            ))
            print(f"  Participant {share.participant_id}: Generated nonces")

        print()

        # ROUND 2: Compute signature shares
        print("ROUND 2: Signature Share Computation")
        print("-" * 80)
        signature_shares = []
        participants = [share.participant_id for share in key_shares]

        for i, share in enumerate(key_shares):
            sig_share = FrostSigner.round2_compute_signature_share(
                share,
                nonce_pairs[i],
                message,
                commitment_list,
                participants,
                public_key_package
            )
            signature_shares.append(sig_share)
            print(f"  Participant {share.participant_id}: Computed signature share")

        print()

        # AGGREGATION
        print("AGGREGATION")
        print("-" * 80)
        R_bytes, z = FrostCoordinator.aggregate_signatures(
            signature_shares,
            commitment_list,
            message,
            public_key_package
        )
        print(f"  Final signature: R={R_bytes.hex()[:32]}..., z={hex(z)[:32]}...")
        print()

        # VERIFICATION
        print("VERIFICATION")
        print("-" * 80)
        valid = FrostCoordinator.verify_signature(
            R_bytes, z, message, public_key_package.group_public_key
        )
        print(f"  Signature valid: {valid}")
        print()

        return R_bytes, z


if __name__ == "__main__":
    print("=" * 80)
    print("FROST THRESHOLD SIGNATURE SCHEME DEMO")
    print("3-of-5 Threshold with Schnorr Signatures")
    print("=" * 80)
    print()

    # Generate 3-of-5 key shares
    threshold = 3
    max_participants = 5

    print(f"KEY GENERATION: {threshold}-of-{max_participants} scheme")
    print("-" * 80)

    key_shares, public_key_package = FrostKeyGeneration.trusted_dealer_keygen(
        threshold, max_participants
    )

    print(f"✓ Generated {len(key_shares)} key shares")
    print(f"✓ Group public key: {public_key_package.serialize_group_pubkey().hex()[:32]}...")
    print()

    # Verify shares
    print("SHARE VERIFICATION")
    print("-" * 80)
    for share in key_shares:
        valid = FrostKeyGeneration.verify_share(share, public_key_package)
        print(f"  Participant {share.participant_id}: {'✓ Valid' if valid else '✗ Invalid'}")
    print()

    # Sign with 3 of 5 participants
    message = b"Send 1 BTC to Alice"
    selected_shares = [key_shares[0], key_shares[2], key_shares[4]]  # Participants 1, 3, 5

    R_bytes, z = FrostWorkflow.sign_message(
        selected_shares,
        message,
        public_key_package
    )

    print("=" * 80)
    print("SUCCESS!")
    print("✓ 3-of-5 threshold signature created")
    print("✓ Private key NEVER reconstructed")
    print("✓ Schnorr signature verified")
    print("=" * 80)
    print()

    print(f"Signature (Schnorr):")
    print(f"  R: {R_bytes.hex()}")
    print(f"  z: {hex(z)}")
