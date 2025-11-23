"""
Ethereum Transaction Builder with EIP-1559 Support

This module provides functionality to create, sign, and serialize Ethereum transactions.
It supports EIP-1559 (Type 2) transactions with maxFeePerGas and maxPriorityFeePerGas.
"""

from typing import Optional
from eth_hash.auto import keccak
from guardianvault.rlp_encoding import encode, encode_int, encode_address


class EthereumTransaction:
    """
    Represents an Ethereum EIP-1559 (Type 2) transaction.

    EIP-1559 transactions include:
    - chainId: Network identifier
    - nonce: Account transaction counter
    - maxPriorityFeePerGas: Tip to miner
    - maxFeePerGas: Maximum total fee per gas
    - gasLimit: Maximum gas units
    - to: Recipient address
    - value: Amount in Wei
    - data: Contract call data (or empty for simple transfers)
    - accessList: Optional list of addresses/storage keys
    - signature: v, r, s values
    """

    def __init__(
        self,
        chain_id: int,
        nonce: int,
        max_priority_fee_per_gas: int,
        max_fee_per_gas: int,
        gas_limit: int,
        to: str,
        value: int,
        data: bytes = b'',
        access_list: list = None
    ):
        """
        Initialize an EIP-1559 transaction.

        Args:
            chain_id: Network ID (1=mainnet, 11155111=sepolia, 1337=local ganache)
            nonce: Transaction count for the sender account
            max_priority_fee_per_gas: Tip to miner in Wei
            max_fee_per_gas: Maximum total fee per gas in Wei
            gas_limit: Maximum gas units
            to: Recipient address (hex string with or without 0x)
            value: Amount to send in Wei
            data: Contract call data (empty for simple ETH transfers)
            access_list: EIP-2930 access list (optional, defaults to empty)
        """
        self.chain_id = chain_id
        self.nonce = nonce
        self.max_priority_fee_per_gas = max_priority_fee_per_gas
        self.max_fee_per_gas = max_fee_per_gas
        self.gas_limit = gas_limit
        self.to = to.lower() if to.startswith('0x') else f"0x{to.lower()}"
        self.value = value
        self.data = data if isinstance(data, bytes) else bytes.fromhex(data.replace('0x', ''))
        self.access_list = access_list if access_list else []

        # Signature components (set after signing)
        self.v: Optional[int] = None
        self.r: Optional[int] = None
        self.s: Optional[int] = None

    def get_signing_hash(self) -> bytes:
        """
        Compute the message hash that needs to be signed.

        For EIP-1559 transactions, this is:
        keccak256(0x02 || rlp([chainId, nonce, maxPriorityFeePerGas, maxFeePerGas,
                                gasLimit, to, value, data, accessList]))

        Returns:
            32-byte hash to be signed
        """
        # Encode transaction fields as RLP list
        rlp_list = [
            encode_int(self.chain_id),
            encode_int(self.nonce),
            encode_int(self.max_priority_fee_per_gas),
            encode_int(self.max_fee_per_gas),
            encode_int(self.gas_limit),
            encode_address(self.to),
            encode_int(self.value),
            self.data,
            self._encode_access_list()
        ]

        # RLP encode the list
        rlp_encoded = encode(rlp_list)

        # Prepend transaction type byte (0x02 for EIP-1559)
        typed_data = b'\x02' + rlp_encoded

        # Return keccak256 hash
        return keccak(typed_data)

    def set_signature(self, v: int, r: int, s: int):
        """
        Set the signature components after signing.

        Args:
            v: Recovery ID (0 or 1 for EIP-1559)
            r: Signature r value
            s: Signature s value
        """
        self.v = v
        self.r = r
        self.s = s

    def serialize(self) -> bytes:
        """
        Serialize the signed transaction for broadcasting.

        For EIP-1559, this is:
        0x02 || rlp([chainId, nonce, maxPriorityFeePerGas, maxFeePerGas,
                     gasLimit, to, value, data, accessList, v, r, s])

        Returns:
            Serialized transaction bytes

        Raises:
            ValueError: If transaction is not signed
        """
        if self.v is None or self.r is None or self.s is None:
            raise ValueError("Transaction must be signed before serialization")

        # Encode all fields including signature
        rlp_list = [
            encode_int(self.chain_id),
            encode_int(self.nonce),
            encode_int(self.max_priority_fee_per_gas),
            encode_int(self.max_fee_per_gas),
            encode_int(self.gas_limit),
            encode_address(self.to),
            encode_int(self.value),
            self.data,
            self._encode_access_list(),
            encode_int(self.v),
            encode_int(self.r),
            encode_int(self.s)
        ]

        # RLP encode
        rlp_encoded = encode(rlp_list)

        # Prepend transaction type byte
        return b'\x02' + rlp_encoded

    def _encode_access_list(self) -> list:
        """
        Encode the access list for RLP.

        Access list format: [[address, [storageKey1, storageKey2, ...]], ...]

        Returns:
            RLP-encodable access list
        """
        if not self.access_list:
            return []

        encoded = []
        for entry in self.access_list:
            address = encode_address(entry['address'])
            storage_keys = [bytes.fromhex(key.replace('0x', '')) for key in entry.get('storageKeys', [])]
            encoded.append([address, storage_keys])

        return encoded

    def to_dict(self) -> dict:
        """
        Convert transaction to dictionary format.

        Returns:
            Transaction data as dictionary
        """
        return {
            'chainId': self.chain_id,
            'nonce': self.nonce,
            'maxPriorityFeePerGas': self.max_priority_fee_per_gas,
            'maxFeePerGas': self.max_fee_per_gas,
            'gasLimit': self.gas_limit,
            'to': self.to,
            'value': self.value,
            'data': f"0x{self.data.hex()}" if self.data else '0x',
            'accessList': self.access_list,
            'v': self.v,
            'r': self.r,
            's': self.s
        }


