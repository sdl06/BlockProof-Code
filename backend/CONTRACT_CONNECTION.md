# How Django Backend Connects to BlockProofCredentialVault Contract

This document explains the technical connection between your Django backend and the Solidity smart contract.

## Overview

The connection happens through **Web3.py**, a Python library that allows Python code to interact with Ethereum-compatible blockchains. Here's the flow:

```
Django Backend → Web3.py → RPC Node → Blockchain → Smart Contract
```

## Connection Components

### 1. **Web3.py Library** (`web3==6.11.3`)

Web3.py is the bridge between Python and the blockchain. It:
- Connects to blockchain nodes via RPC (HTTP)
- Encodes/decodes function calls
- Handles transaction signing
- Listens to blockchain events

### 2. **RPC Endpoint** (Infura, Alchemy, etc.)

An RPC (Remote Procedure Call) endpoint is your gateway to the blockchain:
- **Infura**: `https://sepolia.infura.io/v3/YOUR_KEY`
- **Alchemy**: `https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY`
- **Public RPC**: `https://rpc.sepolia.org` (free but slower)

### 3. **Contract Address**

After deploying your contract, you get an address like:
```
0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

This is where your contract lives on the blockchain.

### 4. **Contract ABI** (Application Binary Interface)

The ABI is a JSON file that describes:
- What functions the contract has
- What parameters they take
- What they return
- What events they emit

**Example ABI entry for `credentialStatus` function:**
```json
{
  "inputs": [{"internalType": "uint256", "name": "credentialId", "type": "uint256"}],
  "name": "credentialStatus",
  "outputs": [{
    "components": [
      {"internalType": "bool", "name": "exists", "type": "bool"},
      {"internalType": "bool", "name": "valid", "type": "bool"},
      ...
    ],
    "type": "tuple"
  }],
  "stateMutability": "view",
  "type": "function"
}
```

## Code Walkthrough

### Step 1: Initialize Web3 Connection

In `blockchain/services.py`, the `BlockProofService` class initializes the connection:

```python
def __init__(self):
    config = settings.BLOCKCHAIN_CONFIG
    self.rpc_url = config['RPC_URL']  # e.g., "https://sepolia.infura.io/v3/..."
    self.contract_address = config['CONTRACT_ADDRESS']  # e.g., "0x742d35..."
    
    # 1. Connect to blockchain via RPC
    self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
    
    # 2. Load contract ABI (describes contract functions)
    self.contract_abi = self._load_contract_abi()
    
    # 3. Create contract instance
    self.contract = self.w3.eth.contract(
        address=Web3.to_checksum_address(self.contract_address),
        abi=self.contract_abi
    )
```

**What happens:**
- `Web3(Web3.HTTPProvider(...))` creates a connection to the blockchain node
- `w3.eth.contract(...)` creates a Python object that represents your contract
- The ABI tells Web3.py how to encode/decode function calls

### Step 2: Read from Contract (Free, No Gas)

**Example: Getting credential status**

**Solidity Contract Function:**
```solidity
function credentialStatus(uint256 credentialId) 
    external view 
    returns (CredentialStatus memory) {
    // Returns credential data
}
```

**Django Backend Call:**
```python
def get_credential_status(self, credential_id: int):
    # Call the contract function (read-only, no transaction)
    result = self.contract.functions.credentialStatus(credential_id).call()
    
    # result is a tuple matching the Solidity return type
    return {
        'exists': result[0],      # bool
        'valid': result[1],       # bool
        'revoked': result[2],     # bool
        'fingerprint': result[3].hex(),  # bytes32 → hex string
        'student_wallet': result[4],     # address
        'institution': result[5],        # address
        'issued_at': result[6],          # uint64
        'expires_at': result[7],         # uint64
        'revoked_at': result[8],         # uint64
    }
```

**What happens behind the scenes:**
1. Web3.py encodes `credential_id` according to the ABI
2. Sends RPC call: `eth_call` to contract address
3. Contract executes function (read-only, no state change)
4. Returns result
5. Web3.py decodes result according to ABI
6. Returns Python data structure

**Cost:** FREE (read-only operations don't cost gas)

### Step 3: Write to Contract (Costs Gas)

**Example: Issuing a credential**

**Solidity Contract Function:**
```solidity
function issueCredential(
    IssueCredentialRequest calldata request
) external whenNotPaused returns (uint256 newCredentialId) {
    // Creates new credential on-chain
    emit CredentialIssued(...);
}
```

**Django Backend Call:**
```python
def issue_credential(self, institution, student_wallet, fingerprint, ...):
    # 1. Prepare the function call
    request = (
        Web3.to_checksum_address(institution),
        Web3.to_checksum_address(student_wallet),
        bytes.fromhex(fingerprint.replace('0x', '')),
        metadata_uri,
        encrypted_payload_uri,
        expires_at
    )
    
    # 2. Build transaction (doesn't send yet)
    transaction = self.contract.functions.issueCredential(request).build_transaction({
        'from': self.account.address,
        'nonce': self.w3.eth.get_transaction_count(self.account.address),
        'gas': 200000,
        'gasPrice': self.w3.eth.gas_price,
    })
    
    # 3. Sign transaction with private key
    signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
    
    # 4. Send transaction to blockchain
    tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    return tx_hash.hex()  # Returns transaction hash
