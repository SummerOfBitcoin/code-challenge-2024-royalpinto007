import hashlib
import json
import os


def to_hash160(hex_input):
    sha = hashlib.sha256(bytes.fromhex(hex_input)).hexdigest()
    hash_160 = hashlib.new("ripemd160")
    hash_160.update(bytes.fromhex(sha))
    return hash_160.hexdigest()


def to_compact_size(value):
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


def to_little_endian(num, size):
    return num.to_bytes(size, byteorder="little").hex()


def legacy_txn_data(txn_id):
    txn_hash = ""
    file_path = os.path.join("mempool", f"{txn_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
            txn_hash += f"{to_little_endian(data['version'], 4)}"
            txn_hash += f"{str(to_compact_size(len(data['vin'])))}"
            for iN in data["vin"]:
                txn_hash += f"{bytes.fromhex(iN['txid'])[::-1].hex()}"
                txn_hash += f"{to_little_endian(iN['vout'], 4)}"
                txn_hash += f"{to_compact_size(len(iN['prevout']['scriptpubkey'])//2)}"
                txn_hash += f"{iN['prevout']['scriptpubkey']}"
                txn_hash += f"{to_little_endian(iN['sequence'], 4)}"
            txn_hash += f"{str(to_compact_size(len(data['vout'])))}"
            for out in data["vout"]:
                txn_hash += f"{to_little_endian(out['value'], 8)}"
                txn_hash += f"{to_compact_size(len(out['scriptpubkey'])//2)}"
                txn_hash += f"{out['scriptpubkey']}"
            txn_hash += f"{to_little_endian(data['locktime'], 4)}"
    return txn_hash


def validate_p2sh_txn_basic(inner_redeemscript_asm, scriptpubkey_asm):
    inner_script = inner_redeemscript_asm.split(" ")
    scriptpubkey = scriptpubkey_asm.split(" ")
    stack = []
    redeem_script = ""
    for i in inner_script:
        if i == "OP_0":
            redeem_script += "00"
        if i == "OP_PUSHNUM_2":
            redeem_script += "02"
        if i == "OP_PUSHBYTES_20":
            redeem_script += "14"
            redeem_script += inner_script[inner_script.index("OP_PUSHBYTES_20") + 1]
        if i == "OP_PUSHBYTES_33":
            redeem_script += "21"
            redeem_script += inner_script[inner_script.index("OP_PUSHBYTES_33") + 1]
    stack.append(redeem_script)
    for i in scriptpubkey:
        if i == "OP_HASH160":
            ripemd160_hash = to_hash160(stack[-1])
            stack.pop(-1)
            stack.append(ripemd160_hash)
        if i == "OP_PUSHBYTES_20":
            stack.append(scriptpubkey[scriptpubkey.index("OP_PUSHBYTES_20") + 1])
        if i == "OP_EQUAL":
            return stack[-1] == stack[-2]


def validate_p2sh_txn_adv(
    inner_redeemscript_asm, scriptpubkey_asm, scriptsig_asm, txn_data
):
    inner_redeemscript = inner_redeemscript_asm.split(" ")
    scriptpubkey = scriptpubkey_asm.split(" ")
    scriptsig = scriptsig_asm.split(" ")
    redeem_stack = []
    signatures = []
    for item in scriptsig:
        if "OP_PUSHBYTES_" in item:
            signatures.append(scriptsig[scriptsig.index(item) + 1])
            scriptsig[scriptsig.index(item)] = "DONE"
    for item in inner_redeemscript:
        if "OP_PUSHNUM_" in item:
            num = item[len("OP_PUSHNUM_") :]
            redeem_stack.append(int(num))
        if "OP_PUSHBYTES_" in item:
            redeem_stack.append(inner_redeemscript[inner_redeemscript.index(item) + 1])
            inner_redeemscript[inner_redeemscript.index(item)] = "DONE"
        if "OP_CHECKMULTISIG" in item:
            msg = txn_data + "01000000"
            msg_hash = hashlib.sha256(bytes.fromhex(msg)).digest().hexdigest()
    return redeem_stack, signatures, msg_hash
