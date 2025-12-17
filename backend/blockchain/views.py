"""
Blockchain API views for verification operations.
These use cached data when possible to minimize RPC calls.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .services import get_blockproof_service
from credentials.models import Credential
import logging
from web3.exceptions import TransactionNotFound

logger = logging.getLogger('blockchain')

def _explorer_tx_url(chain_id: int, tx_hash: str) -> str:
    """
    Return a best-effort block explorer URL for the given chain id.
    """
    base = None
    if chain_id == 1:
        base = "https://etherscan.io"
    elif chain_id == 11155111:
        base = "https://sepolia.etherscan.io"
    elif chain_id == 84532:
        base = "https://sepolia.basescan.org"
    elif chain_id == 8453:
        base = "https://basescan.org"
    elif chain_id == 42161:
        base = "https://arbiscan.io"
    elif chain_id == 421614:
        base = "https://sepolia.arbiscan.io"
    elif chain_id == 137:
        base = "https://polygonscan.com"
    elif chain_id == 80001:
        base = "https://mumbai.polygonscan.com"
    elif chain_id == 56:
        base = "https://bscscan.com"
    elif chain_id == 97:
        base = "https://testnet.bscscan.com"

    if not base:
        return ""
    return f"{base}/tx/{tx_hash}"


@api_view(['POST'])
def verify_credential(request):
    """
    Verify a credential fingerprint.
    Uses cached data first, falls back to blockchain if needed.
    """
    credential_id = request.data.get('credential_id')
    fingerprint = request.data.get('fingerprint')
    
    if not credential_id or not fingerprint:
        return Response(
            {'error': 'credential_id and fingerprint are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Normalize fingerprint (remove 0x if present, ensure lowercase)
    fingerprint_clean = fingerprint.strip().lower()
    if fingerprint_clean.startswith('0x'):
        fingerprint_clean = fingerprint_clean[2:]
    
    # Ensure fingerprint is 64 hex characters (32 bytes)
    if len(fingerprint_clean) != 64:
        return Response(
            {'error': 'Fingerprint must be 32 bytes (64 hex characters)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Convert credential_id to int
    try:
        credential_id_int = int(credential_id)
    except (ValueError, TypeError):
        return Response(
            {'error': 'credential_id must be a valid integer'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Try to get from cache first
    try:
        credential = Credential.objects.get(credential_id=credential_id_int)
        # Compare fingerprints (both should be lowercase, with 0x prefix)
        credential_fp = credential.fingerprint.lower().replace('0x', '')
        if credential_fp == fingerprint_clean:
            # Check if still valid (not revoked, not expired)
            is_valid = credential.is_valid()
            return Response({
                'valid': is_valid,
                'credential_id': credential_id_int,
                'source': 'cache'
            })
        else:
            # Fingerprint doesn't match in cache
            logger.info(f"Fingerprint mismatch in cache for credential {credential_id_int}")
    except Credential.DoesNotExist:
        logger.info(f"Credential {credential_id_int} not found in cache, checking blockchain")
    except Exception as e:
        logger.error(f"Error checking cache: {e}")
    
    # Fall back to blockchain (read-only, free)
    try:
        service = get_blockproof_service()
        if not service or not service.contract:
            return Response(
                {'error': 'Blockchain service not configured'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Add 0x prefix back for the service call
        fingerprint_with_prefix = '0x' + fingerprint_clean
        is_valid = service.verify_fingerprint(credential_id_int, fingerprint_with_prefix)
        
        if is_valid is None:
            return Response(
                {'error': 'Verification service returned invalid response. Check logs for details.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'valid': is_valid,
            'credential_id': credential_id_int,
            'source': 'blockchain'
        })
    except Exception as e:
        logger.error(f"Error verifying fingerprint on blockchain: {e}", exc_info=True)
        return Response(
            {'error': f'Verification failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def credential_status(request, credential_id):
    """
    Get credential status.
    Uses cached data first, falls back to blockchain if needed.
    """
    # Try cache first
    try:
        credential = Credential.objects.get(credential_id=credential_id)
        return Response({
            'exists': True,
            'valid': credential.is_valid(),
            'revoked': credential.revoked,
            'fingerprint': credential.fingerprint,
            'student_wallet': credential.student_wallet,
            'institution': credential.institution.address,
            'issued_at': credential.issued_at,
            'expires_at': credential.expires_at,
            'revoked_at': credential.revoked_at,
            'source': 'cache'
        })
    except Credential.DoesNotExist:
        pass
    
    # Fall back to blockchain
    service = get_blockproof_service()
    status_data = service.get_credential_status(credential_id)
    
    if not status_data:
        return Response(
            {'error': 'Credential not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    return Response({
        **status_data,
        'source': 'blockchain'
    })


@api_view(['GET'])
def transaction_receipt(request, tx_hash: str):
    """
    Fetch a transaction receipt from the configured RPC and (if possible)
    decode a CredentialIssued event to recover the on-chain credential_id.

    This is useful because issue() returns a tx hash immediately, while the
    credential_id is only known once the tx is mined and events are available.
    """
    service = get_blockproof_service()
    if not service or not service.w3:
        return Response(
            {"error": "Blockchain service not configured"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    tx_hash_norm = tx_hash.strip()
    if not tx_hash_norm.startswith("0x"):
        tx_hash_norm = "0x" + tx_hash_norm

    chain_id = None
    try:
        chain_id = int(service.w3.eth.chain_id)
    except Exception:
        chain_id = int(getattr(service, "chain_id", 0) or 0)

    try:
        receipt = service.w3.eth.get_transaction_receipt(tx_hash_norm)
    except TransactionNotFound:
        return Response(
            {
                "error": "Transaction not found on configured RPC. It may be pending, dropped, or on a different network.",
                "tx_hash": tx_hash_norm,
                "chain_id": chain_id,
                "explorer_url": _explorer_tx_url(chain_id, tx_hash_norm) if chain_id else "",
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.error(f"Error fetching transaction receipt: {e}", exc_info=True)
        return Response(
            {"error": f"Failed to fetch receipt: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    decoded = {}
    credential_id = None
    try:
        if service.contract and hasattr(service.contract.events, "CredentialIssued"):
            events = service.contract.events.CredentialIssued().process_receipt(receipt)
            if events:
                ev = events[0]
                args = ev.get("args") or {}
                # Note: ABI uses credentialId, studentWallet, institution, fingerprint, metadataURI, encryptedPayloadURI, expiresAt
                credential_id = args.get("credentialId")
                decoded = {
                    "credential_id": int(credential_id) if credential_id is not None else None,
                    "student_wallet": args.get("studentWallet"),
                    "institution": args.get("institution"),
                    "fingerprint": ("0x" + args.get("fingerprint").hex()) if getattr(args.get("fingerprint"), "hex", None) else args.get("fingerprint"),
                    "metadata_uri": args.get("metadataURI"),
                    "encrypted_payload_uri": args.get("encryptedPayloadURI"),
                    "expires_at": args.get("expiresAt"),
                }
    except Exception as e:
        # Decoding isn't critical; return receipt basics even if decode fails.
        logger.warning(f"Could not decode CredentialIssued event: {e}")

    return Response(
        {
            "tx_hash": tx_hash_norm,
            "chain_id": chain_id,
            "explorer_url": _explorer_tx_url(chain_id, tx_hash_norm) if chain_id else "",
            "status": int(getattr(receipt, "status", 0)) if hasattr(receipt, "status") else receipt.get("status"),
            "block_number": int(getattr(receipt, "blockNumber", 0)) if hasattr(receipt, "blockNumber") else receipt.get("blockNumber"),
            "decoded": decoded,
        }
    )

