import binascii
import hashlib


def validate_header(header, target_difficulty):
    header_bytes = binascii.unhexlify(header)
    if len(header_bytes) != 80:
        raise ValueError("Invalid header length")

    h1 = hashlib.sha256(header_bytes).digest()
    h2 = hashlib.sha256(h1).digest()

    reversed_hash = h2[::-1]

    reversed_hash_int = int.from_bytes(reversed_hash, byteorder="big")
    target_int = int(target_difficulty, 16)

    if reversed_hash_int > target_int:
        raise ValueError("Block does not meet target difficulty")
