#!/usr/bin/env python3
"""
Bitcoin and Ethereum address generation from public keys
Works with threshold_mpc_keymanager.py for TRUE MPC (no private key reconstruction)
"""

import hashlib
from typing import List
from .threshold_mpc_keymanager import (
    ExtendedPublicKey,
    PublicKeyDerivation,
    EllipticCurvePoint
)


class BitcoinAddressGenerator:
    """Generate Bitcoin addresses from public keys (no private key needed!)"""

    @staticmethod
    def pubkey_to_address(public_key: bytes, network: str = "mainnet", address_type: str = "p2pkh") -> str:
        """
        Convert public key to Bitcoin address

        Args:
            public_key: 33-byte compressed public key
            network: Network type - "mainnet", "testnet", or "regtest" (default: "mainnet")
            address_type: Address type - "p2pkh" (legacy), "p2wpkh" (segwit), or "p2tr" (taproot)
                         (default: "p2pkh")

        Returns:
            Bitcoin address string:
            - P2PKH: "1..." (mainnet), "m/n..." (testnet/regtest)
            - P2WPKH: "bc1q..." (mainnet), "tb1q..." (testnet), "bcrt1q..." (regtest)
            - P2TR: "bc1p..." (mainnet), "tb1p..." (testnet), "bcrt1p..." (regtest)

        Note:
            - P2PKH: Legacy addresses (base58)
            - P2WPKH: SegWit v0 addresses (bech32)
            - P2TR: Taproot addresses (bech32m)
        """
        # Validate parameters
        if network not in ["mainnet", "testnet", "regtest"]:
            raise ValueError(f"Invalid network '{network}'. Must be 'mainnet', 'testnet', or 'regtest'")

        if address_type not in ["p2pkh", "p2wpkh", "p2tr"]:
            raise ValueError(f"Invalid address_type '{address_type}'. Must be 'p2pkh', 'p2wpkh', or 'p2tr'")

        if address_type == "p2pkh":
            return BitcoinAddressGenerator._pubkey_to_p2pkh(public_key, network)
        elif address_type == "p2wpkh":
            return BitcoinAddressGenerator._pubkey_to_p2wpkh(public_key, network)
        elif address_type == "p2tr":
            return BitcoinAddressGenerator._pubkey_to_p2tr(public_key, network)

    @staticmethod
    def _pubkey_to_p2pkh(public_key: bytes, network: str) -> str:
        """Convert public key to P2PKH address (legacy)"""
        # Hash the public key: SHA256 then RIPEMD160
        sha256_hash = hashlib.sha256(public_key).digest()

        # RIPEMD160
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(sha256_hash)
        pubkey_hash = ripemd160.digest()

        # Add version byte (0x00 for mainnet, 0x6f for testnet/regtest)
        version = b'\x6f' if network in ["testnet", "regtest"] else b'\x00'
        versioned_hash = version + pubkey_hash

        # Calculate checksum (first 4 bytes of double SHA256)
        checksum = hashlib.sha256(hashlib.sha256(versioned_hash).digest()).digest()[:4]

        # Concatenate and encode to Base58
        address_bytes = versioned_hash + checksum
        return BitcoinAddressGenerator._base58_encode(address_bytes)

    @staticmethod
    def _pubkey_to_p2wpkh(public_key: bytes, network: str) -> str:
        """Convert public key to P2WPKH address (SegWit v0)"""
        from .bitcoin_transaction import Bech32

        # Hash the public key: SHA256 then RIPEMD160
        sha256_hash = hashlib.sha256(public_key).digest()
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(sha256_hash)
        pubkey_hash = ripemd160.digest()

        # Determine HRP based on network
        if network == "mainnet":
            hrp = "bc"
        elif network == "testnet":
            hrp = "tb"
        elif network == "regtest":
            hrp = "bcrt"

        # Encode as bech32 (witness version 0)
        return Bech32.encode_segwit_address(hrp, 0, pubkey_hash)

    @staticmethod
    def _pubkey_to_p2tr(public_key: bytes, network: str) -> str:
        """Convert public key to P2TR address (Taproot - SegWit v1)"""
        from .bitcoin_transaction import Bech32

        # For Taproot, we use the x-only public key (32 bytes)
        # Extract x-coordinate from compressed public key (remove parity byte)
        if len(public_key) != 33:
            raise ValueError("Public key must be 33 bytes (compressed)")

        # The x-coordinate is bytes 1-33 (skip the parity byte)
        x_only_pubkey = public_key[1:]

        # Determine HRP based on network
        if network == "mainnet":
            hrp = "bc"
        elif network == "testnet":
            hrp = "tb"
        elif network == "regtest":
            hrp = "bcrt"

        # Encode as bech32m (witness version 1)
        return Bech32.encode_segwit_address(hrp, 1, x_only_pubkey)

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
    def generate_addresses_from_xpub(
        xpub: ExtendedPublicKey,
        change: int = 0,
        start_index: int = 0,
        count: int = 10,
        network: str = "mainnet",
        address_type: str = "p2pkh"
    ) -> List[dict]:
        """
        Generate multiple Bitcoin addresses from xpub

        Args:
            xpub: Extended public key (from threshold computation)
            change: 0 for receiving, 1 for change
            start_index: Starting address index
            count: Number of addresses to generate
            network: Network type - "mainnet", "testnet", or "regtest" (default: "mainnet")
            address_type: Address type - "p2pkh", "p2wpkh", or "p2tr" (default: "p2pkh")

        Returns:
            List of dicts with path, public_key, address, and address_type
        """
        addresses = []

        for i in range(start_index, start_index + count):
            # Derive change key
            change_pubkey, change_chain = PublicKeyDerivation.derive_public_child(xpub, change)
            change_xpub = ExtendedPublicKey(
                public_key=change_pubkey,
                chain_code=change_chain,
                depth=xpub.depth + 1,
                parent_fingerprint=b'\x00\x00\x00\x00',
                child_number=change
            )

            # Derive address key
            address_pubkey, _ = PublicKeyDerivation.derive_public_child(change_xpub, i)

            # Generate address with specified type
            address = BitcoinAddressGenerator.pubkey_to_address(address_pubkey, network, address_type)

            addresses.append({
                'path': f"m/44'/0'/0'/{change}/{i}",
                'public_key': address_pubkey.hex(),
                'address': address,
                'address_type': address_type
            })

        return addresses


