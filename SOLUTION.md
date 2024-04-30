# Documentation

## Design and Implementation Approach:

Here's how I put together the block construction code:

1. **Processing Transactions**:

   - I gathered transaction data from files in the mempool folder and combined them into one file called `total-mempool.json`.

   ```python
   def get_fee(transaction):

   def pre_process_transaction(transaction):

   def read_transaction_file(filename):
   ```

2. **Validating Transactions**:

   Four types of validations are implemented:

   - **ASM to ScriptPub Conversion and Address Check**: Transactions undergo conversion from ASM format to ScriptPub format, and the associated addresses are verified for correctness.
   - **Removal of Dust Transactions and Prevention of Double Spending**: Dust transactions, which have minimal value and can clutter the blockchain, are filtered out. Measures are also taken to prevent double spending, ensuring each transaction is unique.
   - **Script Validations**: The scripts within transactions are validated to ensure they adhere to scripting rules and do not contain any anomalies.
   - **Extraction of Signatures and ECDSA Signature Verification**: Signatures are extracted from transactions, and ECDSA signature verification (done using coincurve library) is performed to validate the authenticity of transactions.
     </br>

   A final validation function consolidates the results of all four validation processes, ensuring that each transaction meets the necessary criteria before inclusion in the block.

   ```python
   def segwit_txn_data(txn_id):
   def legacy_txn_data(txn_id):
   def validate_p2pkh_txn(signature, pubkey, scriptpubkey_asm, txn_data):

   def to_hash160(hex_input):
   def validate_p2sh_txn_basic(inner_redeemscript_asm, scriptpubkey_asm):
   def validate_p2sh_txn_adv(inner_redeemscript_asm, scriptpubkey_asm, scriptsig_asm, txn_data):

   def segwit_txn_data(txn_id):
   def validate_p2wpkh_txn(witness, wit_scriptpubkey_asm, txn_data):
   ```

After performing all the validations, I created a separate file named `valid-mempool.json` to store the validated transactions, thereby increasing efficiency.

3. **Block Header Creation**:

   - Once the transactions are validated, the program proceeds to create a block header for the mined block.
   - The block header comprises essential information, including the block version, previous block hash, Merkle root hash, timestamp, difficulty target, and nonce.
   - To calculate the Merkle root hash, a Merkle tree is constructed from the transaction data, and the root hash is derived using double SHA-256 hashing.
   - Serialization of transactions is performed to ensure they are properly formatted and can be included in the block header.
     Some utilities used for calculation:

   ```python
   def calculate_compact_size(value):

   def convert_to_little_endian(num, size):

   def reverse_bytes(hex_input):

   def hash256(hex_input):

   def generate_merkle_root(txids):

   def calculate_total_weight_and_fee(transactions):
   ```

4. **Mining the Block**:

   - The final step involves mining the block by finding a nonce value that satisfies the specified target difficulty. (with the goal of finding a nonce that results in a block hash lower than the target difficulty)
   - The code iteratively adjusts the nonce value and hashes the block header until a valid nonce is discovered.

   ```python
   def mine_block(transactions):

   def validate_block(coinbase_tx, txids, transactions):
   ```

I structured the `output.txt` file to adhere to specific formatting requirements, ensuring clarity and ease of interpretation. The file follows a structured order as outlined below:

1. **Block Header**: The block header, containing vital information such as version, timestamp, Merkle root hash, and nonce, is placed at the beginning of the file.

   ```python
   def generate_merkle_root(txids):

   def target_to_bits(target):

   ```

2. **Serialized Coinbase Transaction**: Following the block header, the serialized coinbase transaction is included. This transaction marks the creation of new bitcoins and includes collected transaction fees.

   ```python
   def serialize_coinbase_transaction(witness_commitment):

   def calculate_witness_commitment(transactions):

   def verify_witness_commitment(coinbase_tx, witness_commitment):
   ```

3. **Transaction IDs in Order**: Finally, the file lists the transaction IDs in the order they appear in the block. It is ensured that the first ID corresponds to the coinbase transaction ID.

By structuring the `output.txt` file in this manner, it adheres to the specified format guidelines, facilitating seamless interpretation and analysis of the mined block's content.

```python
def main():
```

That's how I built the whole program step by step, making sure each part worked before moving on to the next.

## Challenges:

As a beginner, working on this project had some tough parts. I didn't know much about working with the validation part, serialisation, building block headers, figuring out the Merkle root. Also, since we had to make everything from scratch without using any ready-made tools/libraries, it made things harder.

I found some helpful resources like the "Grokking Bitcoin" and "Mastering Bitcoin 3.0" book and YouTube videos including SoB that explained things well. Websites like learnmeabitcoin.com and blockchain.com also gave me useful information. I was also a part of Chaincode Learning Program of BitShala which helped me a lot.

Another challenge was figuring out how to serialize transactions and validate them. Serialization is like putting data in a specific order, and it was tough to get it right. I had to make sure the transactions followed the rules, which involved lots of checking and verifying.

I also looked for help in online communities like Bitcoin Stack Exchange and SoB's server. They were great for clearing up any confusion and giving me extra tips.

Despite the tough parts, this project helped me learn a lot about Bitcoin. Going forward, I'll keep learning and exploring more advanced topics to get better at blockchain stuff.

## Results, Performance and Conclusion:

The performance of the solution can be analyzed based on various factors such as the number of transactions processed, the time taken to mine a block, and the validity of the resulting block. Also, efficiency can be evaluated in terms of memory usage and processing time.

One thing to note is that the highest score I got was 85%. I couldn't get higher because of some issues, like mistakes in figuring out the block weight. Maybe adding more checks could have helped, but I ran out of time.

Looking ahead, I could try to improve by making my checks better and trying different tools or languages. These changes might help me do even better next time.

In conclusion, the block construction program successfully processes transactions from the mempool, validates them, creates a block header, and mines a block and executes them as asked in output.txt format.

It was a great learning experience overall, and I'm excited to continue improving my skills in the future. I learned a lot about bitcoin and stuff.

## Learning Resources

As a part-time crypto trader, diving into the world of Bitcoin development has been a rewarding journey, one that I don't regret. Here are some of the resources that proved invaluable in completing this assignment and expanding my knowledge:

- [Learn me a Bitcoin](https://learnmeabitcoin.com/)

- [Bitcoin Stack Exchange](https://bitcoin.stackexchange.com/)

- [Bitcoin Book (3rd Edition)](https://github.com/bitcoinbook/bitcoinbook)

- [Grokking Bitcoin](https://rosenbaum.se/book/grokking-bitcoin.html)

- [Mempool.space](https://mempool.space/)

- [Blockchain.com](https://www.blockchain.com/)

- [Bitcoin.it](https://en.bitcoin.it/wiki)

- [Bitcoin.com](https://www.bitcoin.com/get-started/)

I also recommend considering joining the Chaincode Labs Cohort, as it offers a similar program focused on one month of learning and continued growth in the Bitcoin development space.
