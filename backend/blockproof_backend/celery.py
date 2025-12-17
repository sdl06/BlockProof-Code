"""
Celery configuration for background blockchain operations.
This minimizes blocking operations and optimizes cost.
"""

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blockproof_backend.settings')

app = Celery('blockproof_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configure periodic tasks (beat schedule)
config = settings.BLOCKCHAIN_CONFIG
interval = config.get('EVENT_INDEXING_INTERVAL', 60)

app.conf.beat_schedule = {
    'index-blockchain-events': {
        'task': 'blockchain.tasks.index_blockchain_events',
        'schedule': interval,  # Run every N seconds
    },
}

