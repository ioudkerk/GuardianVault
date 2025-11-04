#!/usr/bin/env python3
"""
Enhanced Crypto MPC Key Manager with Address Generation
Requires: pip install ecdsa base58 eth-hash[pycryptodome]
"""

import hashlib
from typing import Tuple
from crypto_mpc_keymanager import DistributedKeyManager, KeyShare


class BitcoinAddress:
    """Bitcoin address generation from private keys"""
    
    @staticmethod
    def private_key_to_wif(private_key: bytes, compressed: bool = True, testnet: bool = False) -> str:
        """
        Convert private key to Wallet Import Format (WIF)
        
        Args:
            private_key: 32-byte private key
            compressed: Whether to use compressed format
            testnet: Whether this is for testnet
            
        Returns:
            WIF-encoded private key
        """
        # Version byte (0x80 for mainnet, 0xef for testnet)
        version = b'\xef' if testnet else b'\x80'
        
        # Add version byte
        extended = version + private_key
        
        # Add compression flag if compressed
        if compressed:
            extended += b'\x01'
        
        # Double SHA256 for checksum
        checksum = hashlib.sha256(hashlib.sha256(extended).digest()).digest()[:4]
        
        # Base58 encode
        return BitcoinAddress._base58_encode(extended + checksum)
    
    @staticmethod
    def _base58_encode(data: bytes) -> str:
        """Encode bytes to Base58"""
        alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        
        # Convert bytes to integer
        num = int.from_bytes(data, byteorder='big')
        
        # Convert to base58
        encoded = ''
        while num > 0:
            num, remainder = divmod(num, 58)
            encoded = alphabet[remainder] + encoded
        
        # Add '1' for each leading zero byte
        for byte in data:
            if byte == 0:
                encoded = '1' + encoded
            else:
                break
        
        return encoded
    
    @staticmethod
    def private_key_to_public_key(private_key: bytes, compressed: bool = True) -> bytes:
        """
        Derive public key from private key using secp256k1
        
        Args:
            private_key: 32-byte private key
            compressed: Whether to return compressed public key
            
        Returns:
            Public key (33 bytes if compressed, 65 bytes if uncompressed)
        """
        try:
            from ecdsa import SECP256k1, SigningKey
            
            sk = SigningKey.from_string(private_key, curve=SECP256k1)
            vk = sk.get_verifying_key()
            
            if compressed:
                # Compressed format: 0x02 or 0x03 + x coordinate
                point = vk.pubkey.point
                x_bytes = point.x().to_bytes(32, byteorder='big')
                prefix = b'\x02' if point.y() % 2 == 0 else b'\x03'
                return prefix + x_bytes
            else:
                # Uncompressed format: 0x04 + x + y coordinates
                return b'\x04' + vk.to_string()
                
        except ImportError:
            print("Warning: ecdsa library not installed. Install with: pip install ecdsa")
            # Return a placeholder for demonstration
            return b'\x02' + private_key  # This is NOT a real public key
    
    @staticmethod
    def public_key_to_address(public_key: bytes, testnet: bool = False) -> str:
        """
        Convert public key to Bitcoin address (P2PKH)
        
        Args:
            public_key: Public key bytes
            testnet: Whether this is for testnet
            
        Returns:
            Bitcoin address
        """
        # SHA256 then RIPEMD160
        sha256_hash = hashlib.sha256(public_key).digest()
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(sha256_hash)
        public_key_hash = ripemd160.digest()
        
        # Version byte (0x00 for mainnet, 0x6f for testnet)
        version = b'\x6f' if testnet else b'\x00'
        
        # Add version byte
        versioned_hash = version + public_key_hash
        
        # Double SHA256 for checksum
        checksum = hashlib.sha256(hashlib.sha256(versioned_hash).digest()).digest()[:4]
        
        # Base58 encode
        return BitcoinAddress._base58_encode(versioned_hash + checksum)
    
    @classmethod
    def generate_address(cls, private_key: bytes, compressed: bool = True, 
                        testnet: bool = False) -> Tuple[str, str]:
        """
        Generate Bitcoin address and WIF from private key
        
        Returns:
            (address, wif_private_key)
        """
        public_key = cls.private_key_to_public_key(private_key, compressed)
        address = cls.public_key_to_address(public_key, testnet)
        wif = cls.private_key_to_wif(private_key, compressed, testnet)
        return address, wif


