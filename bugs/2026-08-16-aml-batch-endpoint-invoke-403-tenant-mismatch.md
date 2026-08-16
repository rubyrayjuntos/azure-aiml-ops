---
title: Azure ML batch endpoint invoke returns 403 Tenant mismatch
id: AML-BATCH-403-TENANT-MISMATCH
status: Open
created: 2026-08-16
component: Azure Machine Learning – Batch Endpoints / Control Plane
severity: Blocks R2.1/R2.7/R2.9 (deploy→infer→drift proof)
labels: [azureml, batch-endpoint, invoke, tenant, auth, cli]
---

## Summary

- `az ml batch-endpoint invoke` returns `403 Tenant mismatch: Token tenant does not match resource tenant` against a workspace in tenant `[TENANT_A_ID]`, even though the signed-in account and the workspace both belong to `[TENANT_A_ID]` (confirmed via decoded token claims — `tid` matches the workspace's own `properties.tenantId`).
- The error is returned directly by Azure's own AML scoring frontdoor (`server: azureml-frontdoor`), not by the CLI or SDK.
- `batch-endpoint create` and `batch-deployment create` both succeed cleanly against the same workspace with the same credentials; only `invoke` fails.
- Reproduced on two separate, unrelated workspaces in the same subscription/tenant to rule out project-specific configuration.
- This blocks batch invocation needed for R2 evidence (deploy→infer→observe).

## Environment (redacted)

- Date/time: 2026-08-15 to 2026-08-16 (UTC-05)
- Subscription: `[SUBSCRIPTION_ID]`, Tenant: `[TENANT_A_ID]`
- Workspaces:
  - WS1: `mlw-azure-ai-ml-ops-dev` (rg: `rg-azure-ai-ml-ops-dev`) — this project
  - WS2: `mlw-azmlops-0001dev` (rg: `[RG2_NAME]`) — independent, older, previously-provisioned workspace unrelated to this project, used purely to rule out project-specific config
- Azure CLI:
  ```
  azure-cli: 2.89.1
  azure-cli-core: 2.89.1
  extensions: ml 2.44.1
  ```
- Auth: Entra ID (Microsoft Entra ID); `az account show` confirms `tenantId` matches the workspace's tenant
- Batch endpoint: `[ENDPOINT_NAME]` (WS1), `taxi-gha-bep-azmlops-0001dev` (WS2); compute: AmlCompute `[COMPUTE_NAME]`

## Expected

`az ml batch-endpoint invoke` succeeds when the signed-in principal and the workspace are in the same tenant, returning a job ID and starting batch scoring.

## Actual

`az ml batch-endpoint invoke` fails with HTTP 403 and a message indicating tenant mismatch, despite the token's `tid` claim matching the workspace's own tenant.

## Exact commands and diagnostic steps performed

1. **Verify tenant context**
   ```
   az account show --query "{tenantId: tenantId, user: user.name, subscription: id}" -o tsv
   ```
   Confirmed `tenantId` matches `[TENANT_A_ID]`.

2. **Confirm workspace tenant** — `az ml workspace show`'s own `properties.tenantId` matches the signed-in account's tenant.

3. **Invoke batch endpoint**
   ```
   az ml batch-endpoint invoke -n [ENDPOINT_NAME] -g rg-azure-ai-ml-ops-dev -w mlw-azure-ai-ml-ops-dev \
     --input [DATA_ASSET_URI]
   ```
   Result: `403: Tenant mismatch: Token tenant does not match resource tenant`, returned by `server: azureml-frontdoor` (i.e. Azure's own scoring frontdoor, not the CLI/SDK layer).

## Diagnostic steps completed — all fail identically

- Data-asset input vs. raw HTTPS blob URL input.
- User-principal token vs. service-principal (GitHub Actions OIDC) token.
- Decoded JWT claims for both token types confirmed correct: `tid` matches the workspace's own `properties.tenantId`, `aud=https://ml.azure.com`.
- Endpoint and deployment deleted and fully recreated from scratch.
- `az ml workspace sync-keys` run.
- `auth_mode: key` attempted as a workaround — rejected outright by Azure with `AuthMode must be 'AADToken'` (batch endpoints only support AAD-token auth for this workspace configuration, so this isn't a viable routing-around).
- **Conclusive test:** the identical failure reproduced against a completely separate, older, previously-provisioned workspace and endpoint in the same subscription/tenant (`mlw-azmlops-0001dev` / `taxi-gha-bep-azmlops-0001dev`), unrelated to anything this project's Terraform/RBAC/templates touch.

## Reproduction control

- Repro attempted on WS2 (independent workspace, pre-existing endpoint) → identical 403.
- Re-authentication attempts: `az login --tenant [TENANT_A_ID]` (fresh interactive login), `az account clear` → `az login` → identical result both times.
- No role or RBAC changes made during tests; principal has the documented required roles on both workspaces and resource groups.

## Evidence artifacts

- `.azure/deployment-plan.md`, section "R2.1 blocker: batch-endpoint invoke fails with a genuine Azure-side auth rejection" (this project's own repo) — full narrative with timestamps as recorded during live testing on 2026-08-15/16.

## Non-solutions and constraints

We will not relax security (e.g., tenant-switching hacks, cross-tenant app registrations, or portal/console edits) to bypass the failure. All infrastructure changes in this project occur via Terraform saved-plan workflows; no console drift is permitted.

## Impact

Blocks R2 steps requiring real batch inference: initial serving proof (R2.1), `HEALTHY` drift-state population proof (R2.7), and induced `DRIFT_DETECTED` proof (R2.9).

## Request

- Engineering triage for the `403 Tenant mismatch` check on batch-endpoint invocation when the token's tenant ID and the resource's tenant ID are equal.
- Guidance on additional diagnostics to capture (e.g. correlation IDs / `x-ms-request-id` from the frontdoor response). We can reproduce on demand and supply correlation IDs from a fresh failing run.

## Filing status

Not yet filed as a formal Microsoft support case — this subscription does not currently have a support plan (`az support in-subscription tickets create` returns `InvalidSupportPlan`, confirmed with the correct problem classification `Model deployment and serving (Batch Endpoints) / Problem consuming Batch Endpoint`). This document is intended as a GitHub issue / Microsoft Q&A post, or as the evidence package for a future support ticket if a plan becomes available. Kept separate from `AML-DATA-IDENTITY-01`, which affects a different Azure ML subsystem (data access/mount on AmlCompute, not batch-endpoint control plane) and would route to a different engineering owner.

## Attachments checklist

- [ ] CLI logs with `--debug` (scrubbed)
- [ ] `az version` output
- [ ] `az ml workspace show` output for WS1 and WS2
- [ ] Endpoint/deployment ARM IDs
- [ ] Evidence log snippets from `.azure/deployment-plan.md`
