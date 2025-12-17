# Deployment Guide

Step-by-step guide to deploy the BlockProof Django backend.

## Prerequisites

1. Python 3.9+
2. PostgreSQL (for production)
3. Redis (for Celery)
4. Blockchain RPC endpoint (Infura, Alchemy, etc.)
5. Deployed smart contract address

## Step 1: Environment Setup

### 1.1 Clone and Install

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 1.2 Configure Environment Variables

Create `.env` file:

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/blockproof

# Blockchain
RPC_URL=https://mainnet.infura.io/v3/YOUR_KEY
CONTRACT_ADDRESS=0x...
CHAIN_ID=1  # 1 for mainnet, 11155111 for Sepolia

# Private key (for write operations)
PRIVATE_KEY=0x...

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

## Step 2: Database Setup

### 2.1 Create Database

```bash
# PostgreSQL
createdb blockproof

# Or using psql
psql -U postgres
CREATE DATABASE blockproof;
```

### 2.2 Run Migrations

```bash
python manage.py migrate
python manage.py createsuperuser
```

## Step 3: Deploy Application

### Option A: Railway (Recommended for Low Cost)

1. **Install Railway CLI**:
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Initialize Project**:
   ```bash
   railway init
   railway link
   ```

3. **Set Environment Variables**:
   ```bash
   railway variables set SECRET_KEY=your-secret-key
   railway variables set DATABASE_URL=postgresql://...
   # ... set all other variables
   ```

4. **Deploy**:
   ```bash
   railway up
   ```

5. **Add PostgreSQL Service**:
   - In Railway dashboard, add PostgreSQL service
   - Update `DATABASE_URL` to use Railway's PostgreSQL

6. **Add Redis Service**:
   - Add Redis service in Railway dashboard
   - Update `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`

### Option B: Render

1. **Create Web Service**:
   - Connect GitHub repository
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn blockproof_backend.wsgi:application`

2. **Add PostgreSQL**:
   - Create PostgreSQL database
   - Use provided `DATABASE_URL`

3. **Add Redis**:
   - Create Redis instance
   - Use provided Redis URL

4. **Set Environment Variables**:
   - Add all variables from `.env.example`

### Option C: AWS/GCP

#### AWS (Elastic Beanstalk)

1. **Install EB CLI**:
   ```bash
   pip install awsebcli
   ```

2. **Initialize**:
   ```bash
   eb init -p python-3.9 blockproof-backend
   eb create blockproof-env
   ```

3. **Configure**:
   - Set environment variables in EB console
   - Add RDS PostgreSQL
   - Add ElastiCache Redis

4. **Deploy**:
   ```bash
   eb deploy
   ```

#### GCP (App Engine)

1. **Create `app.yaml`**:
   ```yaml
   runtime: python39
   env: standard
   
   env_variables:
     SECRET_KEY: 'your-secret-key'
     DATABASE_URL: 'postgresql://...'
     # ... other variables
   
   automatic_scaling:
     min_instances: 1
     max_instances: 10
   ```

2. **Deploy**:
   ```bash
   gcloud app deploy
   ```

## Step 4: Setup Celery Workers

### Option A: Railway/Render

Add a separate service/worker:

**Railway**:
- Add new service
- Command: `celery -A blockproof_backend worker -l info`
- Same environment variables

**Render**:
- Create background worker
- Command: `celery -A blockproof_backend worker -l info`

### Option B: Separate Server

```bash
# Install on server
pip install -r requirements.txt

# Run worker
celery -A blockproof_backend worker -l info --detach

# Run beat (scheduler)
celery -A blockproof_backend beat -l info --detach
```

### Option C: Systemd (Linux)

Create `/etc/systemd/system/celery-worker.service`:

```ini
[Unit]
Description=Celery Worker
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A blockproof_backend worker -l info

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable celery-worker
sudo systemctl start celery-worker
```

## Step 5: Initial Data Sync

After deployment, sync historical events:

```bash
python manage.py sync_events
```

Or via Django shell:
```python
from blockchain.tasks import index_blockchain_events
index_blockchain_events()
```

## Step 6: Monitoring

### Health Check Endpoint

Add to `urls.py`:
```python
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'database': 'connected',  # Add DB check
        'blockchain': 'connected',  # Add RPC check
    })
```

### Logging

Configure logging in `settings.py` for production:
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/blockproof/backend.log',
        },
    },
    'loggers': {
        'blockchain': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

## Step 7: SSL/HTTPS

### Railway/Render
- Automatic SSL via Let's Encrypt
- No additional configuration needed

### AWS/GCP
- Use Application Load Balancer with SSL certificate
- Or Cloudflare in front of your app

## Step 8: Backup Strategy

### Database Backups

**PostgreSQL**:
```bash
# Manual backup
pg_dump blockproof > backup.sql

# Automated (cron)
0 2 * * * pg_dump blockproof > /backups/blockproof-$(date +\%Y\%m\%d).sql
```

**Railway/Render**:
- Use built-in backup features
- Or external backup service

## Cost Estimates

### Minimal Setup (Railway/Render)
- App: $5-10/month
- PostgreSQL: Included or $5/month
- Redis: $0-5/month (free tier available)
- **Total: ~$5-20/month**

### Production Setup (AWS/GCP)
- App hosting: $10-50/month
- RDS PostgreSQL: $15-30/month
- ElastiCache Redis: $15-30/month
- Load balancer: $20/month
- **Total: ~$60-130/month**

## Troubleshooting

### Event Indexer Not Running

1. Check Celery worker logs
2. Verify Redis connection
3. Check RPC endpoint is accessible
4. Verify contract address is correct

### High RPC Costs

1. Reduce event indexing frequency
2. Use public RPC as fallback
3. Implement request throttling
4. Monitor usage and upgrade plan if needed

### Database Connection Issues

1. Verify `DATABASE_URL` format
2. Check database is accessible from app
3. Verify credentials are correct
4. Check firewall rules

## Next Steps

1. Set up monitoring (Sentry, DataDog, etc.)
2. Configure alerts for critical failures
3. Set up CI/CD pipeline
4. Implement rate limiting
5. Add API authentication
6. Set up analytics

