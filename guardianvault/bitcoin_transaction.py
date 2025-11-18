#!/usr/bin/env python3
"""
Bitcoin Transaction Builder
Constructs and signs Bitcoin transactions compatible with MPC threshold signing
"""

import hashlib
import struct
from typing import List, Tuple
from dataclasses import dataclass


class Bech32:
    """Bech32/Bech32m encoding/decoding for SegWit addresses"""

    CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
    GENERATOR = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    BECH32_CONST = 1
    BECH32M_CONST = 0x2bc830a3

    @classmethod
    def bech32_polymod(cls, values):
        """Compute Bech32 checksum"""
        gen = cls.GENERATOR
        chk = 1
        for value in values:
            b = chk >> 25
            chk = (chk & 0x1ffffff) << 5 ^ value
            for i in range(5):
                chk ^= gen[i] if ((b >> i) & 1) else 0
        return chk

    @classmethod
    def bech32_hrp_expand(cls, hrp):
        """Expand human-readable part for checksum"""
        return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]

    @classmethod
    def bech32_verify_checksum(cls, hrp, data, const):
        """Verify Bech32/Bech32m checksum"""
        return cls.bech32_polymod(cls.bech32_hrp_expand(hrp) + data) == const

    @classmethod
    def bech32_create_checksum(cls, hrp, data, const):
        """Create Bech32/Bech32m checksum"""
        values = cls.bech32_hrp_expand(hrp) + data
        polymod = cls.bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ const
        return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]

    @classmethod
    def bech32_encode(cls, hrp, data, const):
        """Encode Bech32/Bech32m string"""
        combined = data + cls.bech32_create_checksum(hrp, data, const)
        return hrp + '1' + ''.join([cls.CHARSET[d] for d in combined])

    @classmethod
    def bech32_decode(cls, bech):
        """Decode a Bech32/Bech32m string - returns (hrp, data, encoding)"""
        if ((any(ord(x) < 33 or ord(x) > 126 for x in bech)) or
                (bech.lower() != bech and bech.upper() != bech)):
            return (None, None, None)
        bech = bech.lower()
        pos = bech.rfind('1')
        if pos < 1 or pos + 7 > len(bech) or len(bech) > 90:
            return (None, None, None)
        if not all(x in cls.CHARSET for x in bech[pos+1:]):
            return (None, None, None)
        hrp = bech[:pos]
        data = [cls.CHARSET.find(x) for x in bech[pos+1:]]

        # Try Bech32 first, then Bech32m
        encoding = None
        if cls.bech32_verify_checksum(hrp, data, cls.BECH32_CONST):
            encoding = 'bech32'
        elif cls.bech32_verify_checksum(hrp, data, cls.BECH32M_CONST):
            encoding = 'bech32m'
        else:
            return (None, None, None)

        return (hrp, data[:-6], encoding)

    @classmethod
    def convertbits(cls, data, frombits, tobits, pad=True):
        """Convert between bit groups"""
        acc = 0
        bits = 0
        ret = []
        maxv = (1 << tobits) - 1
        max_acc = (1 << (frombits + tobits - 1)) - 1
        for value in data:
            if value < 0 or (value >> frombits):
                return None
            acc = ((acc << frombits) | value) & max_acc
            bits += frombits
            while bits >= tobits:
                bits -= tobits
                ret.append((acc >> bits) & maxv)
        if pad:
            if bits:
                ret.append((acc << (tobits - bits)) & maxv)
        elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
            return None
        return ret

    @classmethod
    def decode_segwit_address(cls, hrp, addr):
        """Decode a SegWit address (v0-v16)"""
        hrpgot, data, encoding = cls.bech32_decode(addr)
        if hrpgot != hrp:
            return (None, None)
        decoded = cls.convertbits(data[1:], 5, 8, False)
        if decoded is None or len(decoded) < 2 or len(decoded) > 40:
            return (None, None)
        if data[0] > 16:
            return (None, None)

        # Witness v0 uses bech32, v1+ use bech32m
        if data[0] == 0:
            if encoding != 'bech32':
                return (None, None)
            if len(decoded) != 20 and len(decoded) != 32:
                return (None, None)
        else:
            if encoding != 'bech32m':
                return (None, None)
            # Taproot (v1) requires 32 bytes
            if data[0] == 1 and len(decoded) != 32:
                return (None, None)

        return (data[0], decoded)

    @classmethod
    def encode_segwit_address(cls, hrp, witver, witprog):
        """Encode a SegWit address"""
        # Witness v0 uses bech32, v1+ use bech32m
        const = cls.BECH32_CONST if witver == 0 else cls.BECH32M_CONST

        # Convert witness program to 5-bit groups
        data = cls.convertbits(witprog, 8, 5)
        if data is None:
            return None

        # Encode with witness version
        return cls.bech32_encode(hrp, [witver] + data, const)