class LegacyEthereumTransaction:
    """
    Represents a legacy (Type 0) Ethereum transaction.
    Compatible with older tools like Ganache CLI v6 that don't support EIP-1559.
    """

    def __init__(
        self,
        chain_id: int,
        nonce: int,
        gas_price: int,
        gas_limit: int,
        to: str,
        value: int,
        data: bytes = b''
    ):
        """
        Initialize a legacy transaction.

        Args:
            chain_id: Network ID
            nonce: Transaction count for the sender account
            gas_price: Gas price in Wei
            gas_limit: Maximum gas units
            to: Recipient address (hex string with or without 0x)
            value: Amount to send in Wei
            data: Contract call data (empty for simple ETH transfers)
        """
        self.chain_id = chain_id
        self.nonce = nonce
        self.gas_price = gas_price
        self.gas_limit = gas_limit
        self.to = to.lower() if to.startswith('0x') else f"0x{to.lower()}"
        self.value = value
        self.data = data if isinstance(data, bytes) else bytes.fromhex(data.replace('0x', ''))

        # Signature components (set after signing)
        self.v: Optional[int] = None
        self.r: Optional[int] = None
        self.s: Optional[int] = None

    def get_signing_hash(self) -> bytes:
        """
        Compute the message hash for legacy transactions.

        Uses EIP-155 replay protection: keccak256(RLP(nonce, gasPrice, gasLimit, to, value, data, chainId, 0, 0))

        Returns:
            32-byte hash to be signed
        """
        # EIP-155: append chain_id, 0, 0 for replay protection
        rlp_list = [
            encode_int(self.nonce),
            encode_int(self.gas_price),
            encode_int(self.gas_limit),
            encode_address(self.to),
            encode_int(self.value),
            self.data,
            encode_int(self.chain_id),
            b'',  # 0
            b''   # 0
        ]

        rlp_encoded = encode(rlp_list)
        return keccak(rlp_encoded)

    def set_signature(self, v: int, r: int, s: int):
        """
        Set the signature components after signing.

        For legacy transactions with EIP-155, v = chain_id * 2 + 35 + recovery_id

        Args:
            v: Recovery ID (0 or 1, will be converted to EIP-155 format)
            r: Signature r value
            s: Signature s value
        """
        # Convert v from recovery ID (0/1) to EIP-155 format
        self.v = self.chain_id * 2 + 35 + v
        self.r = r
        self.s = s

    def serialize(self) -> bytes:
        """
        Serialize the signed transaction for broadcasting.

        Returns:
            RLP-encoded transaction bytes

        Raises:
            ValueError: If transaction is not signed
        """
        if self.v is None or self.r is None or self.s is None:
            raise ValueError("Transaction must be signed before serialization")

        rlp_list = [
            encode_int(self.nonce),
            encode_int(self.gas_price),
            encode_int(self.gas_limit),
            encode_address(self.to),
            encode_int(self.value),
            self.data,
            encode_int(self.v),
            encode_int(self.r),
            encode_int(self.s)
        ]

        return encode(rlp_list)

    def to_dict(self) -> dict:
        """
        Convert transaction to dictionary format.

        Returns:
            Transaction data as dictionary
        """
        return {
            'chainId': self.chain_id,
            'nonce': self.nonce,
            'gasPrice': self.gas_price,
            'gasLimit': self.gas_limit,
            'to': self.to,
            'value': self.value,
            'data': f"0x{self.data.hex()}" if self.data else '0x',
            'v': self.v,
            'r': self.r,
            's': self.s
        }


