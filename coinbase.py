from utilities import hash256, reverse_bytes
from transaction_serialization import serialize_transaction


def serialize_coinbase_transaction(witness_commitment):
    tx_dict = {
        "version": "01000000",
        "marker": "00",
        "flag": "01",
        "inputcount": "01",
        "inputs": [
            {
                "txid": "0000000000000000000000000000000000000000000000000000000000000000",
                "vout": "ffffffff",
                "scriptsigsize": "25",
                "scriptsig": "03233708184d696e656420627920416e74506f6f6c373946205b8160a4256c0000946e0100",
                "sequence": "ffffffff",
            }
        ],
        "outputcount": "02",
        "outputs": [
            {
                "amount": "f595814a00000000",
                "scriptpubkeysize": "19",
                "scriptpubkey": "76a914edf10a7fac6b32e24daa5305c723f3de58db1bc888ac",
            },
            {
                "amount": "0000000000000000",
                "scriptpubkeysize": "26",
                "scriptpubkey": f"6a24aa21a9ed{witness_commitment}",
            },
        ],
        "witness": [
            {
                "stackitems": "01",
                "0": {
                    "size": "20",
                    "item": "0000000000000000000000000000000000000000000000000000000000000000",
                },
            }
        ],
        "locktime": "00000000",
    }
    tx_dict_modified = {
        "version": 1,
        "marker": "00",
        "flag": "01",
        "inputcount": "01",
        "vin": [
            {
                "txid": "0000000000000000000000000000000000000000000000000000000000000000",
                "vout": int("ffffffff", 16),
                "scriptsigsize": 37,
                "scriptsig": "03233708184d696e656420627920416e74506f6f6c373946205b8160a4256c0000946e0100",
                "sequence": int("ffffffff", 16),
            }
        ],
        "outputcount": "02",
        "vout": [
            {
                "value": 2753059167,
                "scriptpubkeysize": "19",
                "scriptpubkey": "76a914edf10a7fac6b32e24daa5305c723f3de58db1bc888ac",
            },
            {
                "value": 0,
                "scriptpubkeysize": "26",
                "scriptpubkey": f"6a24aa21a9ed{witness_commitment}",
            },
        ],
        "witness": [
            {
                "stackitems": "01",
                "0": {
                    "size": "20",
                    "item": "0000000000000000000000000000000000000000000000000000000000000000",
                },
            }
        ],
        "locktime": 0,
    }
    serialized_tx = tx_dict["version"]
    serialized_tx += tx_dict["marker"] + tx_dict["flag"]
    serialized_tx += tx_dict["inputcount"]
    input_data = tx_dict["inputs"][0]
    serialized_tx += input_data["txid"]
    serialized_tx += input_data["vout"]
    serialized_tx += input_data["scriptsigsize"].zfill(2)
    serialized_tx += input_data["scriptsig"]
    serialized_tx += input_data["sequence"]
    serialized_tx += tx_dict["outputcount"]
    for output in tx_dict["outputs"]:
        serialized_tx += output["amount"].zfill(16)
        serialized_tx += output["scriptpubkeysize"].zfill(2)
        serialized_tx += output["scriptpubkey"]
    witness_data = tx_dict["witness"][0]
    serialized_tx += witness_data["stackitems"]
    serialized_tx += witness_data["0"]["size"].zfill(2)
    serialized_tx += witness_data["0"]["item"]
    serialized_tx += tx_dict["locktime"]
    return serialized_tx, reverse_bytes(
        hash256(serialize_transaction(tx_dict_modified))
    )
