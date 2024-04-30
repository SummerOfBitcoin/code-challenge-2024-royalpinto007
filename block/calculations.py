from utilities import hash256
import hashlib


def generate_merkle_root(txids):
    if len(txids) == 0:
        return None

    level = [bytes.fromhex(txid)[::-1].hex() for txid in txids]

    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            if i + 1 == len(level):
                pair_hash = hash256(level[i] + level[i])
            else:
                pair_hash = hash256(level[i] + level[i + 1])
            next_level.append(pair_hash)
        level = next_level
    return level[0]


def target_to_bits(target):
    target_bytes = bytes.fromhex(target)

    for i in range(len(target_bytes)):
        if target_bytes[i] != 0:
            break

    exponent = len(target_bytes) - i

    if len(target_bytes[i:]) >= 3:
        coefficient = int.from_bytes(target_bytes[i : i + 3], byteorder="big")
    else:
        coefficient = int.from_bytes(target_bytes[i:], byteorder="big")

    bits = (exponent << 24) | coefficient

    return hex(bits)


def hash256(hex):
    binary = bytes.fromhex(hex)
    hash1 = hashlib.sha256(binary).digest()
    hash2 = hashlib.sha256(hash1).digest()
    result = hash2.hex()
    return result


def calculate_total_weight_and_fee(transactions):
    total_weight = 0
    total_fee = 0
    for tx in transactions:
        total_weight += tx["weight"]
        total_fee += tx["fee"]

    if total_weight > 4000000:
        raise ValueError("Block exceeds maximum weight")

    return total_weight, total_fee