class EthereumTransactionBuilder:
    """
    High-level builder for creating Ethereum transactions.
    """

    @staticmethod
    def build_transfer_transaction(
        sender_address: str,
        recipient_address: str,
        amount_eth: float,
        nonce: int,
        chain_id: int,
        max_priority_fee_gwei: float = 2.0,
        max_fee_gwei: float = 100.0,
        gas_limit: int = 21000,
        legacy: bool = False
    ):
        """
        Build a simple ETH transfer transaction.

        Args:
            sender_address: Sender's Ethereum address
            recipient_address: Recipient's Ethereum address
            amount_eth: Amount to send in ETH
            nonce: Current nonce for sender account
            chain_id: Network chain ID
            max_priority_fee_gwei: Priority fee (tip) in Gwei (default: 2)
            max_fee_gwei: Maximum total fee in Gwei (default: 100)
            gas_limit: Gas limit (default: 21000 for simple transfers)
            legacy: If True, create legacy (Type 0) transaction instead of EIP-1559

        Returns:
            EthereumTransaction or LegacyEthereumTransaction ready to be signed
        """
        # Convert ETH to Wei (1 ETH = 10^18 Wei)
        value_wei = int(amount_eth * 10**18)

        if legacy:
            # Legacy transaction: use gas_price instead of EIP-1559 fees
            # Use max_fee as gas_price for legacy
            gas_price_wei = int(max_fee_gwei * 10**9)

            return LegacyEthereumTransaction(
                chain_id=chain_id,
                nonce=nonce,
                gas_price=gas_price_wei,
                gas_limit=gas_limit,
                to=recipient_address,
                value=value_wei,
                data=b''
            )
        else:
            # EIP-1559 transaction
            # Convert Gwei to Wei (1 Gwei = 10^9 Wei)
            max_priority_fee_wei = int(max_priority_fee_gwei * 10**9)
            max_fee_wei = int(max_fee_gwei * 10**9)

            return EthereumTransaction(
                chain_id=chain_id,
                nonce=nonce,
                max_priority_fee_per_gas=max_priority_fee_wei,
                max_fee_per_gas=max_fee_wei,
                gas_limit=gas_limit,
                to=recipient_address,
                value=value_wei,
                data=b''
            )

    @staticmethod
    def build_contract_transaction(
        sender_address: str,
        contract_address: str,
        nonce: int,
        chain_id: int,
        data: bytes,
        value_wei: int = 0,
        max_priority_fee_gwei: float = 2.0,
        max_fee_gwei: float = 100.0,
        gas_limit: int = 100000
    ) -> EthereumTransaction:
        """
        Build a contract interaction transaction.

        Args:
            sender_address: Sender's Ethereum address
            contract_address: Smart contract address
            nonce: Current nonce for sender account
            chain_id: Network chain ID
            data: Encoded contract call data
            value_wei: Amount of Wei to send with transaction (default: 0)
            max_priority_fee_gwei: Priority fee in Gwei
            max_fee_gwei: Maximum total fee in Gwei
            gas_limit: Gas limit (higher for contract calls)

        Returns:
            EthereumTransaction ready to be signed
        """
        # Convert Gwei to Wei
        max_priority_fee_wei = int(max_priority_fee_gwei * 10**9)
        max_fee_wei = int(max_fee_gwei * 10**9)

        return EthereumTransaction(
            chain_id=chain_id,
            nonce=nonce,
            max_priority_fee_per_gas=max_priority_fee_wei,
            max_fee_per_gas=max_fee_wei,
            gas_limit=gas_limit,
            to=contract_address,
            value=value_wei,
            data=data
        )


