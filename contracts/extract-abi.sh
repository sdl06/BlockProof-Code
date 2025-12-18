#!/bin/bash
# Bash script to extract ABI from Hardhat artifacts
# Usage: ./extract-abi.sh

ARTIFACT_PATH="artifacts/contracts/BlockProofCredentialVault.sol/BlockProofCredentialVault.json"
OUTPUT_PATH="../backend/blockchain/contract_abi.json"

if [ -f "$ARTIFACT_PATH" ]; then
    echo "Extracting ABI from $ARTIFACT_PATH..."
    cat "$ARTIFACT_PATH" | jq .abi > "$OUTPUT_PATH"
    echo "✅ ABI extracted to $OUTPUT_PATH"
else
    echo "❌ Error: Artifact not found at $ARTIFACT_PATH"
    echo "Make sure you've compiled the contract first: npm run compile"
    exit 1
fi














