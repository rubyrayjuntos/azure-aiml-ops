---
title: AML-DATA-IDENTITY-01 — rslex requires SAS for new uri_file content despite identity prerequisites
id: AML-DATA-IDENTITY-01
status: Open
created: 2026-08-16
component: Azure Machine Learning – Data Access (rslex mount) on AmlCompute
severity: Blocks R2.5/R2.8 directly; R2.6 transitively
labels: [azureml, data, identity, rslex, amlcompute, uri_file, mount, sas]
---

## Summary

- On AmlCompute, `rslex` fails to mount new `uri_file` data-asset content unless key-based (account-key-derived) SAS is available, even when every Microsoft-documented identity-based-access prerequisite is satisfied.
- With storage shared keys disabled and the workspace configured for identity-based data access, mounting a data asset that points at newly written blob content fails; re-enabling shared keys makes the identical pipeline succeed with no other change; disabling shared keys again reproduces the failure.
- This blocks baseline capture and challenger-promotion steps that require reading newly registered training data via identity.

## Environment (redacted)

- Date/time: 2026-08-16 (UTC)
- Subscription: `[SUBSCRIPTION_ID]`, Tenant: `[TENANT_A_ID]`
- Workspace: `mlw-azure-ai-ml-ops-dev` (rg: `rg-azure-ai-ml-ops-dev`)
- Storage: `stazureaimlopscffddc57`
  - Shared Key access: disabled (`allowSharedKeyAccess=false`) for all failing runs
  - RBAC (`storage_account_access_type`): `Identity`
- Identities and roles:
  - Compute user-assigned identity: `id-azure-ai-ml-ops-dev-compute`, role **Storage Blob Data Contributor** on the storage account, scope `/subscriptions/[SUBSCRIPTION_ID]/resourceGroups/rg-azure-ai-ml-ops-dev/providers/Microsoft.Storage/storageAccounts/stazureaimlopscffddc57`
  - Workspace system-assigned identity: also holds **Storage Blob Data Contributor** (auto-granted by the `Microsoft.MachineLearningServices` resource provider when `storage_account_access_type=Identity`)
- Azure CLI:
  ```
  azure-cli: 2.89.1
  extensions: ml 2.44.1  (confirmed latest available: `az extension list-versions --name ml`)
  ```
- Also reproduced directly against `azure-ai-ml` Python SDK `1.34.1` (latest PyPI release at time of testing), bypassing the CLI entirely — same failure, ruling out a CLI-specific regression.
- Terraform: AzureRM provider `4.81.0` manages the workspace/storage account. Confirmed via `terraform providers schema -json` that `azurerm_machine_learning_workspace` exposes no `system_datastores_auth_mode`-equivalent argument in this provider version — the setting below was Azure ML's own default, not explicit Terraform config.
- `rslex` version: not printed as an explicit version string in the job logs; observed component paths are `rslex-fuse`, `rslex-azure-storage`, `rslex-azureml`, `rslex_http_stream`.

## Configuration preconditions confirmed at time of failure

```
$ az ml workspace show -g rg-azure-ai-ml-ops-dev -n mlw-azure-ai-ml-ops-dev --query system_datastores_auth_mode -o tsv
identity

$ az storage account show -g rg-azure-ai-ml-ops-dev -n stazureaimlopscffddc57 --query allowSharedKeyAccess -o tsv
False

$ az role assignment list --scope <storage-account-id> -o table
Principal (id-azure-ai-ml-ops-dev-compute)   Storage Blob Data Contributor   <storage-account-id>
```

All three of Microsoft's documented preconditions for identity-based AmlCompute data access were satisfied, yet the mount still failed.

## Expected

AML jobs on AmlCompute can mount/read newly created blobs referenced by a `uri_file` data asset via the compute's managed identity (no SAS), given the preconditions above.

## Actual

The pipeline's `prepare` step (a `PythonScriptStep` on AmlCompute) fails to mount the `uri_file` input. Job-level error:

```
{"Error":{"Code":"ServiceError","Message":"Failed to mount URI
  azureml://.../datastores/workspaceblobstore/paths/azure-ai-ml-ops-training-data/8/train.csv
  at mount point /mnt/azureml/cr/j/.../cap/data-capability/wd/INPUT_input", ...},
  "ComponentName":"CommonRuntime"}
```

