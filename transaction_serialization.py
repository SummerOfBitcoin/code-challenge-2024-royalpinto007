from utilities import convert_to_little_endian, calculate_compact_size


def serialize_transaction(txn_data):

    serialized_txn = ""
    data = txn_data
    serialized_txn += f"{convert_to_little_endian(data['version'], 4)}"

    if any(i.get("scriptsig") == "" for i in data["vin"]):
        serialized_txn += "0001"

    serialized_txn += f"{str(calculate_compact_size(len(data['vin'])))}"

    for input_data in data["vin"]:
        serialized_txn += f"{bytes.fromhex(input_data['txid'])[::-1].hex()}"
        serialized_txn += f"{convert_to_little_endian(input_data['vout'], 4)}"
        serialized_txn += f"{calculate_compact_size(len(input_data['scriptsig']) // 2)}"
        serialized_txn += f"{input_data['scriptsig']}"
        serialized_txn += f"{convert_to_little_endian(input_data['sequence'], 4)}"

    serialized_txn += f"{str(calculate_compact_size(len(data['vout'])))}"

    for output in data["vout"]:
        serialized_txn += f"{convert_to_little_endian(output['value'], 8)}"
        serialized_txn += f"{calculate_compact_size(len(output['scriptpubkey']) // 2)}"
        serialized_txn += f"{output['scriptpubkey']}"

    for input_data in data["vin"]:
        if "witness" in input_data and input_data["witness"]:
            serialized_txn += f"{calculate_compact_size(len(input_data['witness']))}"
            for witness_data in input_data["witness"]:
                serialized_txn += f"{calculate_compact_size(len(witness_data) // 2)}"
                serialized_txn += f"{witness_data}"

    serialized_txn += f"{convert_to_little_endian(data['locktime'], 4)}"

    return serialized_txn
