from utilities import convert_to_little_endian, calculate_compact_size


def serialize(txn_dict):

    txn_hash = ""
    data = txn_dict
    txn_hash += f"{convert_to_little_endian(data['version'], 4)}"
    txn_hash += f"{str(calculate_compact_size(len(data['vin'])))}"

    for input_data in data["vin"]:
        txn_hash += f"{bytes.fromhex(input_data['txid'])[::-1].hex()}"
        txn_hash += f"{convert_to_little_endian(input_data['vout'], 4)}"
        txn_hash += f"{calculate_compact_size(len(input_data['scriptsig']) // 2)}"
        txn_hash += f"{input_data['scriptsig']}"
        txn_hash += f"{convert_to_little_endian(input_data['sequence'], 4)}"

    txn_hash += f"{str(calculate_compact_size(len(data['vout'])))}"

    for output in data["vout"]:
        txn_hash += f"{convert_to_little_endian(output['value'], 8)}"
        txn_hash += f"{calculate_compact_size(len(output['scriptpubkey']) // 2)}"
        txn_hash += f"{output['scriptpubkey']}"

    txn_hash += f"{convert_to_little_endian(data['locktime'], 4)}"

    return txn_hash