class EthereumAddressGenerator:
    """Generate Ethereum addresses from public keys (no private key needed!)"""

    @staticmethod
    def pubkey_to_address(public_key: bytes) -> str:
        """
        Convert public key to Ethereum address with EIP-55 checksum

        Args:
            public_key: 33-byte compressed public key

        Returns:
            Ethereum address string (e.g., "0x742d35...")
        """
        # Decompress public key to get full (x, y) coordinates
        point = EllipticCurvePoint.from_bytes(public_key)

        # Ethereum uses uncompressed public key (without 0x04 prefix)
        # We need the 64 bytes (32 bytes x + 32 bytes y)
        x_bytes = point.x.to_bytes(32, 'big')
        y_bytes = point.y.to_bytes(32, 'big')
        uncompressed = x_bytes + y_bytes

        # Keccak256 hash
        try:
            from eth_hash.auto import keccak
            hash_result = keccak(uncompressed)
        except ImportError:
            # Fallback to simple hash for demonstration
            print("Warning: eth-hash not installed. Using SHA3-256 as fallback.")
            hash_result = hashlib.sha3_256(uncompressed).digest()

        # Take last 20 bytes
        address_bytes = hash_result[-20:]

        # Convert to hex with 0x prefix
        address_hex = '0x' + address_bytes.hex()

        # Apply EIP-55 checksum
        address_checksum = EthereumAddressGenerator._apply_eip55_checksum(address_hex)

        return address_checksum

    @staticmethod
    def _apply_eip55_checksum(address: str) -> str:
        """
        Apply EIP-55 checksum encoding to Ethereum address

        Args:
            address: Address with 0x prefix (lowercase)

        Returns:
            Checksummed address
        """
        # Remove 0x prefix for hashing
        address_lower = address[2:].lower()

        # Hash the lowercase address
        try:
            from eth_hash.auto import keccak
            hash_result = keccak(address_lower.encode('utf-8'))
        except ImportError:
            hash_result = hashlib.sha3_256(address_lower.encode('utf-8')).digest()

        hash_hex = hash_result.hex()

        # Apply checksum
        checksummed = '0x'
        for i, char in enumerate(address_lower):
            if char in '0123456789':
                checksummed += char
            else:
                # If hash bit is 1, uppercase; otherwise lowercase
                if int(hash_hex[i], 16) >= 8:
                    checksummed += char.upper()
                else:
                    checksummed += char

        return checksummed

    @staticmethod
    def generate_addresses_from_xpub(
        xpub: ExtendedPublicKey,
        change: int = 0,
        start_index: int = 0,
        count: int = 10
    ) -> List[dict]:
        """
        Generate multiple Ethereum addresses from xpub

        Args:
            xpub: Extended public key (from threshold computation)
            change: 0 for receiving, 1 for change
            start_index: Starting address index
            count: Number of addresses to generate

        Returns:
            List of dicts with path, public_key, and address
        """
        addresses = []

        for i in range(start_index, start_index + count):
            # Derive change key
            change_pubkey, change_chain = PublicKeyDerivation.derive_public_child(xpub, change)
            change_xpub = ExtendedPublicKey(
                public_key=change_pubkey,
                chain_code=change_chain,
                depth=xpub.depth + 1,
                parent_fingerprint=b'\x00\x00\x00\x00',
                child_number=change
            )

            # Derive address key
            address_pubkey, _ = PublicKeyDerivation.derive_public_child(change_xpub, i)

            # Generate address
            address = EthereumAddressGenerator.pubkey_to_address(address_pubkey)

            addresses.append({
                'path': f"m/44'/60'/0'/{change}/{i}",
                'public_key': address_pubkey.hex(),
                'address': address
            })

        return addresses


