"""
Ethereum RPC Client for practical demo scripts

Re-exports the EthereumRPCClient from the main guardianvault package
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from guardianvault.ethereum_rpc import EthereumRPCClient

__all__ = ['EthereumRPCClient']
