# BlockProof Architecture

## Overview

BlockProof turns academic credentials into verifiable, student-owned assets. Universities (or their registrars) anchor a cryptographic fingerprint of each credential on-chain while the full diploma remains inside the student's embedded wallet. Employers later prove authenticity by matching the fingerprint from a QR code or verification link against the blockchain record.

The on-chain backend is implemented in `contracts/BlockProofCredentialVault.sol` and is designed to run on any EVM-compatible chain that the BlockProof deployment strategy targets.

## Roles

| Role | Description | Powers |
| --- | --- | --- |
| `superAdmin` | BlockProof core ops multisig. | Approves registrars, pauses protocol, hands over ownership. |
| `registrar` | BlockProof compliance agents. | Onboard / update universities (institutions). |
| `institution` | University-controlled wallet (can be a Safe). | Issues credentials, manages controllers. |
| `controller` | Registrar office operators or automation keys. | Issue / revoke credentials for their institution. |
| `student wallet` | Embedded wallet instantiated via Privy/Dynamic. | Holds credentials and exposes QR / verify links. |
| `verifier` | Employer / school verifying record. | Calls the public `credentialStatus` or `verifyFingerprint` view. |

## Data Model

### Institutions

- Stored by canonical wallet address.
- Contains name, active flag, and timestamps.
- Controllers per institution are tracked to allow departmental issuers or off-chain automation.

### Credentials

- Fingerprint: `bytes32` hash representing the diploma payload. Suggested format:
  ```
  fingerprint = keccak256(
      abi.encodePacked(
          studentWallet,
          institutionId,
          diplomaDocumentHash,
          metadataURI,
          issuedAt
      )
  );
  ```
- Metadata URI: public details for wallets or explorers (e.g., IPFS JSON).
- Encrypted payload URI: private diploma stored in the student's wallet vault or university KMS. The URI can be an HTTPS endpoint requiring auth.
- Revocation reason hash: hashed string describing why a credential was revoked.
- Expires at (optional): supports time-bound certificates.

### Wallet Strategy

1. Student logs in with university account; Privy/Dynamic provisions a non-custodial embedded wallet.
2. The wallet address is passed to the contract when issuing credentials (`studentWallet`).
3. The wallet stores the full diploma, encrypted and synced to off-chain storage, while the on-chain record only stores the fingerprint.
4. Verification links (QR codes) bundle the `credentialId` and fingerprint so that anyone can call `verifyFingerprint`.

## Flows

### 1. Onboarding a University

1. `superAdmin` adds registrar(s) via `setRegistrar`.
2. Registrar calls `upsertInstitution(institutionAddress, name, true)`.
3. Institution (or registrar) assigns controllers (operators) using `setInstitutionController`.

### 2. Issuing a Credential

1. Registrar backend creates the fingerprint from the diploma payload.
2. Controller calls `issueCredential` with:
   - institution wallet
   - student embedded wallet address
   - fingerprint
   - public metadata URI (IPFS/HTTPS)
   - encrypted payload URI (Privy/Dynamic resource)
3. Contract stores the record, marks fingerprint as unique, and emits `CredentialIssued`.
4. Off-chain service listens to events and updates the student's wallet view.

### 3. Verification

1. Employer scans a QR code or link to obtain `{ credentialId, fingerprint }`.
2. Calls `credentialStatus(credentialId)` for status and metadata, plus `verifyFingerprint` to confirm fingerprint match.
3. If result is true, credential is authentic, unrevoked, and unexpired.

### 4. Revocation

1. Controller hashes a revocation reason (e.g., `keccak256("Academic misconduct case #123")`).
2. Calls `revokeCredential(id, reasonHash)`.
3. Contract records timestamp and emits `CredentialRevoked`. QR lookups will now fail.

## Security Considerations

- **Role separation:** Institutions cannot onboard each other; only trusted registrars can, protecting network integrity.
- **Controller granularity:** Registrars or institutions can rotate keys without redeploying contracts.
- **Fingerprint uniqueness:** `fingerprintUsed` prevents accidental duplication of documents once minted.
- **Pause switch:** `setPaused(true)` halts issuance/revocation during incidents.
- **Embedded wallets:** Students never handle seed phrases; wallet providers abstract key custody with email/SAML login, while still giving users ownership.

## Suggested Off-Chain Services

- Event indexer to sync `CredentialIssued` and `CredentialRevoked` into a database and wallet UI.
- QR/link generator embedding the fingerprint + credential id.
- Compliance dashboard for registrars to monitor issuance throughput and detect anomalies.

This document, combined with the inline NatSpec in the Solidity contract, should be sufficient for smart-contract auditors, backend integrators, and product stakeholders to understand how BlockProof maintains a tamper-proof diploma registry.
