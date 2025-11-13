// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

/// @title BlockProofCredentialVault
/// @notice Issues and verifies tamper-proof diploma fingerprints owned by student wallets.
/// @dev Designed to be blockchain-agnostic and production-friendly with explicit role separation.
contract BlockProofCredentialVault {
    // ----------------------------------------------------------
    //                         Errors
    // ----------------------------------------------------------
    error NotSuperAdmin();
    error NotRegistrar();
    error UnauthorizedController(address institution, address sender);
    error InstitutionNotFound(address institution);
    error InstitutionInactive(address institution);
    error InvalidInstitution();
    error InvalidFingerprint();
    error InvalidStudentWallet();
    error FingerprintAlreadyUsed(bytes32 fingerprint);
    error CredentialNotFound(uint256 credentialId);
    error CredentialRevokedAlready(uint256 credentialId);
    error InvalidSuperAdminCandidate();
    error ContractPaused();

    // ----------------------------------------------------------
    //                          Events
    // ----------------------------------------------------------
    event SuperAdminUpdated(address indexed newAdmin);
    event RegistrarUpdated(address indexed registrar, bool allowed);
    event InstitutionUpserted(
        address indexed institution,
        string name,
        bool isActive,
        uint64 timestamp
    );
    event InstitutionControllerUpdated(
        address indexed institution,
        address indexed controller,
        bool allowed
    );
    event CredentialIssued(
        uint256 indexed credentialId,
        address indexed studentWallet,
        address indexed institution,
        bytes32 fingerprint,
        string metadataURI,
        string encryptedPayloadURI,
        uint64 expiresAt
    );
    event CredentialRevoked(
        uint256 indexed credentialId,
        address indexed revokedBy,
        bytes32 reasonHash,
        uint64 revokedAt
    );
    event PausedStateChanged(bool isPaused, address indexed triggeredBy);

    // ----------------------------------------------------------
    //                         Structs
    // ----------------------------------------------------------
    struct Institution {
        string name;
        bool exists;
        bool isActive;
        uint64 createdAt;
        uint64 lastUpdatedAt;
    }

    struct Credential {
        uint256 id;
        address studentWallet;
        address institution;
        bytes32 fingerprint;
        string metadataURI;
        string encryptedPayloadURI;
        uint64 issuedAt;
        uint64 expiresAt;
        uint64 revokedAt;
        bytes32 revocationReasonHash;
        bool revoked;
    }

    struct IssueCredentialRequest {
        address institution;
        address studentWallet;
        bytes32 fingerprint;
        string metadataURI;
        string encryptedPayloadURI;
        uint64 expiresAt;
    }

    struct CredentialStatus {
        bool exists;
        bool valid;
        bool revoked;
        bytes32 fingerprint;
        address studentWallet;
        address institution;
        uint64 issuedAt;
        uint64 expiresAt;
        uint64 revokedAt;
    }

    // ----------------------------------------------------------
    //                    State & Storage
    // ----------------------------------------------------------
    address public superAdmin;
    address public pendingSuperAdmin;

    bool public paused;

    mapping(address => bool) public registrars;
    mapping(address => Institution) private _institutions;
    mapping(address => mapping(address => bool)) private _institutionControllers;

    uint256 public credentialCount;
    mapping(uint256 => Credential) private _credentials;
    mapping(address => uint256[]) private _studentCredentialIds;
    mapping(bytes32 => bool) public fingerprintUsed;

    // ----------------------------------------------------------
    //                      Constructor
    // ----------------------------------------------------------
    constructor() {
        superAdmin = msg.sender;
        emit SuperAdminUpdated(msg.sender);
    }

    // ----------------------------------------------------------
    //                     Modifiers
    // ----------------------------------------------------------
    modifier onlySuperAdmin() {
        if (msg.sender != superAdmin) revert NotSuperAdmin();
        _;
    }

    modifier onlyRegistrar() {
        if (!registrars[msg.sender]) revert NotRegistrar();
        _;
    }

    modifier whenNotPaused() {
        if (paused) revert ContractPaused();
        _;
    }

    // ----------------------------------------------------------
    //              Admin & Emergency Management
    // ----------------------------------------------------------
    /// @notice Starts a two-step transfer of the super admin role.
    /// @param newAdmin wallet that must later call `acceptSuperAdmin`.
    function transferSuperAdmin(address newAdmin) external onlySuperAdmin {
        if (newAdmin == address(0)) revert InvalidSuperAdminCandidate();
        pendingSuperAdmin = newAdmin;
    }

    /// @notice Completes the transfer of the super admin role.
    function acceptSuperAdmin() external {
        if (msg.sender != pendingSuperAdmin) revert NotSuperAdmin();
        superAdmin = pendingSuperAdmin;
        pendingSuperAdmin = address(0);
        emit SuperAdminUpdated(superAdmin);
    }

    /// @notice Adds or removes a registrar that can manage university records.
    /// @param registrar target wallet.
    /// @param allowed true to grant permissions, false to revoke.
    function setRegistrar(address registrar, bool allowed) external onlySuperAdmin {
        registrars[registrar] = allowed;
        emit RegistrarUpdated(registrar, allowed);
    }

    /// @notice Pauses or resumes the contract in emergencies.
    /// @param value true pauses, false resumes.
    function setPaused(bool value) external onlySuperAdmin {
        paused = value;
        emit PausedStateChanged(value, msg.sender);
    }

    // ----------------------------------------------------------
    //                Institution Administration
    // ----------------------------------------------------------
    /// @notice Registers or updates a university/institution.
    /// @param institution canonical wallet controlled by the university.
    /// @param name display name for off-chain reference.
    /// @param isActive whether the institution can currently issue credentials.
    function upsertInstitution(
        address institution,
        string calldata name,
        bool isActive
    ) external onlyRegistrar {
        if (institution == address(0)) revert InvalidInstitution();
        if (bytes(name).length == 0) revert InvalidInstitution();

        Institution storage record = _institutions[institution];
        uint64 nowTs = uint64(block.timestamp);

        if (!record.exists) {
            record.exists = true;
            record.createdAt = nowTs;
        }

        record.name = name;
        record.isActive = isActive;
        record.lastUpdatedAt = nowTs;

        emit InstitutionUpserted(institution, name, isActive, nowTs);
    }

    /// @notice Adds or removes controllers allowed to issue on behalf of an institution.
    /// @param institution institution being managed.
    /// @param controller wallet being toggled.
    /// @param allowed flag to enable/disable.
    function setInstitutionController(
        address institution,
        address controller,
        bool allowed
    ) external {
        _requireInstitutionManager(institution, msg.sender);
        if (controller == address(0)) revert UnauthorizedController(institution, controller);

        _institutionControllers[institution][controller] = allowed;
        emit InstitutionControllerUpdated(institution, controller, allowed);
    }

    /// @notice Checks whether a wallet can issue for an institution.
    function canIssueForInstitution(address institution, address controller) public view returns (bool) {
        return controller == institution || _institutionControllers[institution][controller];
    }

    // ----------------------------------------------------------
    //                Credential Issuance & Lifecycle
    // ----------------------------------------------------------
    /// @notice Issues a new credential fingerprint anchored on-chain.
    /// @param request batched issuance payload.
    /// @dev `metadataURI` can point to IPFS/HTTPS metadata; `encryptedPayloadURI` should point to the private diploma document.
    function issueCredential(
        IssueCredentialRequest calldata request
    ) external whenNotPaused returns (uint256 newCredentialId) {
        _requireIssuePermissions(request.institution, msg.sender);
        _requireActiveInstitution(request.institution);

        if (request.studentWallet == address(0)) revert InvalidStudentWallet();
        if (request.fingerprint == bytes32(0)) revert InvalidFingerprint();
        if (fingerprintUsed[request.fingerprint]) revert FingerprintAlreadyUsed(request.fingerprint);

        credentialCount += 1;
        newCredentialId = credentialCount;

        Credential storage credential = _credentials[newCredentialId];
        credential.id = newCredentialId;
        credential.studentWallet = request.studentWallet;
        credential.institution = request.institution;
        credential.fingerprint = request.fingerprint;
        credential.metadataURI = request.metadataURI;
        credential.encryptedPayloadURI = request.encryptedPayloadURI;
        credential.issuedAt = uint64(block.timestamp);
        credential.expiresAt = request.expiresAt;

        fingerprintUsed[request.fingerprint] = true;
        _studentCredentialIds[request.studentWallet].push(newCredentialId);

        emit CredentialIssued(
            newCredentialId,
            request.studentWallet,
            request.institution,
            request.fingerprint,
            request.metadataURI,
            request.encryptedPayloadURI,
            request.expiresAt
        );
    }

    /// @notice Revokes an issued credential.
    /// @param credentialId target credential identifier.
    /// @param reasonHash optional keccak256 hash of the off-chain revocation note.
    function revokeCredential(uint256 credentialId, bytes32 reasonHash) external whenNotPaused {
        Credential storage credential = _credentialById(credentialId);
        _requireIssuePermissions(credential.institution, msg.sender);
        if (credential.revoked) revert CredentialRevokedAlready(credentialId);

        credential.revoked = true;
        credential.revokedAt = uint64(block.timestamp);
        credential.revocationReasonHash = reasonHash;

        emit CredentialRevoked(credentialId, msg.sender, reasonHash, credential.revokedAt);
    }

    // ----------------------------------------------------------
    //                    View / Validation
    // ----------------------------------------------------------
    /// @notice Returns a credential status summary that verifiers can consume.
    function credentialStatus(uint256 credentialId) external view returns (CredentialStatus memory) {
        Credential storage credential = _credentials[credentialId];
        if (credential.id == 0) return CredentialStatus(false, false, false, bytes32(0), address(0), address(0), 0, 0, 0);

        bool isExpired = credential.expiresAt != 0 && credential.expiresAt < block.timestamp;
        bool isValid = !credential.revoked && !isExpired;

        return
            CredentialStatus(
                true,
                isValid,
                credential.revoked,
                credential.fingerprint,
                credential.studentWallet,
                credential.institution,
                credential.issuedAt,
                credential.expiresAt,
                credential.revokedAt
            );
    }

    /// @notice Verifies that a credential exists, is valid, and matches the supplied fingerprint.
    function verifyFingerprint(uint256 credentialId, bytes32 fingerprint) external view returns (bool) {
        Credential storage credential = _credentials[credentialId];
        if (credential.id == 0) return false;

        bool matches = credential.fingerprint == fingerprint;
        bool expired = credential.expiresAt != 0 && credential.expiresAt < block.timestamp;
        return matches && !credential.revoked && !expired;
    }

    /// @notice Returns the full credential record (metadata URIs included).
    function getCredential(uint256 credentialId) external view returns (Credential memory) {
        Credential storage credential = _credentialById(credentialId);
        return credential;
    }

    /// @notice Fetches institution metadata.
    function getInstitution(address institution) external view returns (Institution memory) {
        return _institutions[institution];
    }

    /// @notice Checks whether a controller is currently enabled for the institution.
    function isController(address institution, address controller) external view returns (bool) {
        return _institutionControllers[institution][controller];
    }

    /// @notice Lists all credential identifiers owned by a student wallet.
    function studentCredentialIds(address studentWallet) external view returns (uint256[] memory) {
        return _studentCredentialIds[studentWallet];
    }

    // ----------------------------------------------------------
    //                  Internal Helper Logic
    // ----------------------------------------------------------
    function _credentialById(uint256 credentialId) internal view returns (Credential storage) {
        Credential storage credential = _credentials[credentialId];
        if (credential.id == 0) revert CredentialNotFound(credentialId);
        return credential;
    }

    function _requireIssuePermissions(address institution, address issuer) internal view {
        if (!canIssueForInstitution(institution, issuer)) {
            revert UnauthorizedController(institution, issuer);
        }
    }

    function _requireInstitutionManager(address institution, address actor) internal view {
        if (
            actor != superAdmin &&
            !registrars[actor] &&
            actor != institution
        ) {
            revert UnauthorizedController(institution, actor);
        }
        _requireInstitutionExists(institution);
    }

    function _requireInstitutionExists(address institution) internal view {
        if (!_institutions[institution].exists) revert InstitutionNotFound(institution);
    }

    function _requireActiveInstitution(address institution) internal view {
        Institution storage record = _institutions[institution];
        if (!record.exists) revert InstitutionNotFound(institution);
        if (!record.isActive) revert InstitutionInactive(institution);
    }
}
