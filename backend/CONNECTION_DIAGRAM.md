# Connection Diagram: Django ↔ Smart Contract

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Django Backend                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   API Views  │→ │   Services   │→ │   Models     │     │
│  │  (REST API)  │  │  (Web3.py)   │  │  (Database)  │     │
│  └──────────────┘  └──────┬───────┘  └──────────────┘     │
│                           │                                 │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            │ HTTP/JSON-RPC
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    RPC Node (Infura/Alchemy)                 │
│  - Receives JSON-RPC requests                               │
│  - Executes on blockchain                                   │
│  - Returns results                                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ Blockchain Protocol
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ethereum Blockchain                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  BlockProofCredentialVault Contract                  │  │
│  │  Address: 0x742d35...                                │  │
│  │                                                       │  │
│  │  Functions:                                           │  │
│  │  - credentialStatus(uint256) → CredentialStatus      │  │
│  │  - verifyFingerprint(uint256, bytes32) → bool        │  │
│  │  - issueCredential(request) → uint256                │  │
│  │  - revokeCredential(uint256, bytes32)                │  │
│  │                                                       │  │
│  │  Events:                                              │  │
│  │  - CredentialIssued(...)                             │  │
│  │  - CredentialRevoked(...)                            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Detailed Read Operation Flow

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │
       │ GET /api/blockchain/status/123/
       ▼
┌─────────────────────────────────────┐
│  Django View: credential_status()   │
│  - Receives credential_id = 123     │
└──────┬──────────────────────────────┘
       │
       │ Try cache first
       ▼
┌─────────────────────────────────────┐
│  Database Query                     │
│  Credential.objects.get(id=123)     │
└──────┬──────────────────────────────┘
       │
       │ Not found? Fallback to blockchain
       ▼
┌─────────────────────────────────────┐
│  BlockProofService                  │
│  get_credential_status(123)         │
└──────┬──────────────────────────────┘
       │
       │ Python call
       ▼
┌─────────────────────────────────────┐
│  Web3.py Contract Instance          │
│  contract.functions                 │
│    .credentialStatus(123)           │
│    .call()                          │
└──────┬──────────────────────────────┘
       │
       │ Encodes: function signature + parameters
       │ Creates JSON-RPC request
       ▼
┌─────────────────────────────────────┐
│  RPC Request (HTTP POST)            │
│  {                                   │
│    "method": "eth_call",            │
│    "params": [{                     │
│      "to": "0x742d35...",           │
│      "data": "0x1234abcd..."        │
│    }, "latest"]                     │
│  }                                   │
└──────┬──────────────────────────────┘
       │
       │ HTTP POST to RPC endpoint
       ▼
┌─────────────────────────────────────┐
│  Blockchain Node                    │
│  - Executes function (read-only)    │
│  - No state change                  │
│  - Returns encoded result           │
└──────┬──────────────────────────────┘
       │
       │ JSON-RPC Response
       │ { "result": "0x5678ef..." }
       ▼
┌─────────────────────────────────────┐
│  Web3.py                            │
│  - Decodes result using ABI         │
│  - Converts to Python types         │
│  - Returns tuple/dict               │
└──────┬──────────────────────────────┘
       │
       │ Python dict
       ▼
┌─────────────────────────────────────┐
│  Django View                        │
│  - Formats as JSON                  │
│  - Returns HTTP response            │
└──────┬──────────────────────────────┘
       │
       │ JSON Response
       ▼
