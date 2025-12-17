"""
Handlers to sync blockchain events to Django models.
This keeps the cached data in sync with blockchain events.
"""

from django.utils import timezone
from .models import CredentialIssuedEvent, CredentialRevokedEvent
from credentials.models import Credential
from institutions.models import Institution
import logging

logger = logging.getLogger('blockchain')


def sync_credential_issued(event: CredentialIssuedEvent):
    """
    Sync a CredentialIssued event to the Credential model.
    """
    try:
        # Get or create institution
        institution, _ = Institution.objects.get_or_create(
            address=event.institution.lower(),
            defaults={
                'name': 'Unknown Institution',  # Will be updated if we have institution events
                'is_active': True,
                'created_at': event.block_number,  # Approximate
                'last_updated_at': event.block_number,
            }
        )
        
        # Create or update credential
        credential, created = Credential.objects.update_or_create(
            credential_id=event.credential_id,
            defaults={
                'student_wallet': event.student_wallet.lower(),
                'institution': institution,
                'fingerprint': event.fingerprint.lower(),
                'metadata_uri': event.metadata_uri,
                'encrypted_payload_uri': event.encrypted_payload_uri,
                'issued_at': event.expires_at if event.expires_at else int(timezone.now().timestamp()),
                'expires_at': event.expires_at if event.expires_at else None,
                'revoked': False,
            }
        )
        
        if created:
            logger.info(f"Created credential {event.credential_id} from event")
        else:
            logger.info(f"Updated credential {event.credential_id} from event")
            
    except Exception as e:
        logger.error(f"Error syncing CredentialIssued event {event.credential_id}: {e}")


def sync_credential_revoked(event: CredentialRevokedEvent):
    """
    Sync a CredentialRevoked event to the Credential model.
    """
    try:
        credential = Credential.objects.get(credential_id=event.credential_id)
        credential.revoked = True
        credential.revoked_at = event.revoked_at
        credential.revocation_reason_hash = event.reason_hash
        credential.save()
        
        logger.info(f"Revoked credential {event.credential_id} from event")
    except Credential.DoesNotExist:
        logger.warning(f"Credential {event.credential_id} not found when processing revocation")
    except Exception as e:
        logger.error(f"Error syncing CredentialRevoked event {event.credential_id}: {e}")

