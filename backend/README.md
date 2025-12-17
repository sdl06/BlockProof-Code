# BlockProof Django Backend

Django backend for BlockProof credential verification system. Optimized for cost-effective blockchain integration.

## Features

- ✅ **Event Indexing**: Automatically syncs blockchain events to local database
- ✅ **Cost Optimized**: Minimizes RPC calls through caching
- ✅ **REST API**: Full API for credential operations
- ✅ **Background Tasks**: Celery for async blockchain operations
- ✅ **Admin Interface**: Django admin for managing data

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Setup Database

```bash
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

### 6. Start Celery (for event indexing)

In a separate terminal:

```bash
# Start Redis first (if not running)
redis-server

# Start Celery worker
celery -A blockproof_backend worker -l info

# Start Celery beat (for scheduled tasks)
celery -A blockproof_backend beat -l info
```

## Project Structure

```
backend/
├── blockproof_backend/     # Django project settings
├── blockchain/             # Blockchain integration
│   ├── models.py          # Event caching models
│   ├── services.py        # Web3 service layer
│   ├── tasks.py           # Celery tasks for event indexing
│   └── views.py           # API views
├── credentials/            # Credential management
│   ├── models.py          # Credential models
│   ├── views.py           # Credential API
│   └── serializers.py     # API serializers
├── institutions/           # Institution management
│   ├── models.py          # Institution models
│   └── views.py           # Institution API
└── requirements.txt        # Python dependencies
```

## API Endpoints

### Credentials

- `GET /api/credentials/` - List all credentials
- `GET /api/credentials/{id}/` - Get credential details
- `POST /api/credentials/issue/` - Issue new credential (costs gas)
- `POST /api/credentials/{id}/revoke/` - Revoke credential (costs gas)

Query parameters:
- `?student_wallet=0x...` - Filter by student wallet
- `?institution=0x...` - Filter by institution
- `?valid_only=true` - Only show valid credentials

### Blockchain

- `POST /api/blockchain/verify/` - Verify credential fingerprint
- `GET /api/blockchain/status/{id}/` - Get credential status

### Institutions

- `GET /api/institutions/` - List all institutions
- `GET /api/institutions/{address}/` - Get institution details

## Cost Optimization

See [COST_OPTIMIZATION.md](./COST_OPTIMIZATION.md) for detailed strategies.

Key optimizations:
1. **Event Indexing**: Syncs blockchain events to database (minimizes RPC calls)
2. **Local Caching**: All reads come from database, not blockchain
3. **Batch Processing**: Events processed in batches
4. **Free RPC Tier**: Uses free tier from Infura/Alchemy

## Development

### Running Tests

```bash
python manage.py test
```

### Accessing Admin

1. Create superuser: `python manage.py createsuperuser`
2. Visit: http://localhost:8000/admin/

### Event Indexing

The event indexer runs automatically via Celery Beat. It:
- Processes new blockchain events every 60 seconds
- Caches events in database
- Updates credential and institution data

To manually trigger indexing:

```bash
python manage.py shell
>>> from blockchain.tasks import index_blockchain_events
>>> index_blockchain_events.delay()
```

## Deployment

### Production Checklist

1. Set `DEBUG=False` in `.env`
2. Use PostgreSQL (not SQLite)
3. Set up Redis for Celery
4. Configure proper `ALLOWED_HOSTS`
5. Use production RPC endpoint
6. Set up monitoring for event indexer
7. Configure backups for database

### Environment Variables

Required for production:
- `SECRET_KEY`
- `DATABASE_URL`
- `RPC_URL`
- `CONTRACT_ADDRESS`
- `CHAIN_ID`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

## Troubleshooting

### Event Indexer Not Running

1. Check Celery worker is running: `celery -A blockproof_backend worker -l info`
2. Check Celery beat is running: `celery -A blockproof_backend beat -l info`
3. Check Redis is running: `redis-cli ping`

### RPC Errors

1. Verify RPC URL is correct
2. Check you're within free tier limits
3. Try switching to public RPC as fallback

### Database Issues

1. Run migrations: `python manage.py migrate`
2. Check database connection in settings
3. Verify database user has proper permissions

## License

MIT

