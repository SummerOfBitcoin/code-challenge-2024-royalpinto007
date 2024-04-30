import json
import os
import hashlib
import time
import binascii

from coinbase import serialize_coinbase_transaction
from utilities import reverse_bytes, hash256
from transaction_serialization import serialize_transaction
from txid_serialization_backup import serialize

MEMPOOL_DIR = "mempool"
OUTPUT_FILE = "output.txt"
DIFFICULTY_TARGET = "0000ffff00000000000000000000000000000000000000000000000000000000"
BLOCK_VERSION = 4
WITNESS_RESERVED_VALUE_HEX = (
    "0000000000000000000000000000000000000000000000000000000000000000"
)

WITNESS_RESERVED_VALUE_BYTES = bytes.fromhex(WITNESS_RESERVED_VALUE_HEX)
WTXID_COINBASE = bytes(32).hex()


def get_fee(transaction):
    in_value = [int(i["prevout"]["value"]) for i in transaction["vin"]]
    total_sum_in_value = sum(in_value)
    out_value = [int(i["value"]) for i in transaction["vout"]]
    total_sum_out_value = sum(out_value)
    return total_sum_in_value - total_sum_out_value


def pre_process_transaction(transaction):

    global p2pkh, p2wpkh, p2sh
    transaction["txid"] = reverse_bytes(hash256(serialize(transaction)))
    transaction["weight"] = 1
    transaction["wtxid"] = reverse_bytes(hash256(serialize_transaction(transaction)))
    transaction["fee"] = transaction.get("fee", get_fee(transaction))

    return transaction


def read_transaction_file(filename):
    with open(os.path.join(MEMPOOL_DIR, filename), "r") as file:
        transaction = json.load(file)

    pre_process_transaction(transaction)
    return transaction


def validate_transaction(transaction):
    return True


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


def mine_block(transactions):
    nonce = 0
    txids = [tx["txid"] for tx in transactions]

    witness_commitment = calculate_witness_commitment(transactions)
    print("witneness commitment:", witness_commitment)

    coinbase_hex, coinbase_txid = serialize_coinbase_transaction(
        witness_commitment=witness_commitment
    )

    merkle_root = generate_merkle_root([coinbase_txid] + txids)

    block_version_bytes = BLOCK_VERSION.to_bytes(4, "little")
    prev_block_hash_bytes = bytes.fromhex(
        "0000000000000000000000000000000000000000000000000000000000000000"
    )
    merkle_root_bytes = bytes.fromhex(merkle_root)
    timestamp_bytes = int(time.time()).to_bytes(4, "little")
    bits_bytes = (0x1F00FFFF).to_bytes(4, "little")
    nonce_bytes = nonce.to_bytes(4, "little")

    block_header = (
        block_version_bytes
        + prev_block_hash_bytes
        + merkle_root_bytes
        + timestamp_bytes
        + bits_bytes
        + nonce_bytes
    )

    target = int(DIFFICULTY_TARGET, 16)
    print("target:", target)
    while True:
        block_hash = hashlib.sha256(hashlib.sha256(block_header).digest()).digest()
        reversed_hash = block_hash[::-1]
        if int.from_bytes(reversed_hash, "big") <= target:
            break
        nonce += 1
        nonce_bytes = nonce.to_bytes(4, "little")
        block_header = block_header[:-4] + nonce_bytes
        if nonce < 0x0 or nonce > 0xFFFFFFFF:
            raise ValueError("Invalid nonce")

    block_header_hex = block_header.hex()
    validate_header(block_header_hex, DIFFICULTY_TARGET)

    return block_header_hex, txids, nonce, coinbase_hex, coinbase_txid


def hash256(hex):
    binary = bytes.fromhex(hex)
    hash1 = hashlib.sha256(binary).digest()
    hash2 = hashlib.sha256(hash1).digest()
    result = hash2.hex()
    return result


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


def calculate_total_weight_and_fee(transactions):
    total_weight = 0
    total_fee = 0
    for tx in transactions:
        total_weight += tx["weight"]
        total_fee += tx["fee"]

    if total_weight > 4000000:
        raise ValueError("Block exceeds maximum weight")

    return total_weight, total_fee


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


def validate_block(coinbase_tx, txids, transactions):

    mempool_txids = set()
    for filename in os.listdir(MEMPOOL_DIR):
        tx_data = read_transaction_file(filename)
        if "vin" in tx_data and len(tx_data["vin"]) > 0 and "txid" in tx_data["vin"][0]:
            mempool_txids.add(tx_data["vin"][0]["txid"])
        else:
            raise ValueError(f"Transaction file {filename} is missing 'txid' in 'vin'")

    for txid in txids:
        if txid not in mempool_txids:
            raise ValueError(f"Invalid txid found in block: {txid}")

    total_weight, total_fee = calculate_total_weight_and_fee(transactions)

    witness_commitment = calculate_witness_commitment(transactions)
    if not verify_witness_commitment(coinbase_tx, witness_commitment):
        raise ValueError("Invalid witness commitment in coinbase transaction")

    print(
        f"Block is valid with a total weight of {total_weight} and a total fee of {total_fee}!"
    )


def main():
    transactions = []

    with open("valid-mempool.json", "r") as file:
        unverified_txns = json.load(file)

    for tx in unverified_txns[:2100]:
        verified_tx = pre_process_transaction(tx)
        transactions.append(verified_tx)

    print(f"Total transactions: {len(transactions)}")

    if not any(transactions):
        raise ValueError("No valid transactions to include in the block")

    block_header, txids, nonce, coinbase_tx_hex, coinbase_txid = mine_block(
        transactions
    )

    with open(OUTPUT_FILE, "w") as file:
        file.write(f"{block_header}\n{coinbase_tx_hex}\n{coinbase_txid}\n")
        file.writelines(f"{txid}\n" for txid in txids)

    total_weight, total_fee = calculate_total_weight_and_fee(transactions)
    print(f"Total weight: {total_weight}")
    print(f"Total fee: {total_fee}")


if __name__ == "__main__":
    main()
