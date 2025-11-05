"""
GuardianVault - Multi-Party Computation Cryptocurrency Key Manager

A Python library for secure threshold cryptography and MPC-based key management.
"""

from .threshold_mpc_keymanager import (
    ThresholdKeyGeneration,
    ThresholdBIP32,
    KeyShare,
    ExtendedPublicKey
)
from .threshold_signing import ThresholdSigner, KeyShare as SigningKeyShare
from .threshold_addresses import BitcoinAddressGenerator, EthereumAddressGenerator

__version__ = "0.1.0"
__all__ = [
    "ThresholdKeyGeneration",
    "ThresholdBIP32",
    "KeyShare",
    "ExtendedPublicKey",
    "ThresholdSigner",
    "SigningKeyShare",
    "BitcoinAddressGenerator",
    "EthereumAddressGenerator",
]
