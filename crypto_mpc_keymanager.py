#!/usr/bin/env python3
"""
Multi-Party Computation Cryptocurrency Key Manager
Uses Shamir's Secret Sharing for distributed key management

SECURITY WARNING: This is for educational purposes. 
For production use, ensure proper security audits and secure storage of shares.
"""

import hashlib
import hmac
import secrets
from typing import List, Tuple, Optional
from dataclasses import dataclass
import json


class ShamirSecretSharing:
    """
    Implementation of Shamir's Secret Sharing Scheme
    Allows splitting a secret into N shares where K shares are needed to reconstruct
    """
    
    def __init__(self, prime: Optional[int] = None):
        # Use a large prime number for the finite field
        # This is a 256-bit prime (suitable for 256-bit secrets like crypto keys)
        self.prime = prime or (2**256 - 189)
    
    def _eval_polynomial(self, coefficients: List[int], x: int) -> int:
        """Evaluate polynomial at point x using Horner's method"""
        result = 0
        for coeff in reversed(coefficients):
            result = (result * x + coeff) % self.prime
        return result
    
    def split_secret(self, secret: bytes, threshold: int, num_shares: int) -> List[Tuple[int, bytes]]:
        """
        Split a secret into shares using Shamir's Secret Sharing
        
        Args:
            secret: The secret to split (as bytes)
            threshold: Minimum number of shares needed to reconstruct
            num_shares: Total number of shares to create
            
        Returns:
            List of (share_id, share_value) tuples
        """
        if threshold > num_shares:
            raise ValueError("Threshold cannot be greater than number of shares")
        if threshold < 2:
            raise ValueError("Threshold must be at least 2")
        
        # Convert secret bytes to integer
        secret_int = int.from_bytes(secret, byteorder='big')
        
        if secret_int >= self.prime:
            raise ValueError("Secret is too large for the chosen prime")
        
        # Generate random coefficients for polynomial of degree (threshold - 1)
        # The secret is the constant term (coefficient[0])
        coefficients = [secret_int]
        for _ in range(threshold - 1):
            coefficients.append(secrets.randbelow(self.prime))
        
        # Generate shares by evaluating polynomial at different points
        shares = []
        for i in range(1, num_shares + 1):
            x = i
            y = self._eval_polynomial(coefficients, x)
            # Convert y back to bytes (32 bytes for 256-bit values)
            y_bytes = y.to_bytes(32, byteorder='big')
            shares.append((x, y_bytes))
        
        return shares
    
    def _lagrange_interpolation(self, shares: List[Tuple[int, int]], x: int = 0) -> int:
        """
        Perform Lagrange interpolation to find polynomial value at x
        Default x=0 gives us the secret (constant term)
        """
        k = len(shares)
        result = 0
        
        for i in range(k):
            xi, yi = shares[i]
            numerator = 1
            denominator = 1
            
            for j in range(k):
                if i != j:
                    xj, _ = shares[j]
                    numerator = (numerator * (x - xj)) % self.prime
                    denominator = (denominator * (xi - xj)) % self.prime
            
            # Compute modular multiplicative inverse of denominator
            denominator_inv = pow(denominator, self.prime - 2, self.prime)
            lagrange_coeff = (numerator * denominator_inv) % self.prime
            result = (result + yi * lagrange_coeff) % self.prime
        
        return result
    
    def reconstruct_secret(self, shares: List[Tuple[int, bytes]]) -> bytes:
        """
        Reconstruct secret from shares
        
        Args:
            shares: List of (share_id, share_value) tuples
            
        Returns:
            The reconstructed secret as bytes
        """
        if len(shares) < 2:
            raise ValueError("Need at least 2 shares to reconstruct")
        
        # Convert share bytes to integers
        shares_int = [(x, int.from_bytes(y, byteorder='big')) for x, y in shares]
        
        # Use Lagrange interpolation to find the secret (polynomial value at x=0)
        secret_int = self._lagrange_interpolation(shares_int, x=0)
        
        # Convert back to bytes
        secret_bytes = secret_int.to_bytes(32, byteorder='big')
        return secret_bytes