def recover_v_from_signature(r: int, s: int, message_hash: bytes, public_key: bytes, chain_id: int) -> int:
    """
    Recover the v parameter (recovery ID) for an Ethereum signature.

    Args:
        r: Signature r value
        s: Signature s value
        message_hash: The message hash that was signed
        public_key: The public key that signed the message (65 bytes uncompressed)
        chain_id: Network chain ID

    Returns:
        Recovery ID (0 or 1)
    """
    from ecdsa import SECP256k1, VerifyingKey
    from ecdsa.util import sigdecode_string

    # Try both recovery IDs (0 and 1)
    for v in [0, 1]:
        try:
            # Create signature bytes (r || s)
            sig_bytes = r.to_bytes(32, 'big') + s.to_bytes(32, 'big')

            # Try to recover public key
            recovered_key = VerifyingKey.from_public_key_recovery(
                sig_bytes,
                message_hash,
                SECP256k1,
                hashfunc=None
            )[v]

            # Check if recovered key matches our public key
            recovered_bytes = b'\x04' + recovered_key.to_string()
            if recovered_bytes == public_key:
                return v

        except Exception:
            continue

    raise ValueError("Could not recover v parameter from signature")


if __name__ == "__main__":
    print("Testing Ethereum Transaction Builder...")

    # Test 1: Create a simple transfer transaction
    tx = EthereumTransactionBuilder.build_transfer_transaction(
        sender_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        recipient_address="0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
        amount_eth=0.1,
        nonce=0,
        chain_id=1337,  # Local network
        max_priority_fee_gwei=2.0,
        max_fee_gwei=100.0
    )
    print("✓ Created transfer transaction")

    # Test 2: Compute signing hash
    signing_hash = tx.get_signing_hash()
    assert len(signing_hash) == 32
    print(f"✓ Computed signing hash: 0x{signing_hash.hex()}")

    # Test 3: Sign and serialize (mock signature)
    tx.set_signature(v=0, r=12345, s=67890)
    serialized = tx.serialize()
    assert serialized[0] == 0x02  # EIP-1559 type
    print(f"✓ Serialized transaction: {len(serialized)} bytes")

    # Test 4: Convert to dict
    tx_dict = tx.to_dict()
    assert tx_dict['chainId'] == 1337
    assert tx_dict['value'] == int(0.1 * 10**18)
    print("✓ Converted to dictionary")

    # Test 5: Contract transaction
    contract_tx = EthereumTransactionBuilder.build_contract_transaction(
        sender_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        contract_address="0x1234567890123456789012345678901234567890",
        nonce=1,
        chain_id=1337,
        data=bytes.fromhex("a9059cbb"),  # Example: ERC20 transfer function selector
        gas_limit=100000
    )
    print("✓ Created contract transaction")

    print("\nAll Ethereum transaction tests passed! ✓")
