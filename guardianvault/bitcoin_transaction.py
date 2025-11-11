#!/usr/bin/env python3
"""
Bitcoin Transaction Builder
Constructs and signs Bitcoin transactions compatible with MPC threshold signing
"""

import hashlib
import struct
from typing import List, Tuple
from dataclasses import dataclass


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
    def decode_address_to_hash(address: str) -> bytes:
        """
        Decode a Bitcoin address to get the 20-byte hash

        Args:
            address: Bitcoin address (base58)

        Returns:
            20-byte hash
        """
        import base58

        # Decode base58
        decoded = base58.b58decode(address)

        # Remove version byte (first) and checksum (last 4 bytes)
        address_hash = decoded[1:-4]

        return address_hash

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
        Build a P2PKH transaction

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
        recipient_hash = BitcoinTransaction.decode_address_to_hash(recipient_address)
        recipient_script = BitcoinTransaction.create_p2pkh_script(recipient_hash)
        tx.add_output(send_amount_btc, recipient_script)

        # Add change output if significant (dust threshold = 0.00001 BTC)
        if change_amount_btc >= 0.00001:
            sender_hash = BitcoinTransaction.decode_address_to_hash(sender_address)
            change_script = BitcoinTransaction.create_p2pkh_script(sender_hash)
            tx.add_output(change_amount_btc, change_script)

        # Create script_code for signing (the scriptPubKey of the output being spent)
        sender_hash = BitcoinTransaction.decode_address_to_hash(sender_address)
        script_code = BitcoinTransaction.create_p2pkh_script(sender_hash)

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