class EthereumAddress:
    """Ethereum address generation from private keys"""
    
    @staticmethod
    def private_key_to_public_key(private_key: bytes) -> bytes:
        """
        Derive public key from private key using secp256k1
        
        Args:
            private_key: 32-byte private key
            
        Returns:
            Uncompressed public key (64 bytes, without 0x04 prefix)
        """
        try:
            from ecdsa import SECP256k1, SigningKey
            
            sk = SigningKey.from_string(private_key, curve=SECP256k1)
            vk = sk.get_verifying_key()
            # Return uncompressed public key without 0x04 prefix
            return vk.to_string()
            
        except ImportError:
            print("Warning: ecdsa library not installed. Install with: pip install ecdsa")
            # Return a placeholder
            return private_key + private_key  # NOT a real public key
    
    @staticmethod
    def public_key_to_address(public_key: bytes) -> str:
        """
        Convert public key to Ethereum address
        
        Args:
            public_key: 64-byte uncompressed public key (without 0x04 prefix)
            
        Returns:
            Ethereum address with 0x prefix
        """
        # Keccak256 hash of public key
        try:
            from eth_hash.auto import keccak
            address_bytes = keccak(public_key)[-20:]  # Take last 20 bytes
        except ImportError:
            print("Warning: eth-hash library not installed. Install with: pip install eth-hash[pycryptodome]")
            # Fallback to SHA3 (not exactly the same but similar for demo)
            import hashlib
            address_bytes = hashlib.sha3_256(public_key).digest()[-20:]
        
        # Add 0x prefix and convert to hex
        return '0x' + address_bytes.hex()
    
    @staticmethod
    def checksum_address(address: str) -> str:
        """
        Apply EIP-55 checksum encoding to address
        
        Args:
            address: Ethereum address (with or without 0x prefix)
            
        Returns:
            Checksummed address
        """
        # Remove 0x prefix if present
        address = address.lower().replace('0x', '')
        
        # Hash the address
        try:
            from eth_hash.auto import keccak
            hash_bytes = keccak(address.encode('utf-8'))
        except ImportError:
            import hashlib
            hash_bytes = hashlib.sha3_256(address.encode('utf-8')).digest()
        
        hash_hex = hash_bytes.hex()
        
        # Apply checksum
        checksummed = '0x'
        for i, char in enumerate(address):
            if char in '0123456789':
                checksummed += char
            else:
                # Uppercase if hash digit >= 8
                checksummed += char.upper() if int(hash_hex[i], 16) >= 8 else char
        
        return checksummed
    
    @classmethod
    def generate_address(cls, private_key: bytes) -> Tuple[str, str]:
        """
        Generate Ethereum address from private key
        
        Returns:
            (checksummed_address, hex_private_key)
        """
        public_key = cls.private_key_to_public_key(private_key)
        address = cls.public_key_to_address(public_key)
        checksummed_address = cls.checksum_address(address)
        hex_private_key = '0x' + private_key.hex()
        return checksummed_address, hex_private_key


class EnhancedDistributedKeyManager(DistributedKeyManager):
    """Enhanced manager with address generation capabilities"""
    
    def generate_bitcoin_address(self, master_seed: bytes, account: int = 0, 
                                 address_index: int = 0, compressed: bool = True,
                                 testnet: bool = False) -> dict:
        """
        Generate a Bitcoin address from master seed
        
        Returns:
            Dictionary with address, WIF, and derivation path
        """
        private_key = self.derive_bitcoin_address_key(master_seed, account, address_index)
        address, wif = BitcoinAddress.generate_address(private_key, compressed, testnet)
        
        return {
            'address': address,
            'wif': wif,
            'private_key_hex': private_key.hex(),
            'path': f"m/44'/0'/{account}'/0/{address_index}",
            'network': 'testnet' if testnet else 'mainnet'
        }
    
    def generate_ethereum_address(self, master_seed: bytes, account: int = 0,
                                  address_index: int = 0) -> dict:
        """
        Generate an Ethereum address from master seed
        
        Returns:
            Dictionary with address, private key, and derivation path
        """
        private_key = self.derive_ethereum_address_key(master_seed, account, address_index)
        address, hex_private_key = EthereumAddress.generate_address(private_key)
        
        return {
            'address': address,
            'private_key': hex_private_key,
            'path': f"m/44'/60'/{account}'/0/{address_index}"
        }
    
    def generate_addresses_from_shares(self, key_shares: list, coin_type: str,
                                      account: int = 0, num_addresses: int = 5) -> list:
        """
        Generate multiple addresses from shares without storing master seed
        
        Args:
            key_shares: List of KeyShare objects (must meet threshold)
            coin_type: 'bitcoin' or 'ethereum'
            account: Account index
            num_addresses: Number of addresses to generate
            
        Returns:
            List of address dictionaries
        """
        # Temporarily reconstruct master seed
        master_seed = self.reconstruct_master_seed(key_shares)
        
        addresses = []
        for i in range(num_addresses):
            if coin_type.lower() == 'bitcoin':
                addr_info = self.generate_bitcoin_address(master_seed, account, i)
            elif coin_type.lower() == 'ethereum':
                addr_info = self.generate_ethereum_address(master_seed, account, i)
            else:
                raise ValueError(f"Unsupported coin type: {coin_type}")
            
            addresses.append(addr_info)
        
        # Clear master seed from memory (Python doesn't guarantee this, but it's good practice)
        del master_seed
        
        return addresses


