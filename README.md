# BlockProof – Smart Contract Backend

Production-ready Solidity backend that powers BlockProof’s verifiable diploma network. Universities can anchor credential fingerprints on-chain, students keep ownership inside embedded wallets (Privy/Dynamic), and employers verify authenticity instantly.

## Highlights

- **Role-gated issuance:** `superAdmin`, registrars, institutions, and controllers each have scoped permissions.
- **Student-owned credentials:** Only the fingerprint is on-chain; the full diploma stays inside the student’s embedded wallet vault.
- **Instant verification:** Public read functions (`credentialStatus`, `verifyFingerprint`) allow employers to validate QR payloads in seconds.
- **Operational safety:** Pause switch, unique fingerprint enforcement, revocation trail, and controller rotation for compromised keys.

## Repo Structure

| Path | Description |
| --- | --- |
| `contracts/BlockProofCredentialVault.sol` | Core Solidity contract with NatSpec comments. |
| `docs/ARCHITECTURE.md` | Deeper explanation of data model, flows, and wallet strategy. |

## Development

1. Install your preferred EVM toolchain (Foundry/Hardhat) and point it to the `contracts` folder.
2. Compile: `forge build` or `npx hardhat compile`.
3. Deploy: supply constructor args (none) and then call the role-management functions via scripts or a multisig.
4. Integrate off-chain services following the flows documented in `docs/ARCHITECTURE.md`.

## Credential Lifecycle

1. **Onboard university:** registrar calls `upsertInstitution`.
2. **Delegate operators:** institution or registrar calls `setInstitutionController`.
3. **Issue diploma:** controller submits `issueCredential` with student wallet + fingerprint + URIs.
4. **Verify:** employer scans QR and calls `credentialStatus` + `verifyFingerprint`.
5. **Revoke (if needed):** controller calls `revokeCredential`.

See the architecture doc for hashing guidance, QR payload formats, and embedded wallet considerations aligned with Privy/Dynamic.