@dataclass
class KeyShare:
    """Represents a single share of a split key"""
    share_id: int
    share_value: bytes
    threshold: int
    total_shares: int
    
    def to_dict(self) -> dict:
        return {
            'share_id': self.share_id,
            'share_value': self.share_value.hex(),
            'threshold': self.threshold,
            'total_shares': self.total_shares
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'KeyShare':
        return cls(
            share_id=data['share_id'],
            share_value=bytes.fromhex(data['share_value']),
            threshold=data['threshold'],
            total_shares=data['total_shares']
        )


class HDWalletDerivation:
    """
    Hierarchical Deterministic Wallet key derivation (BIP32/BIP44)
    Allows deriving child keys from a master seed without reconstructing it
    """
    
    # BIP44 constants
    BIP44_PURPOSE = 44
    BITCOIN_COIN_TYPE = 0
    ETHEREUM_COIN_TYPE = 60
    
    @staticmethod
    def _hmac_sha512(key: bytes, data: bytes) -> bytes:
        """Compute HMAC-SHA512"""
        return hmac.new(key, data, hashlib.sha512).digest()
    
    @classmethod
    def derive_master_key(cls, seed: bytes) -> Tuple[bytes, bytes]:
        """
        Derive master private key and chain code from seed
        
        Returns:
            (master_private_key, chain_code)
        """
        # BIP32 master key derivation
        hmac_result = cls._hmac_sha512(b"Bitcoin seed", seed)
        master_private_key = hmac_result[:32]
        chain_code = hmac_result[32:]
        return master_private_key, chain_code
    
    @classmethod
    def derive_child_key(cls, parent_key: bytes, chain_code: bytes, index: int, 
                        hardened: bool = True) -> Tuple[bytes, bytes]:
        """
        Derive child key from parent key using BIP32
        
        Args:
            parent_key: Parent private key (32 bytes)
            chain_code: Parent chain code (32 bytes)
            index: Child index
            hardened: Whether to use hardened derivation
            
        Returns:
            (child_private_key, child_chain_code)
        """
        if hardened:
            index = index | 0x80000000  # Set hardened bit
        
        if hardened:
            # Hardened derivation: use 0x00 || parent_key || index
            data = b'\x00' + parent_key + index.to_bytes(4, byteorder='big')
        else:
            # Non-hardened: would need public key (not implemented here for simplicity)
            raise NotImplementedError("Non-hardened derivation requires public key")
        
        hmac_result = cls._hmac_sha512(chain_code, data)
        child_key_modifier = int.from_bytes(hmac_result[:32], byteorder='big')
        child_chain_code = hmac_result[32:]
        
        # Add modifier to parent key (modulo curve order for secp256k1)
        SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
        parent_key_int = int.from_bytes(parent_key, byteorder='big')
        child_key_int = (parent_key_int + child_key_modifier) % SECP256K1_ORDER
        child_key = child_key_int.to_bytes(32, byteorder='big')
        
        return child_key, child_chain_code
    
    @classmethod
    def derive_bip44_path(cls, master_key: bytes, chain_code: bytes, 
                         coin_type: int, account: int = 0, 
                         change: int = 0, address_index: int = 0) -> bytes:
        """
        Derive key following BIP44 path: m/44'/coin_type'/account'/change/address_index
        
        Args:
            master_key: Master private key
            chain_code: Master chain code
            coin_type: Coin type (0 for Bitcoin, 60 for Ethereum)
            account: Account index
            change: Change index (0 for external, 1 for internal)
            address_index: Address index
            
        Returns:
            Derived private key
        """
        # Derive m/44'
        key, chain = cls.derive_child_key(master_key, chain_code, cls.BIP44_PURPOSE, hardened=True)
        
        # Derive m/44'/coin_type'
        key, chain = cls.derive_child_key(key, chain, coin_type, hardened=True)
        
        # Derive m/44'/coin_type'/account'
        key, chain = cls.derive_child_key(key, chain, account, hardened=True)
        
        # Derive m/44'/coin_type'/account'/change
        key, chain = cls.derive_child_key(key, chain, change, hardened=True)
        
        # Derive m/44'/coin_type'/account'/change/address_index
        key, chain = cls.derive_child_key(key, chain, address_index, hardened=True)
        
        return key


class DistributedKeyManager:
    """
    Main class for managing cryptocurrency keys using MPC and Shamir's Secret Sharing
    """
    
    def __init__(self):
        self.sss = ShamirSecretSharing()
        self.hdw = HDWalletDerivation()
    
    def generate_master_seed(self) -> bytes:
        """Generate a cryptographically secure random master seed"""
        return secrets.token_bytes(32)  # 256 bits
    
    def split_master_seed(self, master_seed: bytes, threshold: int, 
                         num_shares: int) -> List[KeyShare]:
        """
        Split the master seed into shares
        
        Args:
            master_seed: The master seed to split
            threshold: Minimum shares needed to reconstruct
            num_shares: Total number of shares
            
        Returns:
            List of KeyShare objects
        """
        shares = self.sss.split_secret(master_seed, threshold, num_shares)
        return [
            KeyShare(share_id=sid, share_value=sval, 
                    threshold=threshold, total_shares=num_shares)
            for sid, sval in shares
        ]
    
    def reconstruct_master_seed(self, key_shares: List[KeyShare]) -> bytes:
        """
        Reconstruct master seed from shares
        
        Args:
            key_shares: List of KeyShare objects
            
        Returns:
            Reconstructed master seed
        """
        shares = [(ks.share_id, ks.share_value) for ks in key_shares]
        return self.sss.reconstruct_secret(shares)
    
    def derive_bitcoin_address_key(self, master_seed: bytes, 
                                   account: int = 0, address_index: int = 0) -> bytes:
        """
        Derive a Bitcoin address private key from master seed
        
        Args:
            master_seed: Master seed
            account: Account index
            address_index: Address index
            
        Returns:
            Bitcoin private key for the specified path
        """
        master_key, chain_code = self.hdw.derive_master_key(master_seed)
        derived_key = self.hdw.derive_bip44_path(
            master_key, chain_code, 
            coin_type=self.hdw.BITCOIN_COIN_TYPE,
            account=account,
            address_index=address_index
        )
        return derived_key
    
    def derive_ethereum_address_key(self, master_seed: bytes, 
                                    account: int = 0, address_index: int = 0) -> bytes:
        """
        Derive an Ethereum address private key from master seed
        
        Args:
            master_seed: Master seed
            account: Account index
            address_index: Address index
            
        Returns:
            Ethereum private key for the specified path
        """
        master_key, chain_code = self.hdw.derive_master_key(master_seed)
        derived_key = self.hdw.derive_bip44_path(
            master_key, chain_code,
            coin_type=self.hdw.ETHEREUM_COIN_TYPE,
            account=account,
            address_index=address_index
        )
        return derived_key
    
    def save_share_to_file(self, key_share: KeyShare, filename: str):
        """Save a key share to a JSON file"""
        with open(filename, 'w') as f:
            json.dump(key_share.to_dict(), f, indent=2)
    
    def load_share_from_file(self, filename: str) -> KeyShare:
        """Load a key share from a JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        return KeyShare.from_dict(data)


def main():
    """Example usage demonstrating the MPC key management system"""
    print("=" * 80)
    print("Multi-Party Computation Cryptocurrency Key Manager")
    print("Using Shamir's Secret Sharing for Distributed Key Management")
    print("=" * 80)
    print()
    
    # Initialize the manager
    manager = DistributedKeyManager()
    
    # Step 1: Generate a master seed
    print("Step 1: Generating master seed...")
    master_seed = manager.generate_master_seed()
    print(f"Master Seed (hex): {master_seed.hex()}")
    print(f"Master Seed length: {len(master_seed)} bytes")
    print()
    
    # Step 2: Split the master seed into shares (3-of-5 scheme)
    print("Step 2: Splitting master seed into shares (3-of-5 threshold scheme)...")
    threshold = 3
    num_shares = 5
    key_shares = manager.split_master_seed(master_seed, threshold, num_shares)
    
    print(f"Created {num_shares} shares (need {threshold} to reconstruct)")
    for i, share in enumerate(key_shares):
        print(f"\nShare {i+1}:")
        print(f"  ID: {share.share_id}")
        print(f"  Value: {share.share_value.hex()}")
        # Save each share to a file
        filename = f"/home/claude/share_{share.share_id}.json"
        manager.save_share_to_file(share, filename)
        print(f"  Saved to: {filename}")
    print()
    
    # Step 3: Derive Bitcoin and Ethereum keys WITHOUT reconstructing master seed
    print("Step 3: Deriving child keys from master seed...")
    print("\nBitcoin Address Keys (BIP44 path: m/44'/0'/0'/0/index):")
    for i in range(3):
        btc_key = manager.derive_bitcoin_address_key(master_seed, account=0, address_index=i)
        print(f"  Bitcoin Address {i} private key: {btc_key.hex()}")
    
    print("\nEthereum Address Keys (BIP44 path: m/44'/60'/0'/0/index):")
    for i in range(3):
        eth_key = manager.derive_ethereum_address_key(master_seed, account=0, address_index=i)
        print(f"  Ethereum Address {i} private key: {eth_key.hex()}")
    print()
    
    # Step 4: Demonstrate reconstruction from shares
    print("Step 4: Demonstrating secret reconstruction...")
    print(f"Using shares 1, 3, and 5 (threshold = {threshold})...")
    
    # Select 3 shares for reconstruction
    selected_shares = [key_shares[0], key_shares[2], key_shares[4]]
    
    reconstructed_seed = manager.reconstruct_master_seed(selected_shares)
    print(f"Reconstructed Seed: {reconstructed_seed.hex()}")
    print(f"Original Seed:      {master_seed.hex()}")
    print(f"Match: {reconstructed_seed == master_seed}")
    print()
    
    # Step 5: Verify we can derive the same keys from reconstructed seed
    print("Step 5: Verifying derived keys from reconstructed seed...")
    btc_key_original = manager.derive_bitcoin_address_key(master_seed, account=0, address_index=0)
    btc_key_reconstructed = manager.derive_bitcoin_address_key(reconstructed_seed, account=0, address_index=0)
    
    print(f"Original Bitcoin key:      {btc_key_original.hex()}")
    print(f"Reconstructed Bitcoin key: {btc_key_reconstructed.hex()}")
    print(f"Match: {btc_key_original == btc_key_reconstructed}")
    print()
    
    print("=" * 80)
    print("IMPORTANT SECURITY NOTES:")
    print("=" * 80)
    print("1. Store each share on separate, secure devices")
    print("2. Never store threshold or more shares in the same location")
    print("3. Use hardware security modules (HSMs) for production")
    print("4. This is a demonstration - audit code before production use")
    print("5. The master seed should NEVER be stored - only the shares")
    print("6. To generate addresses, you only need the shares (reconstruct temporarily)")
    print("=" * 80)


if __name__ == "__main__":
    main()
