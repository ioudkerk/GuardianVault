"""
GuardianVault - Multi-Party Computation Cryptocurrency Key Manager

A Python library for secure MPC-based key management using additive secret sharing.
This implements an (n,n) scheme where all parties must participate to sign.
"""

from .mpc_keymanager import (
    MPCKeyGeneration,
    MPCBIP32,
    KeyShare,
    ExtendedPublicKey,
    PublicKeyDerivation,
    EllipticCurvePoint,
    SECP256K1_N,
    SECP256K1_P,
)
from .mpc_signing import (
    MPCSigner,
    MPCSigningWorkflow,
    SignatureShare,
    ThresholdSignature,
    KeyShare as SigningKeyShare,
)
from .mpc_addresses import BitcoinAddressGenerator, EthereumAddressGenerator

# Backwards compatibility aliases (deprecated - will be removed in future versions)
ThresholdKeyGeneration = MPCKeyGeneration
ThresholdBIP32 = MPCBIP32
ThresholdSigner = MPCSigner
ThresholdSigningWorkflow = MPCSigningWorkflow

__version__ = "0.2.0"
__all__ = [
    # New names (preferred)
    "MPCKeyGeneration",
    "MPCBIP32",
    "MPCSigner",
    "MPCSigningWorkflow",
    "KeyShare",
    "ExtendedPublicKey",
    "PublicKeyDerivation",
    "EllipticCurvePoint",
    "SignatureShare",
    "ThresholdSignature",
    "BitcoinAddressGenerator",
    "EthereumAddressGenerator",
    "SECP256K1_N",
    "SECP256K1_P",
    # Backwards compatibility (deprecated)
    "ThresholdKeyGeneration",
    "ThresholdBIP32",
    "ThresholdSigner",
    "ThresholdSigningWorkflow",
    "SigningKeyShare",
]
