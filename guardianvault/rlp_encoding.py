"""
RLP (Recursive Length Prefix) Encoding for Ethereum

RLP is used to encode arbitrarily nested arrays of binary data.
This implementation follows the Ethereum specification.
"""

from typing import Union, List


def encode(data: Union[bytes, List]) -> bytes:
    """
    Encode data using RLP.

    Args:
        data: Either bytes or a list of items (recursively encodable)

    Returns:
        RLP-encoded bytes
    """
    if isinstance(data, bytes):
        return encode_bytes(data)
    elif isinstance(data, list):
        return encode_list(data)
    else:
        raise TypeError(f"Cannot RLP encode type {type(data)}")


def encode_bytes(data: bytes) -> bytes:
    """
    Encode a byte string using RLP.

    Rules:
    - For a single byte in [0x00, 0x7f], the byte itself is the encoding
    - For 0-55 bytes long, encoding is: [0x80 + length, data...]
    - For 56+ bytes long, encoding is: [0xb7 + length_of_length, length..., data...]
    """
    length = len(data)

    if length == 1 and data[0] < 0x80:
        # Single byte < 128: the byte is its own encoding
        return data
    elif length <= 55:
        # Short string: [0x80 + length] + data
        return bytes([0x80 + length]) + data
    else:
        # Long string: [0xb7 + len(length)] + length + data
        length_bytes = length.to_bytes((length.bit_length() + 7) // 8, 'big')
        return bytes([0xb7 + len(length_bytes)]) + length_bytes + data


def encode_list(data: List) -> bytes:
    """
    Encode a list using RLP.

    Rules:
    - Concatenate RLP encodings of each element
    - If total payload is 0-55 bytes: [0xc0 + length, payload...]
    - If total payload is 56+ bytes: [0xf7 + length_of_length, length..., payload...]
    """
    # Encode all list elements
    encoded_items = b''.join(encode(item) for item in data)
    length = len(encoded_items)

    if length <= 55:
        # Short list: [0xc0 + length] + payload
        return bytes([0xc0 + length]) + encoded_items
    else:
        # Long list: [0xf7 + len(length)] + length + payload
        length_bytes = length.to_bytes((length.bit_length() + 7) // 8, 'big')
        return bytes([0xf7 + len(length_bytes)]) + length_bytes + encoded_items


def encode_int(value: int) -> bytes:
    """
    Encode an integer as bytes for RLP.

    Rules:
    - 0 encodes as empty bytes b''
    - Positive integers encode as big-endian bytes with no leading zeros
    """
    if value == 0:
        return b''

    # Convert to bytes without leading zeros
    num_bytes = (value.bit_length() + 7) // 8
    return value.to_bytes(num_bytes, 'big')


def encode_address(address: str) -> bytes:
    """
    Encode an Ethereum address (hex string) as bytes for RLP.

    Args:
        address: Ethereum address as hex string (with or without 0x prefix)

    Returns:
        20 bytes representing the address
    """
    if address.startswith('0x'):
        address = address[2:]

    if len(address) != 40:
        raise ValueError(f"Invalid Ethereum address length: {len(address)} (expected 40)")

    return bytes.fromhex(address)


def decode(data: bytes) -> Union[bytes, List]:
    """
    Decode RLP-encoded data.

    Args:
        data: RLP-encoded bytes

    Returns:
        Decoded data (bytes or list)
    """
    if not data:
        raise ValueError("Cannot decode empty data")

    result, remaining = decode_with_remainder(data)

    if remaining:
        raise ValueError(f"Extra data after decoding: {remaining.hex()}")

    return result


def decode_with_remainder(data: bytes) -> tuple:
    """
    Decode RLP data and return both the decoded value and remaining bytes.

    Returns:
        (decoded_value, remaining_bytes)
    """
    if not data:
        raise ValueError("Cannot decode empty data")

    first_byte = data[0]

    if first_byte <= 0x7f:
        # Single byte
        return bytes([first_byte]), data[1:]

    elif first_byte <= 0xb7:
        # Short string
        length = first_byte - 0x80
        if length == 0:
            return b'', data[1:]
        return data[1:1+length], data[1+length:]

    elif first_byte <= 0xbf:
        # Long string
        length_of_length = first_byte - 0xb7
        length = int.from_bytes(data[1:1+length_of_length], 'big')
        start = 1 + length_of_length
        return data[start:start+length], data[start+length:]

    elif first_byte <= 0xf7:
        # Short list
        length = first_byte - 0xc0
        if length == 0:
            return [], data[1:]

        list_data = data[1:1+length]
        result = []
        pos = 0

        while pos < length:
            item, remainder = decode_with_remainder(list_data[pos:])
            result.append(item)
            pos = length - len(remainder)

        return result, data[1+length:]

    else:
        # Long list
        length_of_length = first_byte - 0xf7
        length = int.from_bytes(data[1:1+length_of_length], 'big')
        start = 1 + length_of_length

        list_data = data[start:start+length]
        result = []
        pos = 0

        while pos < length:
            item, remainder = decode_with_remainder(list_data[pos:])
            result.append(item)
            pos = length - len(remainder)

        return result, data[start+length:]


def decode_int(data: bytes) -> int:
    """
    Decode RLP-encoded bytes as an integer.

    Args:
        data: RLP-encoded integer (as bytes)

    Returns:
        Integer value
    """
    if not data:
        return 0
    return int.from_bytes(data, 'big')


if __name__ == "__main__":
    # Test cases
    print("Testing RLP encoding...")

    # Test 1: Single byte
    assert encode(b'\x00') == b'\x00'
    assert encode(b'\x7f') == b'\x7f'
    assert encode(b'\x80') == b'\x81\x80'
    print("✓ Single byte encoding")

    # Test 2: Short string
    assert encode(b'dog') == b'\x83dog'
    print("✓ Short string encoding")

    # Test 3: Empty string
    assert encode(b'') == b'\x80'
    print("✓ Empty string encoding")

    # Test 4: Empty list
    assert encode([]) == b'\xc0'
    print("✓ Empty list encoding")

    # Test 5: List of strings
    result = encode([b'cat', b'dog'])
    assert result == b'\xc8\x83cat\x83dog'
    print("✓ List encoding")

    # Test 6: Nested list
    result = encode([[], [[]], [[], [[]]]])
    assert result == b'\xc7\xc0\xc1\xc0\xc3\xc0\xc1\xc0'
    print("✓ Nested list encoding")

    # Test 7: Integer encoding
    assert encode_int(0) == b''
    assert encode_int(127) == b'\x7f'
    assert encode_int(128) == b'\x80'
    assert encode_int(256) == b'\x01\x00'
    print("✓ Integer encoding")

    # Test 8: Decoding
    assert decode(b'\x83dog') == b'dog'
    assert decode(b'\xc8\x83cat\x83dog') == [b'cat', b'dog']
    print("✓ Decoding")

    print("\nAll RLP tests passed! ✓")
