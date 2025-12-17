# BlockProof Django Backend Architecture

## Overview

The Django backend serves as a cost-optimized bridge between your frontend and the BlockProof smart contract. It minimizes blockchain interaction costs by caching all on-chain data locally and using event indexing instead of polling.

## Architecture Diagram

```
┌─────────────┐
│   Frontend  │
│  (React/UI) │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────────────────────────────┐
│      Django REST API                │
│  ┌──────────┐  ┌──────────┐        │
│  │Credentials│  │Institutions│      │
│  │   API    │  │    API    │        │
│  └──────────┘  └──────────┘        │
└──────┬──────────────────┬───────────┘
       │                  │
       │ Reads            │ Writes
       ▼                  ▼
┌──────────────┐   ┌──────────────┐
│   Database   │   │  Web3 Service│
│  (PostgreSQL)│   │  (Write Only)│
│              │   └──────┬───────┘
│  - Credentials          │
│  - Institutions         │
│  - Events               │
└──────┬──────────────────┘
       │
       │ Event Indexer (Celery)
       │ Syncs blockchain → DB
       ▼
┌─────────────────────┐
│  Smart Contract     │
│  (Blockchain)       │
└─────────────────────┘
```

## Key Components

### 1. Django Apps

#### `blockchain/`
- **Purpose**: Blockchain integration layer
- **Key Files**:
  - `services.py`: Web3 service for contract interaction
  - `models.py`: Event caching models
  - `tasks.py`: Celery tasks for event indexing
  - `sync_handlers.py`: Syncs events to credential models

#### `credentials/`
- **Purpose**: Credential management
- **Key Files**:
  - `models.py`: Credential model (cached from blockchain)
  - `views.py`: REST API endpoints
  - `serializers.py`: API serialization

#### `institutions/`
- **Purpose**: Institution management
- **Key Files**:
  - `models.py`: Institution model
  - `views.py`: REST API endpoints

### 2. Cost Optimization Strategy

#### Event Indexing (Primary Optimization)
- **Problem**: Polling blockchain for every request is expensive
- **Solution**: Background task syncs events to database
- **Result**: 99% reduction in RPC calls

**How it works**:
1. Celery beat runs every 60 seconds
2. Fetches new events since last sync
3. Stores events in database
4. Syncs events to credential/institution models
5. API reads from database (fast & free)

#### Caching Strategy
- All blockchain data cached in PostgreSQL
- Read operations use database (no RPC calls)
- Write operations go directly to blockchain
- Event indexer keeps cache in sync

### 3. Data Flow

#### Reading Credentials (Free)
```
User Request → Django API → Database → Response
```
No blockchain interaction needed!

#### Writing Credentials (Costs Gas)
```
User Request → Django API → Web3 Service → Blockchain
                                    ↓
                            Transaction Hash
                                    ↓
                            Event Indexer (async)
                                    ↓
                            Database (updated)
```

#### Event Indexing (Background)
```
Celery Beat → Fetch Events → Process Events → Update Database
```

## API Endpoints

### Credentials
- `GET /api/credentials/` - List credentials (from cache)
- `GET /api/credentials/{id}/` - Get credential (from cache)
- `POST /api/credentials/issue/` - Issue credential (blockchain write)
- `POST /api/credentials/{id}/revoke/` - Revoke credential (blockchain write)

### Blockchain
- `POST /api/blockchain/verify/` - Verify fingerprint (cache first, blockchain fallback)
- `GET /api/blockchain/status/{id}/` - Get status (cache first, blockchain fallback)

### Institutions
- `GET /api/institutions/` - List institutions (from cache)
- `GET /api/institutions/{address}/` - Get institution (from cache)

## Database Schema

### Credential
- Cached from `CredentialIssued` events
- Updated by `CredentialRevoked` events
- Indexed on `credential_id`, `student_wallet`, `fingerprint`

### Institution
- Cached from `InstitutionUpserted` events
- Indexed on `address`

### BlockchainEvent Models
- `CredentialIssuedEvent`: Raw event data
- `CredentialRevokedEvent`: Raw event data
- `IndexerState`: Tracks last processed block

## Background Tasks

### Event Indexer (`index_blockchain_events`)
- **Frequency**: Every 60 seconds (configurable)
- **Process**:
  1. Get last processed block
  2. Fetch new events from blockchain
  3. Store events in database
  4. Sync to credential/institution models
  5. Update last processed block

## Cost Breakdown

### Development (Free)
- Testnet: Free
- Free RPC tier: 100k+ requests/day
- Local database: Free
- **Total: $0/month**

### Production (Optimized)
- L2 network: ~$0.01-0.10 per transaction
- RPC calls: Free tier (100k/day)
- Hosting: $5-20/month
- Database: Included or $5/month
- **Total: ~$10-25/month**

### Without Optimization
- Mainnet: ~$5-50 per transaction
- RPC calls: $0.001 per call
- 1000 verifications/day = $1/day = $30/month
- **Total: $50-100+/month**

**Savings: 60-80% cost reduction**

## Security Considerations

1. **Private Keys**: Stored in environment variables, never in code
2. **Read Operations**: No authentication needed (public data)
3. **Write Operations**: Should add authentication/authorization
4. **Rate Limiting**: Should be added for production
5. **Input Validation**: All inputs validated via serializers

## Scalability

### Current Setup
- Handles 1000s of credentials
- Processes events in batches
- Database indexes for fast queries

### Scaling Up
- Add read replicas for database
- Horizontal scaling of Celery workers
- CDN for static assets
- Load balancer for API

## Monitoring

### Key Metrics
- Event indexer lag (should be < 5 minutes)
- RPC call count (stay within free tier)
- Database size
- API response times
- Gas costs per transaction

### Alerts
- Event indexer failing
- RPC quota approaching limit
- High database size
- API errors

## Next Steps

1. **Immediate**: Deploy contract, configure `.env`, run migrations
2. **Short-term**: Add authentication, rate limiting, monitoring
3. **Long-term**: Add webhooks, analytics, batch operations

See [NEXT_STEPS.md](./NEXT_STEPS.md) for detailed implementation guide.