if __name__ == "__main__":
    import secrets
    from .threshold_mpc_keymanager import (
        ThresholdKeyGeneration,
        ThresholdBIP32
    )

    print("=" * 80)
    print("THRESHOLD ADDRESS GENERATION DEMO")
    print("Unlimited addresses WITHOUT reconstructing private key!")
    print("=" * 80)
    print()

    # Setup (threshold computation required once)
    num_parties = 3
    key_shares, _ = ThresholdKeyGeneration.generate_shares(num_parties)

    seed = secrets.token_bytes(32)
    master_shares, master_pubkey, master_chain = \
        ThresholdBIP32.derive_master_keys_threshold(key_shares, seed)

    print("ONE-TIME SETUP: Deriving account xpubs (threshold computation)")
    print("-" * 80)

    # Bitcoin account xpub
    btc_xpub = ThresholdBIP32.derive_account_xpub_threshold(
        master_shares, master_chain, coin_type=0, account=0
    )
    print(f"✓ Bitcoin xpub: {btc_xpub.public_key.hex()[:32]}...")

    # Ethereum account xpub
    eth_xpub = ThresholdBIP32.derive_account_xpub_threshold(
        master_shares, master_chain, coin_type=60, account=0
    )
    print(f"✓ Ethereum xpub: {eth_xpub.public_key.hex()[:32]}...")
    print()

    # Generate unlimited Bitcoin addresses (no threshold!)
    print("BITCOIN ADDRESSES (No threshold computation!)")
    print("-" * 80)
    btc_addresses = BitcoinAddressGenerator.generate_addresses_from_xpub(
        btc_xpub, change=0, start_index=0, count=5
    )

    for addr in btc_addresses:
        print(f"  {addr['path']}")
        print(f"    Address: {addr['address']}")
        print()

    # Generate unlimited Ethereum addresses (no threshold!)
    print("ETHEREUM ADDRESSES (No threshold computation!)")
    print("-" * 80)
    eth_addresses = EthereumAddressGenerator.generate_addresses_from_xpub(
        eth_xpub, change=0, start_index=0, count=5
    )

    for addr in eth_addresses:
        print(f"  {addr['path']}")
        print(f"    Address: {addr['address']}")
        print()

    print("=" * 80)
    print("SUCCESS!")
    print("✓ Generated Bitcoin and Ethereum addresses")
    print("✓ No private key reconstruction needed")
    print("✓ Can generate unlimited addresses from xpub")
    print("=" * 80)
