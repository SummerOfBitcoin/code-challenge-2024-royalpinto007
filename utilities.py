import hashlib


def calculate_compact_size(value):
    if value < 0xFD:
        return value.to_bytes(1, byteorder="little").hex()
    elif value <= 0xFFFF:
        return (0xFD).to_bytes(1, byteorder="little").hex() + value.to_bytes(
            2, byteorder="little"
        ).hex()
    elif value <= 0xFFFFFFFF:
        return (0xFE).to_bytes(1, byteorder="little").hex() + value.to_bytes(
            4, byteorder="little"
        ).hex()
    else:
        return (0xFF).to_bytes(1, byteorder="little").hex() + value.to_bytes(
            8, byteorder="little"
        ).hex()


def convert_to_little_endian(num, size):
    return num.to_bytes(size, byteorder="little").hex()


def reverse_bytes(hex_input):
    return bytes.fromhex(hex_input)[::-1].hex()


def hash256(hex_input):
    return (
        hashlib.sha256(hashlib.sha256(bytes.fromhex(hex_input)).digest()).digest().hex()
    )
