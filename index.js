const fs = require("fs");
const crypto = require("crypto");
const secp256k1 = require("secp256k1");
const bs58 = require("bs58");

// read JSON files from the mempool folder
function readMempool() {
  const mempoolFiles = fs.readdirSync("./mempool");
  const transactions = [];
  mempoolFiles.forEach((file) => {
    const data = fs.readFileSync(`./mempool/${file}`);
    const transaction = JSON.parse(data);
    transactions.push(transaction);
  });
  return transactions;
}

// scriptPubKey hex to address
function convertScriptPubKeyToAddress(scriptPubKeyHex) {
  const publicKey = Buffer.from(scriptPubKeyHex, "hex");
  const base58Address = generateBase58Address(publicKey);
  const bech32Address = encodeBech32(publicKey);
  return { base58Address, bech32Address };
}

// generate base58 address from public key
function generateBase58Address(publicKey) {
  const hash = crypto.createHash("sha256").update(publicKey).digest();
  const ripemd160 = crypto.createHash("ripemd160").update(hash).digest();
  const pubKeyHashWithVersion = Buffer.concat([Buffer.from([0x00]), ripemd160]);
  const addressChecksum = crypto
    .createHash("sha256")
    .update(pubKeyHashWithVersion)
    .digest();
  const addressChecksum2 = crypto
    .createHash("sha256")
    .update(addressChecksum)
    .digest()
    .slice(0, 4);
  const base58Address = bs58.encode(
    Buffer.concat([pubKeyHashWithVersion, addressChecksum2])
  );
  return base58Address;
}

// // Function to convert scriptPubKey hex to address
// function convertScriptPubKeyToAddress(scriptPubKeyHex) {
//  const publicKey = Buffer.from(scriptPubKeyHex, "hex");

//  // Function to generate base58 address from public key
//  function generateBase58Address(publicKey) {
//    const hash = crypto.createHash("sha256").update(publicKey).digest();
//    const ripemd160 = crypto.createHash("ripemd160").update(hash).digest();
//    const pubKeyHashWithVersion = Buffer.concat([
//      Buffer.from([0x00]),
//      ripemd160,
//    ]);
//    const addressChecksum = crypto
//      .createHash("sha256")
//      .update(pubKeyHashWithVersion)
//      .digest();
//    const addressChecksum2 = crypto
//      .createHash("sha256")
//      .update(addressChecksum)
//      .digest()
//      .slice(0, 4);
//    const base58Address = base58encode(
//      Buffer.concat([pubKeyHashWithVersion, addressChecksum2])
//    );
//    return base58Address;
//  }

//  // Function to encode bytes to base58
//  function base58encode(bytes) {
//    const alphabet =
//      "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
//    let bigInt = BigInt("0x" + bytes.toString("hex"));
//    let encoded = "";
//    while (bigInt > 0n) {
//      const remainder = bigInt % 58n;
//      bigInt = bigInt / 58n;
//      encoded = alphabet[Number(remainder)] + encoded;
//    }
//    for (const byte of bytes) {
//      if (byte !== 0) break;
//      encoded = "1" + encoded;
//    }
//    return encoded;
//  }

// encode bytes to bech32
function encodeBech32(bytes) {
  const alphabet = "qpzry9x8gf2tvdw0s3jn54khce6mua7l";
  let value = 0;
  let checksum = 1;
  let combined = new Uint8Array(bytes.length + 2);
  combined.set(bytes, 0);
  combined.set([checksum >> 5, checksum << 3], bytes.length);
  let result = "";
  for (let i = 0; i < combined.length; ++i) {
    value = (value << 5) + combined[i];
  }
  for (let i = 0; i < combined.length * 8; i += 5) {
    result = alphabet[(value >> (35 - i)) & 0x1f] + result;
  }
  return result;
}

//  // Generate base58 and bech32 addresses
//  const base58Address = generateBase58Address(publicKey);
//  const bech32Address = encodeBech32(publicKey);

//  return { base58Address, bech32Address };
// }

// 1. ASM to ScriptPub Conversion and Address Check
function validateAddress(transaction) {
  const { scriptPubKeyHex, expectedAddress } = transaction;
  const { base58Address, bech32Address } =
    convertScriptPubKeyToAddress(scriptPubKeyHex);

  return expectedAddress === base58Address || expectedAddress === bech32Address;
}

// const transaction = {
//     scriptPubKeyHex: "6085312a9c500ff9cc35b571b0a1e5efb7fb9f16",
//     expectedAddress: "13VAhE9YkDwvMdRB85fm3y3xzLWq8ZcUfJ"
// };

// console.log(validateAddress(transaction));

