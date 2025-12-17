"""
Celery tasks for background blockchain operations.
This minimizes blocking and optimizes cost through batch processing.
"""

from celery import shared_task
from django.conf import settings
from .models import (
    CredentialIssuedEvent,
    CredentialRevokedEvent,
    IndexerState
)
from .services import get_blockproof_service
from .sync_handlers import sync_credential_issued, sync_credential_revoked
import logging

logger = logging.getLogger('blockchain')


@shared_task
def index_blockchain_events():
    """
    Index blockchain events incrementally.
    This is the core cost optimization: instead of polling, we process events
    in batches and cache them locally.
    """
    service = get_blockproof_service()
    if not service.contract:
        logger.warning("Contract not configured, skipping event indexing")
        return
    
    config = settings.BLOCKCHAIN_CONFIG
    batch_size = config.get('EVENT_INDEXING_BATCH_SIZE', 1000)
    
    # Get last processed block
    last_block = IndexerState.get_last_block('credential_events')
    current_block = service.w3.eth.block_number
    
    # Process in batches to avoid timeout
    to_block = min(last_block + batch_size, current_block)
    
    if to_block <= last_block:
        logger.info("No new blocks to process")
        return
    
    logger.info(f"Indexing events from block {last_block} to {to_block}")
    
    try:
        # Get CredentialIssued events
        issued_events = service.get_events('CredentialIssued', last_block + 1, to_block)
        for event in issued_events:
            event_obj = _process_credential_issued_event(event)
            if event_obj:
                sync_credential_issued(event_obj)
        
        # Get CredentialRevoked events
        revoked_events = service.get_events('CredentialRevoked', last_block + 1, to_block)
        for event in revoked_events:
            event_obj = _process_credential_revoked_event(event)
            if event_obj:
                sync_credential_revoked(event_obj)
        
        # Update last processed block
        IndexerState.update_last_block('credential_events', to_block)
        
        logger.info(f"Processed {len(issued_events)} issued and {len(revoked_events)} revoked events")
    except Exception as e:
        logger.error(f"Error indexing events: {e}", exc_info=True)


def _process_credential_issued_event(event_data: dict):
    """Process and cache a CredentialIssued event."""
    try:
        args = event_data['args']
        event, created = CredentialIssuedEvent.objects.update_or_create(
            transaction_hash=event_data['transactionHash'].hex(),
            defaults={
                'block_number': event_data['blockNumber'],
                'log_index': event_data['logIndex'],
                'credential_id': args['credentialId'],
                'student_wallet': args['studentWallet'],
                'institution': args['institution'],
                'fingerprint': args['fingerprint'].hex(),
                'metadata_uri': args['metadataURI'],
                'encrypted_payload_uri': args['encryptedPayloadURI'],
                'expires_at': args['expiresAt'] if args['expiresAt'] > 0 else None,
                'processed': True,
            }
        )
        return event
    except Exception as e:
        logger.error(f"Error processing CredentialIssued event: {e}")
        return None


def _process_credential_revoked_event(event_data: dict):
    """Process and cache a CredentialRevoked event."""
    try:
        args = event_data['args']
        event, created = CredentialRevokedEvent.objects.update_or_create(
            transaction_hash=event_data['transactionHash'].hex(),
            defaults={
                'block_number': event_data['blockNumber'],
                'log_index': event_data['logIndex'],
                'credential_id': args['credentialId'],
                'revoked_by': args['revokedBy'],
                'reason_hash': args['reasonHash'].hex(),
                'revoked_at': args['revokedAt'],
                'processed': True,
            }
        )
        return event
    except Exception as e:
        logger.error(f"Error processing CredentialRevoked event: {e}")
        return None


# Note: Celery beat schedule is configured in settings.py or celery.py
# This function is kept for reference but beat schedule should be set in celery.py

