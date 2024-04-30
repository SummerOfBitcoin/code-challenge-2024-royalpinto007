import json
import os
import hashlib
import time

from coinbase import serialize_coinbase_transaction
from utilities import reverse_bytes, hash256
from transaction_serialization import serialize_transaction
from txid_serialization_backup import serialize
from calculations import generate_merkle_root, hash256, calculate_total_weight_and_fee
from witness import calculate_witness_commitment, verify_witness_commitment
from header import validate_header

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
