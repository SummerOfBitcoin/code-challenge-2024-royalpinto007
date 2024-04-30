import hashlib
from utilities import hash256

WITNESS_RESERVED_VALUE_HEX = (
    "0000000000000000000000000000000000000000000000000000000000000000"
)


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


def calculate_witness_commitment(wtxids):

    witness_root = generate_merkle_root(wtxids)
    witness_reserved_value_hex = WITNESS_RESERVED_VALUE_HEX
    combined_data = witness_root + witness_reserved_value_hex
    witness_commitment = hash256(combined_data)

    return witness_commitment