┌─────────────┐
│   Client    │
│  Receives:  │
│  {          │
│    "exists": true,                  │
│    "valid": true,                   │
│    ...                              │
│  }                                   │
└─────────────┘
```

## Detailed Write Operation Flow

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │
       │ POST /api/credentials/issue/
       │ { institution, student_wallet, ... }
       ▼
┌─────────────────────────────────────┐
│  Django View: issue_credential()    │
│  - Validates input                  │
└──────┬──────────────────────────────┘
       │
       │
       ▼
┌─────────────────────────────────────┐
│  BlockProofService                  │
│  issue_credential(...)              │
└──────┬──────────────────────────────┘
       │
       │ 1. Prepare function call
       ▼
┌─────────────────────────────────────┐
│  Web3.py                            │
│  contract.functions                 │
│    .issueCredential(request)        │
│    .build_transaction({...})        │
│                                     │
│  Creates transaction object:        │
│  {                                   │
│    "to": "0x742d35...",            │
│    "data": "0xabcd1234...",        │
│    "gas": 200000,                   │
│    "gasPrice": 20000000000,         │
│    "nonce": 5                       │
│  }                                   │
└──────┬──────────────────────────────┘
       │
       │ 2. Sign transaction
       ▼
┌─────────────────────────────────────┐
│  Web3.py                            │
│  account.sign_transaction(tx, key)  │
│                                     │
│  Creates signed transaction:        │
│  {                                   │
│    ... (same as above)              │
│    "v": 27,                         │
│    "r": "0x...",                    │
│    "s": "0x..."                     │
│  }                                   │
└──────┬──────────────────────────────┘
       │
       │ 3. Send to blockchain
       ▼
┌─────────────────────────────────────┐
│  RPC Request (HTTP POST)            │
│  {                                   │
│    "method": "eth_sendRawTransaction",│
│    "params": ["0x1234abcd..."]      │
│  }                                   │
└──────┬──────────────────────────────┘
       │
       │ HTTP POST to RPC endpoint
       ▼
┌─────────────────────────────────────┐
│  Blockchain Node                    │
│  - Validates transaction            │
│  - Broadcasts to network            │
│  - Returns transaction hash         │
└──────┬──────────────────────────────┘
       │
       │ JSON-RPC Response
       │ { "result": "0x5678ef..." }
       ▼
┌─────────────────────────────────────┐
│  Transaction Mined                  │
│  - Miner includes in block          │
│  - Contract function executes       │
│  - State changes applied            │
│  - Event CredentialIssued emitted   │
└──────┬──────────────────────────────┘
       │
       │ Event appears in logs
       ▼
┌─────────────────────────────────────┐
│  Event Indexer (Celery Task)        │
│  - Queries for new events           │
│  - Processes CredentialIssued       │
│  - Updates database                 │
└──────┬──────────────────────────────┘
       │
       │ Database updated
       ▼
┌─────────────────────────────────────┐
│  Database                           │
│  Credential record created          │
│  - credential_id: 123               │
│  - student_wallet: 0x...            │
│  - institution: 0x...               │
│  - ...                              │
└─────────────────────────────────────┘
```

## Data Flow: Contract → Database

```
┌─────────────────────────────────────┐
│  Smart Contract                     │
│  - CredentialIssued event emitted   │
│  - Stored in blockchain logs        │
└──────┬──────────────────────────────┘
       │
       │ Every 60 seconds
       ▼
┌─────────────────────────────────────┐
│  Celery Beat (Scheduler)            │
│  Triggers: index_blockchain_events  │
└──────┬──────────────────────────────┘
       │
       │
       ▼
┌─────────────────────────────────────┐
│  Celery Worker                      │
│  index_blockchain_events()          │
└──────┬──────────────────────────────┘
       │
       │ 1. Get last processed block
       ▼
┌─────────────────────────────────────┐
│  IndexerState Model                 │
│  last_processed_block = 15000       │
└──────┬──────────────────────────────┘
       │
       │ 2. Query events
       ▼
┌─────────────────────────────────────┐
│  Web3.py                            │
│  contract.events.CredentialIssued   │
│    .get_logs(                       │
│      fromBlock=15001,               │
│      toBlock='latest'               │
│    )                                │
└──────┬──────────────────────────────┘
       │
       │ RPC: eth_getLogs
       ▼
┌─────────────────────────────────────┐
│  Blockchain Node                    │
│  Returns event logs                 │
└──────┬──────────────────────────────┘
       │
       │ Decoded events
       ▼
┌─────────────────────────────────────┐
│  Process Events                     │
│  For each CredentialIssued event:   │
│  - Save to CredentialIssuedEvent    │
│  - Sync to Credential model         │
└──────┬──────────────────────────────┘
       │
       │
       ▼
┌─────────────────────────────────────┐
│  Database                           │
│  - CredentialIssuedEvent created    │
│  - Credential record created        │
│  - IndexerState updated             │
└─────────────────────────────────────┘
```

## Key Components Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                    Django Application                        │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   Views      │─────→│  Services    │                    │
│  │  (API)       │      │  (Web3.py)   │                    │
│  └──────────────┘      └──────┬───────┘                    │
│         │                      │                            │
│         │                      │                            │
│         ▼                      ▼                            │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   Models     │←─────│   Tasks      │                    │
│  │  (Database)  │      │  (Celery)    │                    │
│  └──────────────┘      └──────┬───────┘                    │
│                                │                            │
└────────────────────────────────┼────────────────────────────┘
                                 │
                                 │ Web3 Connection
                                 │
                                 ▼
                    ┌──────────────────────┐
                    │   Blockchain Node    │
                    │   (via RPC)          │
                    └──────────────────────┘
                                 │
                                 │
                                 ▼
                    ┌──────────────────────┐
                    │  Smart Contract      │
                    │  (On Blockchain)     │
                    └──────────────────────┘
```

## Summary

1. **Web3.py** is the bridge between Python and blockchain
2. **RPC endpoint** provides access to blockchain nodes
3. **Contract ABI** tells Web3.py how to encode/decode calls
4. **Contract address** identifies your deployed contract
5. **Read operations** are free (no gas, no transactions)
6. **Write operations** cost gas (require signed transactions)
7. **Events** are used to sync blockchain state to database

The connection is **stateless** - each request creates a new connection, but Web3.py handles all the complexity of encoding, signing, and decoding.
