@dataclass
class TxInput:
    """Bitcoin transaction input"""
    txid: str  # Previous transaction ID (hex string)
    vout: int  # Output index
    script_sig: bytes = b''  # Signature script (empty for unsigned)
    sequence: int = 0xffffffff  # Sequence number


@dataclass
class TxOutput:
    """Bitcoin transaction output"""
    amount: int  # Amount in satoshis
    script_pubkey: bytes  # Public key script


class BitcoinTransaction:
    """Bitcoin transaction builder and serializer"""

    def __init__(self, version: int = 2, locktime: int = 0):
        self.version = version
        self.inputs: List[TxInput] = []
        self.outputs: List[TxOutput] = []
        self.locktime = locktime

    def add_input(self, txid: str, vout: int, sequence: int = 0xffffffff):
        """Add an input to the transaction"""
        self.inputs.append(TxInput(
            txid=txid,
            vout=vout,
            sequence=sequence
        ))

    def add_output(self, amount_btc: float, script_pubkey: bytes):
        """
        Add an output to the transaction

        Args:
            amount_btc: Amount in BTC (will be converted to satoshis)
            script_pubkey: Output script
        """
        amount_satoshis = int(amount_btc * 100_000_000)
        self.outputs.append(TxOutput(
            amount=amount_satoshis,
            script_pubkey=script_pubkey
        ))

    @staticmethod
    def create_p2pkh_script(address_hash: bytes) -> bytes:
        """
        Create a Pay-to-PubKey-Hash (P2PKH) script

        Args:
            address_hash: 20-byte RIPEMD160(SHA256(pubkey))

        Returns:
            Script bytes: OP_DUP OP_HASH160 <hash> OP_EQUALVERIFY OP_CHECKSIG
        """
        # OP_DUP (0x76) OP_HASH160 (0xa9) <20 bytes> OP_EQUALVERIFY (0x88) OP_CHECKSIG (0xac)
        return bytes([0x76, 0xa9, 0x14]) + address_hash + bytes([0x88, 0xac])

    @staticmethod
    def create_p2tr_script(x_only_pubkey: bytes) -> bytes:
        """
        Create a Pay-to-Taproot (P2TR) script

        Args:
            x_only_pubkey: 32-byte x-only public key

        Returns:
            Script bytes: OP_1 <32 bytes>
        """
        if len(x_only_pubkey) != 32:
            raise ValueError(f"P2TR requires 32-byte x-only pubkey, got {len(x_only_pubkey)} bytes")
        # OP_1 (0x51) followed by 32-byte push
        return bytes([0x51, 0x20]) + x_only_pubkey

    @staticmethod
    def create_p2wpkh_script(witness_program: bytes) -> bytes:
        """
        Create a Pay-to-Witness-PubKey-Hash (P2WPKH) script

        Args:
            witness_program: 20-byte hash160(pubkey)

        Returns:
            Script bytes: OP_0 <20 bytes>
        """
        # OP_0 (0x00) <length> <witness_program>
        return bytes([0x00, 0x14]) + witness_program

    @staticmethod
    def decode_address_to_hash(address: str) -> Tuple[bytes, str]:
        """
        Decode a Bitcoin address to get the hash and address type

        Args:
            address: Bitcoin address (base58, bech32, or bech32m)

        Returns:
            Tuple of (hash bytes, address_type)
            - For P2PKH: (20-byte hash, 'p2pkh')
            - For P2WPKH: (20-byte hash, 'p2wpkh')
            - For P2WSH: (32-byte hash, 'p2wsh')
            - For P2TR: (32-byte x-only pubkey, 'p2tr')
        """
        # Check if bech32/bech32m (SegWit native)
        if address.startswith('bc1') or address.startswith('tb1') or address.startswith('bcrt1'):
            # Bech32 or Bech32m address (P2WPKH, P2WSH, or P2TR)
            # Determine HRP (human-readable part)
            if address.startswith('bc1'):
                hrp = 'bc'
            elif address.startswith('tb1'):
                hrp = 'tb'
            elif address.startswith('bcrt1'):
                hrp = 'bcrt'
            else:
                raise ValueError(f"Unknown bech32 prefix: {address[:4]}")

            # Decode bech32/bech32m
            witver, witprog = Bech32.decode_segwit_address(hrp, address)

            if witver is None:
                raise ValueError(f"Invalid bech32/bech32m address: {address}")

            if witver == 0 and len(witprog) == 20:
                # P2WPKH (witness version 0, 20 bytes) - bech32
                return (bytes(witprog), 'p2wpkh')
            elif witver == 0 and len(witprog) == 32:
                # P2WSH (witness version 0, 32 bytes) - bech32
                return (bytes(witprog), 'p2wsh')
            elif witver == 1 and len(witprog) == 32:
                # P2TR (witness version 1, 32 bytes) - bech32m (Taproot)
                return (bytes(witprog), 'p2tr')
            else:
                raise ValueError(f"Unsupported witness version or program length: v{witver}, {len(witprog)} bytes")
        else:
            # Base58 address (P2PKH or P2SH)
            import base58

            # Decode base58
            decoded = base58.b58decode(address)

            # Remove version byte (first) and checksum (last 4 bytes)
            address_hash = decoded[1:-4]

            # Check version byte to determine type
            version = decoded[0]

            # P2PKH: mainnet=0x00, testnet=0x6f, regtest=0x6f
            # P2SH: mainnet=0x05, testnet=0xc4, regtest=0xc4
            if version in [0x00, 0x6f]:
                return (address_hash, 'p2pkh')
            elif version in [0x05, 0xc4]:
                return (address_hash, 'p2sh')
            else:
                raise ValueError(f"Unknown address version byte: {hex(version)}")

    def serialize_for_signing(self, input_index: int, script_code: bytes, sighash_type: int = 1) -> bytes:
        """
        Serialize transaction for signing (create sighash)

        Args:
            input_index: Index of input being signed
            script_code: Script code (usually the scriptPubKey of the output being spent)
            sighash_type: Signature hash type (1 = SIGHASH_ALL)

        Returns:
            Serialized transaction for hashing
        """
        result = b''

        # Version
        result += struct.pack('<I', self.version)

        # Number of inputs
        result += self._encode_varint(len(self.inputs))

        # Inputs
        for i, tx_input in enumerate(self.inputs):
            # Previous output (txid + vout)
            result += bytes.fromhex(tx_input.txid)[::-1]  # Reverse byte order
            result += struct.pack('<I', tx_input.vout)

            # Script
            if i == input_index:
                # For the input being signed, use the script_code
                result += self._encode_varint(len(script_code))
                result += script_code
            else:
                # For other inputs, use empty script
                result += self._encode_varint(0)

            # Sequence
            result += struct.pack('<I', tx_input.sequence)

        # Number of outputs
        result += self._encode_varint(len(self.outputs))

        # Outputs
        for output in self.outputs:
            result += struct.pack('<Q', output.amount)
            result += self._encode_varint(len(output.script_pubkey))
            result += output.script_pubkey

        # Locktime
        result += struct.pack('<I', self.locktime)

        # Sighash type
        result += struct.pack('<I', sighash_type)

        return result

    def get_sighash(self, input_index: int, script_code: bytes, sighash_type: int = 1) -> bytes:
        """
        Get the signature hash for an input

        Args:
            input_index: Index of input to sign
            script_code: Script code (scriptPubKey of output being spent)
            sighash_type: Signature hash type (1 = SIGHASH_ALL)

        Returns:
            32-byte hash to sign
        """
        serialized = self.serialize_for_signing(input_index, script_code, sighash_type)
        return hashlib.sha256(hashlib.sha256(serialized).digest()).digest()

    def set_input_script_sig(self, input_index: int, script_sig: bytes):
        """Set the scriptSig for an input"""
        self.inputs[input_index].script_sig = script_sig

    @staticmethod
    def create_script_sig(signature_der: bytes, public_key: bytes, sighash_type: int = 1) -> bytes:
        """
        Create a scriptSig for P2PKH

        Args:
            signature_der: DER-encoded signature
            public_key: Compressed public key (33 bytes)
            sighash_type: Signature hash type (1 = SIGHASH_ALL)

        Returns:
            scriptSig bytes: <sig> <pubkey>
        """
        # Append sighash type to signature
        sig_with_sighash = signature_der + bytes([sighash_type])

        # Build scriptSig: <length> <sig+sighash> <length> <pubkey>
        script_sig = bytes([len(sig_with_sighash)]) + sig_with_sighash
        script_sig += bytes([len(public_key)]) + public_key

        return script_sig

    def serialize(self) -> bytes:
        """
        Serialize the complete signed transaction

        Returns:
            Raw transaction bytes
        """
        result = b''

        # Version
        result += struct.pack('<I', self.version)

        # Number of inputs
        result += self._encode_varint(len(self.inputs))

        # Inputs
        for tx_input in self.inputs:
            # Previous output (txid + vout)
            result += bytes.fromhex(tx_input.txid)[::-1]  # Reverse byte order
            result += struct.pack('<I', tx_input.vout)

            # Script sig
            result += self._encode_varint(len(tx_input.script_sig))
            result += tx_input.script_sig

            # Sequence
            result += struct.pack('<I', tx_input.sequence)

        # Number of outputs
        result += self._encode_varint(len(self.outputs))

        # Outputs
        for output in self.outputs:
            result += struct.pack('<Q', output.amount)
            result += self._encode_varint(len(output.script_pubkey))
            result += output.script_pubkey

        # Locktime
        result += struct.pack('<I', self.locktime)

        return result

    @staticmethod
    def _encode_varint(n: int) -> bytes:
        """Encode an integer as a Bitcoin variable-length integer"""
        if n < 0xfd:
            return bytes([n])
        elif n <= 0xffff:
            return b'\xfd' + struct.pack('<H', n)
        elif n <= 0xffffffff:
            return b'\xfe' + struct.pack('<I', n)
        else:
            return b'\xff' + struct.pack('<Q', n)