// 2. Remove Dust Transactions and Double Spending
function removeDustAndDoubleSpending(transactions) {
  const dustThreshold = 546; // Minimum amount for an output to be considered not dust

  // Step 1: Filter out dust transactions
  const filteredTransactions = transactions.filter((transaction) => {
    // Check if any output is below the dust threshold
    const isDust = transaction.vout.some(
      (output) => output.value < dustThreshold
    );
    return !isDust;
  });

  // Step 2: Remove double spending
  const spentOutputs = new Set();

  // Iterate through filtered transactions to remove double spending
  const filteredTransactionsWithoutDoubleSpending = [];
  for (const transaction of filteredTransactions) {
    let isDoubleSpent = false;

    // Check each input to see if it's already spent
    for (const input of transaction.vin) {
      const key = `${input.txid}:${input.vout}`;
      if (spentOutputs.has(key)) {
        isDoubleSpent = true;
        break;
      }
    }

    // If not double spent, add to filteredTransactionsWithoutDoubleSpending and update spentOutputs
    if (!isDoubleSpent) {
      filteredTransactionsWithoutDoubleSpending.push(transaction);

      // Update spentOutputs with this transaction's inputs
      transaction.vin.forEach((input) => {
        const key = `${input.txid}:${input.vout}`;
        spentOutputs.add(key);
      });
    }
  }

  // Check if any transactions were filtered
  const isFiltered =
    filteredTransactionsWithoutDoubleSpending.length !== transactions.length;
  return isFiltered;
}

// 3. Script Validations
function validateScripts(transaction) {
  // Step 1: Validate redeem scripts and their corresponding H160
  const isRedeemScriptValid = validateRedeemScripts(transaction);

  // Step 2: Validate witnesses (if applicable)
  const isWitnessValid = validateWitnesses(transaction);

  // Return true if all validations pass, false otherwise
  return isRedeemScriptValid && isWitnessValid;
}

// Function to validate redeem scripts and their corresponding H160
function validateRedeemScripts(transaction) {
  // Iterate over each input and validate the redeem script and its H160
  for (const input of transaction.vin) {
    const redeemScript = input.redeemScript;
    const expectedH160 = input.expectedH160; // Assuming this is provided for comparison

    // Validate redeem script and its corresponding H160
    // Implement your validation logic here
    // Return false if any validation fails
    // For simplicity, assuming validation passes if redeemScript is not empty and expectedH160 matches
    if (
      !redeemScript ||
      redeemScript.length === 0 ||
      redeemScript !== expectedH160
    ) {
      return false;
    }
  }

  // If all redeem scripts and their corresponding H160s are valid, return true
  return true;
}

// validate witnesses
function validateWitnesses(transaction) {
  // Check if witnesses are present in the transaction
  if (!transaction.witness) {
    // No witnesses to validate
    return true;
  }

  // Iterate over each witness and validate its correctness
  for (const witness of transaction.witness) {
    // Implement your validation logic for witnesses
    // For simplicity, assuming validation passes if witness is not empty
    if (!witness || witness.length === 0) {
      return false;
    }
  }

  // If all witnesses are valid, return true
  return true;
}

// 4. Signature Extraction and Verification
function validateSignatures(transaction) {
  // Step 1: Extract signatures from P2PKH and P2WPKH scripts
  const signatures = extractSignatures(transaction);

  // Step 2: Perform ECDSA signature verification
  const isValidSignature = verifySignatures(transaction, signatures);

  // Return true if all signatures are valid, false otherwise
  return isValidSignature;
}

// Function to extract signatures from P2PKH and P2WPKH scripts
function extractSignatures(transaction) {
  const signatures = [];

  // Iterate over inputs and extract signatures from P2PKH and P2WPKH scripts
  for (const input of transaction.vin) {
    const scriptSig = input.scriptSig;
    const witness = input.witness;

    // Extract signature from scriptSig (P2PKH)
    if (scriptSig && scriptSig.length > 0) {
      // Assuming signature is the first element of scriptSig
      signatures.push(scriptSig[0]);
    }

    // Extract signature from witness (P2WPKH)
    if (witness && witness.length > 0) {
      // Assuming signature is the first element of witness
      signatures.push(witness[0]);
    }
  }

  return signatures;
}

// perform ECDSA signature verification
function verifySignatures(transaction, signatures) {
  // Iterate over inputs and perform signature verification
  for (let i = 0; i < transaction.vin.length; i++) {
    const input = transaction.vin[i];
    const publicKey = input.publicKey; // Assuming publicKey is provided for signature verification
    const scriptPubKey = input.scriptPubKey; // Assuming scriptPubKey is provided for signature verification

    // Convert signature, public key, and message to buffers
    const signatureBuffer = Buffer.from(signatures[i], "hex");
    const publicKeyBuffer = Buffer.from(publicKey, "hex");
    const messageBuffer = Buffer.from(scriptPubKey, "hex"); // Assuming scriptPubKey is the message

    // Verify signature using secp256k1 library
    const isValidSignature = secp256k1.ecdsaVerify(
      signatureBuffer,
      messageBuffer,
      publicKeyBuffer
    );

    // If any signature is invalid, return false
    if (!isValidSignature) {
      return false;
    }
  }

  // If all signatures are valid, return true
  return true;
}

