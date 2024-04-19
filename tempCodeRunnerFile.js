// Function to calculate Merkle Root
function calculateMerkleRoot(transactions) {
    const transactionData = transactions.map(transaction => JSON.stringify(transaction)); // Serialize entire transaction object to JSON string

    const hashes = transactionData.map(data => crypto.createHash('sha256').update(data).digest('hex'));

    while (hashes.length > 1) {
        const newHashes = [];
        for (let i = 0; i < hashes.length; i += 2) {
            const leftHash = hashes[i];
            const rightHash = (i + 1 < hashes.length) ? hashes[i + 1] : '';
            const combinedHash = crypto.createHash('sha256').update(leftHash + rightHash).digest('hex');
            newHashes.push(combinedHash);
        }
        hashes.splice(0, hashes.length, ...newHashes);
    }

    return hashes[0];
}