`rslex.log` (`system_logs/data_capability/rslex.log.<date>`, retrieved by downloading directly from the `workspaceartifactstore` datastore's container via `az storage blob download --auth-mode login`, since `az ml job download` itself hits the identical bug class on read — see "Related, separate bug" below):

```
INFO rslex_azureml::data_store::resolver: [CachedResolver::resolve()] DataStore resolved
  info=DataStoreInfo { id: "workspaceblobstore", ... }
  datastore_type=Some(AzureBlob) account_name=Some("stazureaimlopscffddc57") ...
ERROR rslex_azure_storage::blob_stream_handler::azure_blob_error:
  unexpected azure blob error code in x-ms-error-code header
  error_code=KeyBasedAuthenticationNotPermitted parse_error=VariantNotFound
WARN rslex_http_stream::http_client::response: non-successful response
  Status: 403 Forbidden
  Headers: { "x-ms-error-code": "KeyBasedAuthenticationNotPermitted", ... }
  method=HEAD request_uri=https://stazureaimlopscffddc57.blob.core.windows.net/<workspaceblobstore-container>/azure-ai-ml-ops-training-data/8/train.csv
ERROR rslex::python_error_handling:
  Execution has failed with: ScriptExecution.StreamAccess.Authentication,
  Authentication failed when trying to access the stream.
```

`KeyBasedAuthenticationNotPermitted` is only returned when Azure detects the request was signed with key-derived credentials — this confirms `rslex` itself chose to sign the HEAD request with a key-derived mechanism rather than attempting AAD/managed-identity auth, despite the datastore being registered with `credentials: {}` (empty/identity-based) and `system_datastores_auth_mode=identity` at the workspace level.

## A/B verification (identity vs. shared key), each isolating one variable

| Run | Change | Result |
|---|---|---|
| `identity_fail` — pipeline `affable_candle_338zy0y9c6`, prepare child `57ff63d7-dd06-4abe-9b84-77ef51868adf` | Baseline: keys disabled, new data-asset content (version 8, registered via AAD blob upload + datastore-path reference) | Failed: `KeyBasedAuthenticationNotPermitted` at mount, ~06:24:55Z |
| Re-dispatch (transient-failure check) | No change | Failed identically |
| `azure-ai-ml==1.34.1` SDK directly instead of pinned CLI `2.44.1` | Registration path only (not mount) | Same `KeyBasedAuthenticationNotPermitted`, ruling out an old-SDK-specific bug |
| Blob path convention: custom path vs. the `LocalUpload/<hash>/<filename>` prefix convention used internally by every pre-existing (working) data-asset version | `identity_fail_again` — pipeline `gifted_bird_dz7r42k80q`, prepare child `37e68ab5-8a55-4487-8a66-55ac564f9d00`, data-asset version 200 registered under a manually-constructed `LocalUpload/`-prefixed path | Failed identically at ~06:52:12Z — not a path-naming issue |
| Direct read of the target blob via `az storage blob show --auth-mode login` (AAD, compute-unrelated identity holding `Storage Blob Data Contributor`) | n/a | Succeeds — blob is fully readable via AAD; failure is specific to `rslex`'s own mount-time credential choice, not a genuine authorization gap |
| `az storage account update --allow-shared-key-access true`, then re-run the *exact same* previously-failing data asset (version 8) with no other change | `sas_success` — pipeline `tender_dress_xf3d79yttv`, created 2026-08-16T06:59:04Z | `prepare`: Completed. Full pipeline (`prepare`→`train`→`evaluate`→`register`→`snapshot_baseline`) completed end-to-end |
| `az storage account update --allow-shared-key-access false` immediately after the successful run | Restore declared state | Confirmed `allowSharedKeyAccess: False`; no drift left in Terraform's tracked state |

## Related, separate bug (upload path)

Before reaching the mount failure above, registering a data asset from **new local content** via `az ml data create --type uri_file --path <local-file>` (or the SDK's `MLClient.data.create_or_update()` with a local path) also fails with the identical `KeyBasedAuthenticationNotPermitted`, reproduced even from a caller identity that already holds `Storage Blob Data Contributor` directly on the storage account. This is a distinct failure in the *upload* path (client-side), separate from the *mount* failure above (compute-side), though both surface the identical error code and appear to stem from the same underlying pattern: some Azure ML SDK/CLI/runtime code paths default to account-key-derived SAS generation and never attempt AAD/managed-identity auth, regardless of the caller's or compute's actual RBAC grants.

Workaround for the upload-side bug only: upload the blob directly via `az storage blob upload --auth-mode login` (pure AAD), then register the data asset from the resulting datastore path rather than a local path. This workaround does **not** help with the compute-mount-side bug — a data asset registered this way still fails to mount on AmlCompute with keys disabled (see `identity_fail` above, which used exactly this workaround).

## Minimal reproducible workflow

1. Create an Azure ML workspace with `storage_account_access_type=Identity`; confirm `system_datastores_auth_mode=identity`.
2. Set `allowSharedKeyAccess=false` on the workspace's storage account.
3. Grant the compute cluster's managed identity `Storage Blob Data Contributor` on the storage account.
4. Upload any new blob via `az storage blob upload --auth-mode login` and register a `uri_file` data asset pointing at it (`azureml://datastores/workspaceblobstore/paths/<path>`).
5. Submit a pipeline job on AmlCompute that mounts this asset as an input (`mode: ro_mount`, the default).
6. Observe the job fail with `KeyBasedAuthenticationNotPermitted` inside `rslex.log`.
7. Re-enable `allowSharedKeyAccess=true` with no other change; re-submit the identical job — it succeeds.

## Why this matters

Every data asset registered during this project's initial setup happened to reuse identical, previously-uploaded content across repeated test runs (versions 1–6 of the same asset, byte-identical). Azure ML's own asset registration silently deduplicates identical content by hash and skips the underlying blob write — so those runs never actually exercised the "new content" code path, and the bug went unnoticed until content genuinely changed. Any project that (a) disables storage account shared-key access per Microsoft's own documented recommendation, and (b) needs to feed new training/inference data into an AmlCompute pipeline as it evolves, will hit this.

## Evidence artifacts

- `.azure/deployment-plan.md`, section "AML-DATA-IDENTITY-01" (this project's own repo) — full narrative, controls table, and diagnostic evidence as recorded live on 2026-08-16.
- Job run IDs referenced above: `affable_candle_338zy0y9c6` / `57ff63d7-dd06-4abe-9b84-77ef51868adf` (identity_fail), `gifted_bird_dz7r42k80q` / `37e68ab5-8a55-4487-8a66-55ac564f9d00` (identity_fail_again), `tender_dress_xf3d79yttv` (sas_success).

## Non-solutions and constraints

We will not keep shared keys enabled or embed long-lived SAS/key material as a standing "workaround." This project's governance requires identity-based access with no long-lived secrets, and the owner explicitly chose to restore the hardened state (`allowSharedKeyAccess=false`) rather than normalize the diagnostic exception.

**Terraform note:** as of AzureRM provider `4.81.0`, no argument exists on `azurerm_machine_learning_workspace` to declare `system_datastores_auth_mode` — it was set by Azure ML's own default provisioning behavior, not by explicit Terraform config, and cannot currently be managed/asserted via this provider version (confirmed by direct schema inspection, not by trial and error).

## Impact

Blocks R2.5 (winning-challenger baseline snapshot) and R2.8 (evaluation-crash failure containment, which also requires new training-data content) directly; R2.6 (`INSUFFICIENT_DATA` drift state) transitively, since it depends on a baseline created by R2.5.

## Request

- Engineering triage for `rslex`'s credential resolution: honor identity-based access (`system_datastores_auth_mode=identity`) for `uri_file` assets pointing at content added after workspace/datastore provisioning, provided the compute identity has the documented RBAC.
- Guidance on any additional datastore or asset-level setting required to force identity-only mount resolution for new content, if one exists outside what's currently documented.

## Filing status

Not yet filed as a formal Microsoft support case — this subscription does not currently have a support plan (`az support in-subscription tickets create` returns `InvalidSupportPlan`, confirmed independently for this issue). This document is intended as a GitHub issue against `Azure/azure-cli-extensions` (the `ml` extension) and/or `Azure/azureml-examples`, or a Microsoft Q&A post, and to serve as the evidence package if/when a support plan becomes available. Kept separate from `AML-BATCH-403-TENANT-MISMATCH`, which affects a different Azure ML subsystem (batch-endpoint control plane, not data access/mount) and would route to a different engineering owner.

## Attachments checklist

- [ ] Job logs for failing and succeeding runs (scrubbed)
- [ ] `az version` and extension versions
- [ ] Storage account properties (`allowSharedKeyAccess` state across tests)
- [ ] Role assignment exports for compute UAI and workspace MSI
- [ ] Data asset and job YAML used for repro
- [ ] `.azure/deployment-plan.md` excerpts with timestamps
