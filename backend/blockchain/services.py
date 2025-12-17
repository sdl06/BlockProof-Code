"""
Web3 service layer for interacting with BlockProofCredentialVault contract.
Optimized to minimize RPC calls and gas costs.
"""

import os
from web3 import Web3
from web3.middleware import geth_poa_middleware
from django.conf import settings
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger('blockchain')


class BlockProofService:
    """
    Service for interacting with BlockProofCredentialVault contract.
    
    Cost optimization strategies:
    1. Cache all read operations in Django models
    2. Use event indexing instead of polling
    3. Batch event processing
    4. Use read-only RPC calls (free) for verification
    """
    
    def __init__(self):
        config = settings.BLOCKCHAIN_CONFIG
        self.rpc_url = config['RPC_URL']
        self.contract_address = config['CONTRACT_ADDRESS']
        self.chain_id = config['CHAIN_ID']
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Add PoA middleware if needed (for testnets)
        # Most testnets use PoA consensus
        testnet_chain_ids = [11155111, 5, 84532, 97, 80001, 421614]  # Sepolia, Goerli, Base Sepolia, BNB Testnet, Mumbai, Arbitrum Sepolia
        if self.chain_id in testnet_chain_ids:
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Load contract ABI (you'll need to compile and save this)
        self.contract_abi = self._load_contract_abi()
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
            abi=self.contract_abi
        ) if self.contract_address else None
        
        # Account for write operations (only when needed)
        self.private_key = config.get('PRIVATE_KEY')
        self.account = None
        if self.private_key:
            self.account = self.w3.eth.account.from_key(self.private_key)
    
    def _load_contract_abi(self) -> List[Dict]:
        """Load contract ABI from file or environment."""
        import json
        
        # Try to load from file first
        abi_path = os.path.join(os.path.dirname(__file__), 'contract_abi.json')
        if os.path.exists(abi_path):
            try:
                with open(abi_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load ABI from file: {e}, using minimal ABI")
        
        # Fallback to minimal ABI for key functions
        return [
            {
                "inputs": [{"internalType": "uint256", "name": "credentialId", "type": "uint256"}],
                "name": "credentialStatus",
                "outputs": [{
                    "components": [
                        {"internalType": "bool", "name": "exists", "type": "bool"},
                        {"internalType": "bool", "name": "valid", "type": "bool"},
                        {"internalType": "bool", "name": "revoked", "type": "bool"},
                        {"internalType": "bytes32", "name": "fingerprint", "type": "bytes32"},
                        {"internalType": "address", "name": "studentWallet", "type": "address"},
                        {"internalType": "address", "name": "institution", "type": "address"},
                        {"internalType": "uint64", "name": "issuedAt", "type": "uint64"},
                        {"internalType": "uint64", "name": "expiresAt", "type": "uint64"},
                        {"internalType": "uint64", "name": "revokedAt", "type": "uint64"}
                    ],
                    "internalType": "struct BlockProofCredentialVault.CredentialStatus",
                    "name": "",
                    "type": "tuple"
                }],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "credentialId", "type": "uint256"},
                    {"internalType": "bytes32", "name": "fingerprint", "type": "bytes32"}
                ],
                "name": "verifyFingerprint",
                "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"components": [
                    {"internalType": "address", "name": "institution", "type": "address"},
                    {"internalType": "address", "name": "studentWallet", "type": "address"},
                    {"internalType": "bytes32", "name": "fingerprint", "type": "bytes32"},
                    {"internalType": "string", "name": "metadataURI", "type": "string"},
                    {"internalType": "string", "name": "encryptedPayloadURI", "type": "string"},
                    {"internalType": "uint64", "name": "expiresAt", "type": "uint64"}
                ], "internalType": "struct BlockProofCredentialVault.IssueCredentialRequest", "name": "request", "type": "tuple"}],
                "name": "issueCredential",
                "outputs": [{"internalType": "uint256", "name": "newCredentialId", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "credentialId", "type": "uint256"},
                    {"internalType": "bytes32", "name": "reasonHash", "type": "bytes32"}
                ],
                "name": "revokeCredential",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "internalType": "uint256", "name": "credentialId", "type": "uint256"},
                    {"indexed": True, "internalType": "address", "name": "studentWallet", "type": "address"},
                    {"indexed": True, "internalType": "address", "name": "institution", "type": "address"},
                    {"indexed": False, "internalType": "bytes32", "name": "fingerprint", "type": "bytes32"},
                    {"indexed": False, "internalType": "string", "name": "metadataURI", "type": "string"},
                    {"indexed": False, "internalType": "string", "name": "encryptedPayloadURI", "type": "string"},
                    {"indexed": False, "internalType": "uint64", "name": "expiresAt", "type": "uint64"}
                ],
                "name": "CredentialIssued",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "internalType": "uint256", "name": "credentialId", "type": "uint256"},
                    {"indexed": True, "internalType": "address", "name": "revokedBy", "type": "address"},
                    {"indexed": False, "internalType": "bytes32", "name": "reasonHash", "type": "bytes32"},
                    {"indexed": False, "internalType": "uint64", "name": "revokedAt", "type": "uint64"}
                ],
                "name": "CredentialRevoked",
                "type": "event"
            }
        ]
    
    def get_credential_status(self, credential_id: int) -> Optional[Dict]:
        """
        Get credential status from blockchain (read-only, free).
        Prefer using cached data from database when possible.
        """
        if not self.contract:
            return None
        
        try:
            result = self.contract.functions.credentialStatus(credential_id).call()
            return {
                'exists': result[0],
                'valid': result[1],
                'revoked': result[2],
                'fingerprint': result[3].hex(),
                'student_wallet': result[4],
                'institution': result[5],
                'issued_at': result[6],
                'expires_at': result[7],
                'revoked_at': result[8],
            }
        except Exception as e:
            logger.error(f"Error getting credential status: {e}")
            return None
    
    def verify_fingerprint(self, credential_id: int, fingerprint: str) -> Optional[bool]:
        """
        Verify fingerprint match (read-only, free).
        Returns True if valid, False if invalid, None on error.
        """
        if not self.contract:
            logger.error("Contract not initialized for fingerprint verification")
            return None
        
        try:
            # Clean fingerprint: remove 0x prefix and ensure it's hex
            fingerprint_clean = fingerprint.replace('0x', '').replace('0X', '').lower()
            
            # Validate length (32 bytes = 64 hex characters)
            if len(fingerprint_clean) != 64:
                logger.error(f"Invalid fingerprint length: {len(fingerprint_clean)} (expected 64)")
                return None
            
            # Validate hex characters
            try:
                int(fingerprint_clean, 16)
            except ValueError:
                logger.error(f"Invalid hex characters in fingerprint")
                return None
            
            # Convert hex string to bytes32
            try:
                fingerprint_bytes = bytes.fromhex(fingerprint_clean)
            except ValueError as e:
                logger.error(f"Invalid hex in fingerprint: {e}")
                return None
            
            # Call contract function
            result = self.contract.functions.verifyFingerprint(credential_id, fingerprint_bytes).call()
            logger.info(f"Fingerprint verification for credential {credential_id}: {result}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error verifying fingerprint for credential {credential_id}: {e}", exc_info=True)
            return None
    
    def issue_credential(
        self,
        institution: str,
        student_wallet: str,
        fingerprint: str,
        metadata_uri: str,
        encrypted_payload_uri: str,
        expires_at: int = 0,
        institution_name: str = "Demo Institution"
    ) -> Optional[str]:
        """
        Issue a new credential on-chain (costs gas).
        Returns transaction hash on success.
        """
        if not self.contract or not self.account:
            logger.error("Contract or account not configured for write operations")
            return None
        
        try:
            institution_checksum = Web3.to_checksum_address(institution)
            student_checksum = Web3.to_checksum_address(student_wallet)
            sender_checksum = Web3.to_checksum_address(self.account.address)

            # Use a single "pending" nonce sequence for all txs in this call.
            # This avoids "nonce too low" when we send multiple txs back-to-back
            # (registrar / institution / controller / issue).
            next_nonce = self.w3.eth.get_transaction_count(sender_checksum, 'pending')

            def _fee_params() -> Dict:
                # Legacy txs work on Base Sepolia; keep it simple for the toy app.
                return {'gasPrice': self.w3.eth.gas_price}

            def _gas_limit(fn, fallback: int, buffer: float = 1.35) -> int:
                try:
                    est = int(fn.estimate_gas({'from': sender_checksum}))
                    return max(int(est * buffer) + 10_000, fallback)
                except Exception as e:
                    logger.warning(f"Gas estimation failed, using fallback={fallback}: {e}")
                    return fallback

            # --- Preflight / auto-bootstrap (toy-app friendly) ---
            # If the institution isn't onboarded/active or the backend account isn't allowed to issue for it,
            # the tx will revert (status=0) and there will be no CredentialIssued event.
            try:
                inst = self.contract.functions.getInstitution(institution_checksum).call()
                # getInstitution returns (name, isActive, exists, createdAt, lastUpdatedAt)
                inst_is_active = bool(inst[1])
                inst_exists = bool(inst[2])
            except Exception:
                inst_is_active = False
                inst_exists = False

            can_issue = False
            try:
                can_issue = bool(
                    self.contract.functions.canIssueForInstitution(
                        institution_checksum, sender_checksum
                    ).call()
                )
            except Exception:
                can_issue = False

            if not inst_exists or not inst_is_active or not can_issue:
                # Ensure this backend account is registrar (superAdmin can grant itself registrar).
                try:
                    super_admin = self.contract.functions.superAdmin().call()
                except Exception:
                    super_admin = None

                if super_admin and Web3.to_checksum_address(super_admin) == Web3.to_checksum_address(self.account.address):
                    # Grant registrar to self if needed
                    try:
                        is_registrar = bool(self.contract.functions.registrars(sender_checksum).call())
                    except Exception:
                        is_registrar = False

                    if not is_registrar:
                        fn = self.contract.functions.setRegistrar(sender_checksum, True)
                        tx = fn.build_transaction({
                            'from': sender_checksum,
                            'nonce': next_nonce,
                            'chainId': self.chain_id,
                            'gas': _gas_limit(fn, fallback=180000),
                            **_fee_params(),
                        })
                        tx_hash = self._send_signed_transaction(tx)
                        next_nonce += 1
                        logger.info(f"Granted registrar to backend account: {tx_hash.hex()}")
                        self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

                    # Upsert institution active if missing/inactive
                    if not inst_exists or not inst_is_active:
                        fn = self.contract.functions.upsertInstitution(institution_checksum, institution_name or "Demo Institution", True)
                        tx = fn.build_transaction({
                            'from': sender_checksum,
                            'nonce': next_nonce,
                            'chainId': self.chain_id,
                            'gas': _gas_limit(fn, fallback=260000),
                            **_fee_params(),
                        })
                        tx_hash = self._send_signed_transaction(tx)
                        next_nonce += 1
                        logger.info(f"Upserted institution active: {tx_hash.hex()}")
                        self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

                    # Ensure this backend account can issue for that institution
                    try:
                        can_issue = bool(
                            self.contract.functions.canIssueForInstitution(
                                institution_checksum, sender_checksum
                            ).call()
                        )
                    except Exception:
                        can_issue = False

                    if not can_issue:
                        fn = self.contract.functions.setInstitutionController(institution_checksum, sender_checksum, True)
                        tx = fn.build_transaction({
                            'from': sender_checksum,
                            'nonce': next_nonce,
                            'chainId': self.chain_id,
                            'gas': _gas_limit(fn, fallback=220000),
                            **_fee_params(),
                        })
                        tx_hash = self._send_signed_transaction(tx)
                        next_nonce += 1
                        logger.info(f"Set institution controller: {tx_hash.hex()}")
                        self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                else:
                    logger.warning(
                        "Institution not ready and backend account is not superAdmin; issuance may revert. "
                        "Onboard institution via registrar/superAdmin first."
                    )

            # Prepare transaction
            request = (
                institution_checksum,
                student_checksum,
                bytes.fromhex(fingerprint.replace('0x', '')),
                metadata_uri,
                encrypted_payload_uri,
                expires_at
            )

            fn_issue = self.contract.functions.issueCredential(request)
            transaction = fn_issue.build_transaction({
                'from': sender_checksum,
                'nonce': next_nonce,
                'chainId': self.chain_id,
                # Dynamic gas to avoid out-of-gas on L2s when calldata strings are long.
                'gas': _gas_limit(fn_issue, fallback=450000),
                **_fee_params(),
            })
            
            tx_hash = self._send_signed_transaction(transaction)
            next_nonce += 1
            
            logger.info(f"Credential issuance transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error issuing credential: {e}")
            return None

    def _send_signed_transaction(self, transaction: Dict) -> "Web3.types.HexBytes":
        """
        Sign and send a transaction, compatible across eth-account versions
        that may use rawTransaction vs raw_transaction.
        """
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)

        raw_bytes = None
        if hasattr(signed_txn, "rawTransaction"):
            raw_bytes = getattr(signed_txn, "rawTransaction")
        elif hasattr(signed_txn, "raw_transaction"):
            raw_bytes = getattr(signed_txn, "raw_transaction")
        else:
            try:
                raw_bytes = signed_txn["rawTransaction"]  # type: ignore[index]
            except Exception:
                try:
                    raw_bytes = signed_txn["raw_transaction"]  # type: ignore[index]
                except Exception:
                    raw_bytes = None

        if raw_bytes is None:
            raise AttributeError("SignedTransaction has no raw transaction bytes attribute")

        return self.w3.eth.send_raw_transaction(raw_bytes)
    
    def revoke_credential(self, credential_id: int, reason_hash: str) -> Optional[str]:
        """
        Revoke a credential on-chain (costs gas).
        Returns transaction hash on success.
        """
        if not self.contract or not self.account:
            logger.error("Contract or account not configured for write operations")
            return None
        
        try:
            reason_hash_bytes = bytes.fromhex(reason_hash.replace('0x', ''))
            sender_checksum = Web3.to_checksum_address(self.account.address)
            next_nonce = self.w3.eth.get_transaction_count(sender_checksum, 'pending')
            
            transaction = self.contract.functions.revokeCredential(
                credential_id,
                reason_hash_bytes
            ).build_transaction({
                'from': sender_checksum,
                'nonce': next_nonce,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
            })
            
            tx_hash = self._send_signed_transaction(transaction)
            
            logger.info(f"Credential revocation transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Error revoking credential: {e}")
            return None
    
    def get_events(
        self,
        event_name: str,
        from_block: int,
        to_block: int = 'latest'
    ) -> List[Dict]:
        """
        Get events from blockchain (read-only, but can be expensive for large ranges).
        Use event indexing instead for cost optimization.
        """
        if not self.contract:
            return []
        
        try:
            event = getattr(self.contract.events, event_name)
            events = event.get_logs(fromBlock=from_block, toBlock=to_block)
            return [dict(event) for event in events]
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return []


# Singleton instance
_blockproof_service = None

def get_blockproof_service() -> BlockProofService:
    """Get or create BlockProofService instance."""
    global _blockproof_service
    if _blockproof_service is None:
        _blockproof_service = BlockProofService()
    return _blockproof_service

