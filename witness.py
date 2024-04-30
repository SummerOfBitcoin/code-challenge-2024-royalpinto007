import hashlib
from calculations import generate_merkle_root
from utilities import hash256

WITNESS_RESERVED_VALUE_HEX = (
    "0000000000000000000000000000000000000000000000000000000000000000"
)

WITNESS_RESERVED_VALUE_BYTES = bytes.fromhex(WITNESS_RESERVED_VALUE_HEX)
WTXID_COINBASE = bytes(32).hex()


def calculate_witness_commitment(transactions):
    wtxids = [WTXID_COINBASE]
    for tx in transactions:
        wtxids.append(tx["wtxid"])
    witness_root = generate_merkle_root(wtxids)

    witness_reserved_value_hex = WITNESS_RESERVED_VALUE_HEX

    combined_data = witness_root + witness_reserved_value_hex

    witness_commitment = hash256(combined_data)

    return witness_commitment


def verify_witness_commitment(coinbase_tx, witness_commitment):
    for output in coinbase_tx["vout"]:
        script_hex = output["scriptPubKey"]["hex"]
        if script_hex.startswith("6a24aa21a9ed") and script_hex.endswith(
            witness_commitment
        ):
            return True
    return False