class BitcoinTransactionBuilder:
    """High-level interface for building Bitcoin transactions"""

    @staticmethod
    def build_p2pkh_transaction(
        utxo_txid: str,
        utxo_vout: int,
        utxo_amount_btc: float,
        sender_address: str,
        recipient_address: str,
        send_amount_btc: float,
        fee_btc: float = 0.00001
    ) -> Tuple[BitcoinTransaction, bytes]:
        """
        Build a Bitcoin transaction (supports P2PKH, P2WPKH, and P2TR addresses)

        Args:
            utxo_txid: Transaction ID of UTXO to spend
            utxo_vout: Output index of UTXO
            utxo_amount_btc: Amount in UTXO (BTC)
            sender_address: Address spending the UTXO
            recipient_address: Destination address
            send_amount_btc: Amount to send (BTC)
            fee_btc: Transaction fee (BTC)

        Returns:
            Tuple of (transaction, script_code_for_signing)
        """
        # Calculate change
        change_amount_btc = utxo_amount_btc - send_amount_btc - fee_btc

        if change_amount_btc < 0:
            raise ValueError(f"Insufficient funds: need {send_amount_btc + fee_btc} BTC, have {utxo_amount_btc} BTC")

        # Create transaction
        tx = BitcoinTransaction(version=2, locktime=0)

        # Add input
        tx.add_input(utxo_txid, utxo_vout)

        # Add output to recipient
        recipient_hash, recipient_type = BitcoinTransaction.decode_address_to_hash(recipient_address)

        if recipient_type == 'p2wpkh':
            recipient_script = BitcoinTransaction.create_p2wpkh_script(recipient_hash)
        elif recipient_type == 'p2pkh':
            recipient_script = BitcoinTransaction.create_p2pkh_script(recipient_hash)
        elif recipient_type == 'p2tr':
            recipient_script = BitcoinTransaction.create_p2tr_script(recipient_hash)
        else:
            raise ValueError(f"Unsupported recipient address type: {recipient_type}")

        tx.add_output(send_amount_btc, recipient_script)

        # Add change output if significant (dust threshold = 0.00001 BTC)
        if change_amount_btc >= 0.00001:
            sender_hash, sender_type = BitcoinTransaction.decode_address_to_hash(sender_address)

            if sender_type == 'p2wpkh':
                change_script = BitcoinTransaction.create_p2wpkh_script(sender_hash)
            elif sender_type == 'p2pkh':
                change_script = BitcoinTransaction.create_p2pkh_script(sender_hash)
            elif sender_type == 'p2tr':
                change_script = BitcoinTransaction.create_p2tr_script(sender_hash)
            else:
                raise ValueError(f"Unsupported sender address type: {sender_type}")

            tx.add_output(change_amount_btc, change_script)

        # Create script_code for signing (the scriptPubKey of the output being spent)
        sender_hash, sender_type = BitcoinTransaction.decode_address_to_hash(sender_address)

        if sender_type == 'p2wpkh':
            # For P2WPKH, script_code is P2PKH of the same hash
            script_code = BitcoinTransaction.create_p2pkh_script(sender_hash)
        elif sender_type == 'p2pkh':
            script_code = BitcoinTransaction.create_p2pkh_script(sender_hash)
        elif sender_type == 'p2tr':
            # P2TR uses Schnorr signatures, not ECDSA
            # Current MPC implementation only supports ECDSA
            raise NotImplementedError(
                "Spending from P2TR (Taproot) addresses is not yet supported. "
                "Taproot requires Schnorr signatures, but the current MPC protocol uses ECDSA. "
                "You can receive TO Taproot addresses, but cannot spend FROM them yet. "
                "Use P2PKH or P2WPKH addresses for spending."
            )
        else:
            raise ValueError(f"Unsupported sender address type: {sender_type}")

        return tx, script_code

    @staticmethod
    def sign_transaction(
        tx: BitcoinTransaction,
        input_index: int,
        script_code: bytes,
        signature_der: bytes,
        public_key: bytes
    ) -> BitcoinTransaction:
        """
        Add signature to transaction input

        Args:
            tx: Transaction to sign
            input_index: Input index to sign
            script_code: Script code used for signing
            signature_der: DER-encoded signature
            public_key: Public key (33 bytes compressed)

        Returns:
            Signed transaction
        """
        # Create scriptSig
        script_sig = BitcoinTransaction.create_script_sig(signature_der, public_key)

        # Set the scriptSig for the input
        tx.set_input_script_sig(input_index, script_sig)

        return tx


if __name__ == "__main__":
    # Example usage
    print("Bitcoin Transaction Builder")
    print("=" * 80)
    print()
    print("This module provides Bitcoin transaction construction for MPC signing")
    print()
    print("Key features:")
    print("  ✓ Build P2PKH transactions")
    print("  ✓ Calculate signature hashes (sighash)")
    print("  ✓ Create scriptSig from MPC signatures")
    print("  ✓ Serialize transactions for broadcast")
    print()
