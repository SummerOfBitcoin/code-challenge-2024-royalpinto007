import json

with open("total-mempool.json", "r") as file:
    mempool_data = json.load(file)

for transaction in mempool_data:
    vin = transaction.get("vin")

    if len(vin) == 1:
        prevout = vin[0].get("prevout")

        if prevout.get("scriptpubkey_type") == "p2pkh":
            print("ScriptPubKey ASM:", prevout.get("scriptpubkey_asm"))
            print("ScriptPubKey Type:", prevout.get("scriptpubkey_type"))

    print(vin)