```

**What happens behind the scenes:**
1. Web3.py encodes function call and parameters
2. Builds a transaction object
3. Signs it with your private key (proves you own the account)
4. Sends transaction via RPC: `eth_sendRawTransaction`
5. Transaction is mined into a block
6. Contract function executes
7. State changes are permanent on blockchain
8. Event is emitted (can be listened to later)

**Cost:** Gas fees (varies by network, ~$0.01-5 per transaction)

### Step 4: Listening to Events

**Example: CredentialIssued Event**

**Solidity Event:**
```solidity
event CredentialIssued(
    uint256 indexed credentialId,
    address indexed studentWallet,
    address indexed institution,
    bytes32 fingerprint,
    string metadataURI,
    string encryptedPayloadURI,
    uint64 expiresAt
);
```

**Django Backend Event Listener:**
```python
def get_events(self, event_name: str, from_block: int, to_block: int):
    # Get event logs from blockchain
    event = getattr(self.contract.events, event_name)  # e.g., "CredentialIssued"
    events = event.get_logs(fromBlock=from_block, toBlock=to_block)
    
    return [dict(event) for event in events]
```

**What happens:**
1. Web3.py queries blockchain for event logs
2. Filters by contract address and event signature
3. Decodes event data according to ABI
4. Returns list of events

**Used by:** Event indexer (Celery task) to sync blockchain events to database

## Complete Connection Flow

### Reading a Credential

```
1. API Request: GET /api/blockchain/status/123/
   ↓
2. Django View: credential_status(request, 123)
   ↓
3. Try Database Cache First (fast, free)
   ↓ (if not found)
4. BlockProofService.get_credential_status(123)
   ↓
5. Web3: contract.functions.credentialStatus(123).call()
   ↓
6. RPC Call: eth_call to contract address
   ↓
7. Blockchain Node executes function
   ↓
8. Returns result
   ↓
9. Web3 decodes result
   ↓
10. Django returns JSON response
```

### Issuing a Credential

```
1. API Request: POST /api/credentials/issue/
   ↓
2. Django View: issue_credential(request)
   ↓
3. BlockProofService.issue_credential(...)
   ↓
4. Web3: Build transaction
   ↓
5. Sign transaction with private key
   ↓
6. RPC Call: eth_sendRawTransaction
   ↓
7. Transaction mined into block
   ↓
8. Contract function executes
   ↓
9. Event CredentialIssued emitted
   ↓
10. Event Indexer (Celery) picks up event
   ↓
11. Event synced to database
   ↓
12. API returns transaction hash
```

## Configuration

All connection settings are in `settings.py`:

```python
BLOCKCHAIN_CONFIG = {
    'RPC_URL': 'https://sepolia.infura.io/v3/YOUR_KEY',  # Blockchain node
    'CONTRACT_ADDRESS': '0x742d35...',                    # Your contract
    'CHAIN_ID': 11155111,                                 # Sepolia testnet
    'PRIVATE_KEY': '0x...',                               # For write ops
}
```

Set these in your `.env` file:
```bash
RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
CONTRACT_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
CHAIN_ID=11155111
PRIVATE_KEY=0x...
```

## Contract Function Mapping

| Solidity Function | Django Method | Type | Cost |
|------------------|---------------|------|------|
| `credentialStatus(uint256)` | `get_credential_status()` | Read | Free |
| `verifyFingerprint(uint256, bytes32)` | `verify_fingerprint()` | Read | Free |
| `issueCredential(request)` | `issue_credential()` | Write | Gas |
| `revokeCredential(uint256, bytes32)` | `revoke_credential()` | Write | Gas |
| `CredentialIssued` event | `get_events('CredentialIssued')` | Event | Free* |

*Event queries are free but can be slow for large ranges

## Key Points

1. **ABI is Essential**: Without the ABI, Web3.py doesn't know how to call your contract functions
2. **Reads are Free**: View functions don't cost gas
3. **Writes Cost Gas**: State-changing functions require gas fees
4. **Events for Syncing**: Use events to keep database in sync (cost optimization)
5. **RPC is the Gateway**: All communication goes through an RPC endpoint

## Troubleshooting

### "Contract not configured"
- Check `CONTRACT_ADDRESS` is set in `.env`
- Verify contract is deployed at that address

### "RPC errors"
- Check `RPC_URL` is correct
- Verify you're within free tier limits
- Test connection: `w3.eth.block_number` should return a number

### "Function not found"
- Verify ABI includes the function
- Check function name matches exactly (case-sensitive)
- Ensure contract address is correct

### "Insufficient funds"
- Write operations need ETH for gas
- Check account balance: `w3.eth.get_balance(account.address)`

## Next Steps

1. **Deploy Contract**: Get contract address
2. **Get ABI**: Extract from compiled contract JSON
3. **Configure `.env`**: Set RPC_URL, CONTRACT_ADDRESS, etc.
4. **Test Connection**: Try a read operation first
5. **Test Write**: Issue a test credential

See `NEXT_STEPS.md` for detailed instructions.
