def main():
    """Enhanced example with actual address generation"""
    print("=" * 80)
    print("Enhanced MPC Cryptocurrency Key Manager")
    print("With Bitcoin and Ethereum Address Generation")
    print("=" * 80)
    print()
    
    # Initialize enhanced manager
    manager = EnhancedDistributedKeyManager()
    
    # Generate and split master seed
    print("Generating master seed and splitting into 3-of-5 shares...")
    master_seed = manager.generate_master_seed()
    key_shares = manager.split_master_seed(master_seed, threshold=3, num_shares=5)
    print(f"✓ Created 5 shares (need any 3 to reconstruct)")
    print()
    
    # Generate Bitcoin addresses
    print("=" * 80)
    print("BITCOIN ADDRESSES (Mainnet, Compressed)")
    print("=" * 80)
    for i in range(3):
        btc_info = manager.generate_bitcoin_address(master_seed, account=0, 
                                                    address_index=i, compressed=True)
        print(f"\nAddress {i}:")
        print(f"  Path: {btc_info['path']}")
        print(f"  Address: {btc_info['address']}")
        print(f"  WIF: {btc_info['wif']}")
        print(f"  Private Key: {btc_info['private_key_hex']}")
    print()
    
    # Generate Ethereum addresses
    print("=" * 80)
    print("ETHEREUM ADDRESSES")
    print("=" * 80)
    for i in range(3):
        eth_info = manager.generate_ethereum_address(master_seed, account=0, address_index=i)
        print(f"\nAddress {i}:")
        print(f"  Path: {eth_info['path']}")
        print(f"  Address: {eth_info['address']}")
        print(f"  Private Key: {eth_info['private_key']}")
    print()
    
    # Demonstrate address generation from shares only
    print("=" * 80)
    print("GENERATING ADDRESSES FROM SHARES (MPC Workflow)")
    print("=" * 80)
    print("Using shares 1, 2, and 3 to generate addresses...")
    print()
    
    selected_shares = [key_shares[0], key_shares[1], key_shares[2]]
    
    print("Bitcoin addresses generated from shares:")
    btc_addresses = manager.generate_addresses_from_shares(
        selected_shares, 'bitcoin', account=0, num_addresses=2
    )
    for addr_info in btc_addresses:
        print(f"  • {addr_info['address']} (path: {addr_info['path']})")
    
    print("\nEthereum addresses generated from shares:")
    eth_addresses = manager.generate_addresses_from_shares(
        selected_shares, 'ethereum', account=0, num_addresses=2
    )
    for addr_info in eth_addresses:
        print(f"  • {addr_info['address']} (path: {addr_info['path']})")
    print()
    
    # Security demonstration
    print("=" * 80)
    print("SECURITY DEMONSTRATION")
    print("=" * 80)
    print("Attempting reconstruction with only 2 shares (below threshold)...")
    try:
        insufficient_shares = [key_shares[0], key_shares[1]]
        reconstructed = manager.reconstruct_master_seed(insufficient_shares)
        # If we get here, verify it's wrong
        if reconstructed != master_seed:
            print("✓ Reconstruction failed - produced incorrect seed (as expected)")
        else:
            print("✗ Unexpected: reconstruction succeeded with insufficient shares")
    except Exception as e:
        print(f"✓ Reconstruction properly requires threshold shares: {e}")
    print()
    
    print("=" * 80)
    print("RECOMMENDED WORKFLOW FOR PRODUCTION USE")
    print("=" * 80)
    print("""
1. SETUP PHASE:
   - Generate master seed on secure, air-gapped device
   - Split into N shares with K-of-N threshold
   - Distribute shares to different secure locations/parties
   - DESTROY the original master seed
   - Never store threshold+ shares together

2. ADDRESS GENERATION:
   - Gather K shares from distributed parties
   - Temporarily reconstruct master seed in secure environment
   - Derive required addresses using BIP44 paths
   - Immediately clear master seed from memory
   - Return to distributed state

3. TRANSACTION SIGNING:
   - Similar to address generation
   - Reconstruct temporarily, sign transaction, clear seed
   - Or use threshold signature schemes (more advanced)

4. SHARE STORAGE:
   - Store each share in separate HSMs or secure enclaves
   - Use encrypted backups with strong passphrases
   - Implement access controls and audit logs
   - Consider geographic distribution

5. OPERATIONAL SECURITY:
   - Regularly audit share locations
   - Test recovery procedures
   - Rotate shares periodically if needed
   - Monitor for unauthorized access attempts
    """)
    print("=" * 80)
    
    # Save shares to files
    print("\nSaving shares to files for safekeeping...")
    for share in key_shares:
        filename = f"/home/claude/enhanced_share_{share.share_id}.json"
        manager.save_share_to_file(share, filename)
        print(f"  ✓ Saved share {share.share_id} to {filename}")
    print()
    
    print("Installation note:")
    print("For full functionality, install dependencies:")
    print("  pip install ecdsa base58 eth-hash[pycryptodome]")


if __name__ == "__main__":
    main()