// Block Header
class BlockHeader {
  constructor(prevBlockHash, merkleRoot, timestamp, nonce) {
    this.version = Buffer.from([0x00, 0x00, 0x00, 0x00]); // version 4 bytes
    this.prevBlockHash = Buffer.from(prevBlockHash, "hex"); // previous block 32 bytes
    this.merkleRoot = Buffer.from(merkleRoot, "hex"); // merkle root 32 bytes
    this.timestamp = Buffer.alloc(4); // time 4 bytes
    this.timestamp.writeUInt32LE(timestamp, 0);
    this.bits = Buffer.alloc(4); // bits 4 bytes
    this.bits.writeUInt32LE(0x1d00ffff, 0); // difficulty target
    this.nonce = Buffer.alloc(4); // nonce 4 bytes
    this.nonce.writeUInt32LE(nonce, 0);
  }

  serialize() {
    return Buffer.concat([
      this.version,
      this.prevBlockHash,
      this.merkleRoot,
      this.timestamp,
      this.bits,
      this.nonce,
    ]).toString("hex");
  }

  hash() {
    const header = this.serialize();
    return crypto.createHash("sha256").update(header, "hex").digest("hex");
  }
}

// Coinbase Transaction (needs to be corrected)
class CoinbaseTransaction {
  constructor(coinbaseData, recipientAddress) {
    this.coinbaseData = coinbaseData;
    this.recipientAddress = recipientAddress;
  }

  serialize() {
    return JSON.stringify({
      coinbaseData: this.coinbaseData,
      recipientAddress: this.recipientAddress,
    });
  }
}

// mine a block
function mineBlock(transactions) {
  const coinbaseTransaction = new CoinbaseTransaction(
    "Coinbase data",
    "Recipient address"
  );
  const coinbaseTxId = crypto
    .createHash("sha256")
    .update(coinbaseTransaction.serialize())
    .digest("hex");

  const merkleRoot = calculateMerkleRoot([coinbaseTxId, ...transactions]);
  const timestamp = Math.floor(Date.now() / 1000);

  let nonce = 0;
  let blockHeader;

  while (true) {
    const prevBlockHash = crypto.randomBytes(32).toString("hex"); // Generate a random hash for previous block
    blockHeader = new BlockHeader(prevBlockHash, merkleRoot, timestamp, nonce);
    const hash = blockHeader.hash();
    if (hash < blockHeader.difficultyTarget) {
      break;
    }
    nonce++;
  }

  const serializedCoinbaseTransaction = coinbaseTransaction.serialize();
  const blockHeaderString = blockHeader.serialize();

  const txIds = [
    coinbaseTxId,
    ...transactions.map((transaction) => transaction.txid),
  ];

  const outputData = `${blockHeaderString}\n${serializedCoinbaseTransaction}\n${txIds.join(
    "\n"
  )}`;

  writeOutputToFile(outputData);
}

// validate all transactions
function validateTransactions(transactions) {
  for (const transaction of transactions) {
    if (!validateAddress(transaction)) {
      console.log(`Transaction ${transaction.txid} has invalid address.`);
      return false;
    }
    if (!removeDustAndDoubleSpending([transaction])) {
      console.log(
        `Transaction ${transaction.txid} is either dust or double spending.`
      );
      return false;
    }
    if (!validateScripts(transaction)) {
      console.log(`Transaction ${transaction.txid} has invalid scripts.`);
      return false;
    }
    if (!validateSignatures(transaction)) {
      console.log(`Transaction ${transaction.txid} has invalid signatures.`);
      return false;
    }
  }
  return true;
}

// Read transactions from mempool folder
const transactions = readMempool();

// Validate all transactions
if (validateTransactions(transactions)) {
  // Mine the block with transactions
  mineBlock(transactions);
} else {
  console.log("Failed to validate transactions. Block mining aborted.");
}

// calculate Merkle Root
function calculateMerkleRoot(transactions) {
  const transactionData = transactions.map((transaction) =>
    JSON.stringify(transaction)
  ); // Serialize entire transaction object to JSON string

  const hashes = transactionData.map((data) =>
    crypto.createHash("sha256").update(data).digest("hex")
  );

  while (hashes.length > 1) {
    const newHashes = [];
    for (let i = 0; i < hashes.length; i += 2) {
      const leftHash = hashes[i];
      const rightHash = i + 1 < hashes.length ? hashes[i + 1] : "";
      const combinedHash = crypto
        .createHash("sha256")
        .update(leftHash + rightHash)
        .digest("hex");
      newHashes.push(combinedHash);
    }
    hashes.splice(0, hashes.length, ...newHashes);
  }

  return hashes[0];
}

// write data to output.txt
function writeOutputToFile(data) {
  fs.writeFileSync("output.txt", data);
}

// Mine the block with transactions
mineBlock(transactions);
