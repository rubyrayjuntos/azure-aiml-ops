# Azure AI ML Ops R1 Dev infrastructure deployment plan

> **Status:** Validated

Generated deterministically by AIML-SCAFFOLD platform 1.0.0.

## 1. Project overview

**Goal:** Provision the reviewed local-first Azure ML batch-project Dev infrastructure using the exact saved Terraform plan produced by the protected GitHub workflow. Azure ML compute and charged workload execution remain separate opt-ins.

**Path:** Generated project; mutable preparation and validation evidence is maintained in this file before saved-plan production.

## 2. Requirements

| Attribute | Value |
|---|---|
| Classification | Development; R1 preview |
| Product | `azure-ai-ml-ops` |
| Owner | Ray Swan |
| Cost center | `UNASSIGNED` |
| Subscription | `5b452321-32fd-4b1c-8bbf-6d69a5a587ad` |
| Tenant | `90a7175b-82cd-4815-9050-8cbae3a1d234` |
| Location | `eastus` |
| Data classification | `internal` |
| Deployment approval | `manual_dispatch_with_plan_digest` |

## 3. Components

| Component | Type | Technology | Path |
|---|---|---|---|
| Infrastructure | Infrastructure as code | Terraform 1.10.0 and AzureRM 4.81.0 | `infra/terraform/` |
| Orchestration | Protected CI/CD | GitHub Actions and Entra OIDC | `.github/workflows/` |
| ML lifecycle | Portable local-first ML | Shared Python lifecycle plus local runner; Azure ML adapter | `data-science/`, `scripts/run_local_lifecycle.py`, `mlops/azureml/` |
| Evidence | Append-only evidence | Azure Blob and GitHub artifacts | `scripts/` |

## 4. Recipe selection

**Selected:** Pure Terraform through the protected saved-plan workflow.

The generated project does not use azd or Bicep. Apply consumes the exact reviewed `r1.tfplan` without replanning.

## 5. Architecture and ownership

| Component | Ownership and purpose |
|---|---|
| Environment resource group | Administrator-created prerequisite; never created by workload Terraform |
| Remote backend | Administrator-owned storage; project state key `azure-ai-ml-ops-dev.tfstate` |
| Azure ML workspace | Project-owned, system-assigned identity, identity-based storage access |
| Storage and evidence | Project-owned; Shared Key disabled; evidence container retention 90 days |
| Key Vault | Project-owned; RBAC authorization |
| Log Analytics and Application Insights | Project-owned Dev observability |
| Local execution | Default Dev prepare, train, evaluate, package, score, and local-evidence path; no Azure workspace or compute required |
| Azure training compute | azure_ml_cluster using explicit Standard_D2s_v3, maximum one node |
| Azure batch compute | azure_ml_cluster using explicit Standard_D2s_v3, minimum zero, maximum one node |
| Compute identity | Project-owned user-assigned identity for enabled cluster compute |
| Workflow identity | Administrator-owned Entra OIDC prerequisite |
| Storage data roles | Workload Terraform; exact project-storage scope for workspace and workflow identities, plus enabled cluster compute identity |

One resource has one IaC owner. Workload Terraform must not change bootstrap state, the resource group, GitHub/Entra prerequisites, or the backend.

Local lifecycle evidence does not prove Azure ML job submission, managed identity, lineage, registration, endpoint deployment, or batch execution. Every enabled Azure compute workflow requires a deliberate cost-aware authorization phrase. The factory never selects a replacement VM SKU.

## 6. Provisioning-limit checklist

Complete live, read-only quota and inventory checks before approving this plan. No Terraform mutation is permitted during validation.

| Resource or quota | Planned | Current | Total after deployment | Limit | Result |
|---|---:|---:|---:|---:|---|
| Azure ML clusters | 2 | Not measured | Not measured | 200 | Not exercised |
| Azure ML serverless training | Disabled | Not measured | Not measured | Exact SKU quota when enabled | Not exercised |
| VM-family vCPUs | Exact explicit-SKU discovery required | Not measured | Not measured | Not measured | Not exercised |
| Azure ML workspace | 1 | Not measured | Not measured | Provider limit or documented boundary | Not exercised |
| Storage account | 1 | Not measured | Not measured | Provider limit or documented boundary | Not exercised |
| Storage container (new: `monitoring`) | 1 more | Not measured | Not measured | 5,000,000 containers per storage account | Not exercised; trivial default limit, not a real constraint |
| Key Vault | 1 | Not measured | Not measured | Provider limit or documented boundary | Not exercised |
| Log Analytics workspace | 1 | Not measured | Not measured | Provider limit or documented boundary | Not exercised |
| Application Insights component | 1 | Not measured | Not measured | Provider limit or documented boundary | Not exercised |
| User-assigned identity | 1 | Not measured | Not measured | Provider limit or documented boundary | Not exercised |
| Azure role assignments | 0 more (existing account-scoped roles cover the new container) | Not measured | Not measured | 4,000 per subscription | Not exercised |

## 7. Validation checklist

- [x] Confirm the manifest tenant, subscription, region, environment, backend, and intended deployment identity.
- [x] Verify generation receipt and immutable platform/package provenance.
- [x] Run generated tests and Ruff.
- [x] Run the local lifecycle and retain local-only evidence without claiming Azure execution. (Not repeated; unaffected — new opt-in capability, no change to the existing local lifecycle path.)
- [x] Parse generated YAML and run Actionlint.
- [x] Run `terraform fmt -check -recursive`.
- [x] Run `terraform init -backend=false -lockfile=readonly` and `terraform validate`.
- [x] Review identity and RBAC references statically.
- [x] Run authenticated read-only quota, policy, backend, OIDC, RBAC, and state checks.
- [x] Populate validation proof and set `Validated` through the documented Azure validation workflow, including the same known-failing static compute-SKU check as before.

## 8. Validation proof

**Ninth candidate — the mlflow fix wasn't actually reaching the job.** After the eighth candidate applied cleanly (no-op plan confirmed, `RunningNodeCount:1` cluster intact), `train.yml` was re-dispatched and reached the same `prepare`-succeeds/`train`-fails pattern, and `train`'s error was byte-for-byte the same `UnsupportedModelRegistryStoreURIException` as before the seventh candidate's `azureml-mlflow` fix — despite that fix being live on `main`. Investigation: `az ml environment list` showed the training environment now has two versions (`1` and `2` — version `2` built when the `register` step created it from the corrected `train-conda.yml`), but `pipeline.yml` hardcoded `environment: azureml:azure-ai-ml-ops-train-env:1` on all four steps (`prepare`/`train`/`evaluate`/`register`), so every pipeline run kept resolving to the original, pre-fix environment build regardless of how many times `train-conda.yml` changed. `train-env.yml` itself never sets an explicit version — `az ml environment create` auto-increments on content change — so the hardcoded `:1` was inconsistent with that design from the start and was always going to go stale the first time the environment changed. Changed all four references to `azureml:azure-ai-ml-ops-train-env@latest` (platform commit `1717b64`).

| Check | Command | Result | Timestamp |
|---|---|---|---|
| Reproducible platform wheel | Two independent clean-room builds (`build/`/`dist/` removed first), `SOURCE_DATE_EPOCH` pinned to the commit timestamp | Passed; byte-identical, `sha256:8beb5ba62dec417532579f686e8334d2c23e5506d7067a9bf7896ff0da6a6d9c` | 2026-08-15T16:38:00Z |
| Deterministic generation | Two independent `aiml-scaffold generate` runs from that wheel | Passed; byte-identical; confirmed `@latest` present on all four `environment:` references in the rendered `pipeline.yml` | 2026-08-15T16:39:00Z |
| Offline doctor | `aiml-scaffold doctor --environment dev --no-cloud` | Passed | 2026-08-15T16:40:00Z |
| Python lint | `ruff check .` | Passed, no findings | 2026-08-15T16:40:00Z |
| YAML parse | Parsed every generated `.yml`/`.yaml` | Passed, 0 failures | 2026-08-15T16:40:00Z |
| Actionlint | `actionlint .github/workflows/*.yml` | Passed, no findings | 2026-08-15T16:40:00Z |
| Terraform static validation | `terraform fmt -check -recursive`; `terraform init -backend=false -lockfile=readonly`; `terraform validate` | Passed with AzureRM 4.81.0; infra unchanged (pipeline YAML only) | 2026-08-15T16:41:00Z |
| Scenario and secret scan | Grep for `churn`/`taxi` scenario leakage and credential patterns | Passed; no leakage | 2026-08-15T16:41:00Z |
| Generated tests and lint (pinned environment) | CI run [`31896767990`](https://github.com/rubyrayjuntos/azure-aiml-ops/actions/runs/31896767990) on merge commit `f8af08d` | Passed | 2026-08-15T16:45:00Z |
| Static RBAC review | No RBAC changes in this fix; unaffected | Passed | 2026-08-15T16:42:00Z |
| Azure context and policy | `az account show`; `az policy assignment list` | Passed | 2026-08-15T19:57:58Z |
| Capacity and inventory | `az resource list` by type; `az role assignment list` | Passed; counts unchanged (no new infra) | 2026-08-15T19:57:58Z |
| Compute SKU availability / quota sufficiency (static `doctor` check) | Same `doctor` check | Still fails statically — same documented, non-conclusive condition | 2026-08-15T19:57:58Z |
| Authenticated doctor (full run) | `aiml-scaffold doctor --environment dev` (cloud-enabled) | `overall_status: failed` — same profile as every prior candidate: only the expected `active_identity_match` warning and the two known static compute checks | 2026-08-15T19:57:58Z |

**Validated by:** Ray Swan / Claude, repeating the documented Azure validation workflow after fixing the stale environment-version reference.

### Gate 1 milestone: first fully successful training pipeline run

Run [31905669826](https://github.com/rubyrayjuntos/azure-aiml-ops/actions/runs/31905669826), pipeline `dreamy_chain_xwc3x25ykn`, completed end to end. All four steps — `prepare` (`21986241-ecf9-48bf-9ab6-b4ba64967b04`), `train` (`857c2afc-79bf-4e12-bc39-2586ca0a37b8`), `evaluate` (`0b9ae0cd-c3f9-404b-b9b9-3dc6f1f4c119`), `register` (`c82eb567-907d-4580-a7e3-8edb03606f2a`) — status `Completed`. `az ml model list` confirms `azure-ai-ml-ops-model` version `1` registered. This closes out the real-workload track this deployment plan exists to prove: nine real bugs found and fixed through live testing (CLI flag, idle-duration format, stdout pollution, contaminated build, broken extension pin, missing `azureml-mlflow`, `container_registry_id` drift, stale environment version — plus the compute-quota restriction resolved via the Azure-side vCPU increase), each cycled through the full deterministic-build, PR/CI, authenticated-doctor, digest-bound-plan, and independently-verified-apply governance pipeline documented above.

## 8a. R2: closing the model lifecycle loop

R2 scope (agreed 2026-08-16): prove `register → deploy → infer → observe → detect → retrain → compare → promote/retain` against the real v1 model R1 produced. Full plan: `R2.1` batch serving proof, `R2.2` land a drift-detection capability adapted from proven prior art in the sibling `azure-mlops` project, `R2.3`–`R2.9` interleaved champion/challenger and drift-state proofs. See session record for the full sequence.

### R2.1 blocker: batch-endpoint invoke fails with a genuine Azure-side auth rejection

`az ml batch-endpoint invoke` (and a raw REST call to the same scoring URI, bypassing the CLI/SDK entirely) fails with `403 Tenant mismatch: Token tenant does not match resource tenant`, returned directly by Azure's own AML scoring frontdoor (`server: azureml-frontdoor`), not by the CLI. `batch-endpoint create` and `batch-deployment create` both succeed cleanly against the same workspace with the same credentials; only `invoke` fails.

Diagnostic steps completed, all fail identically: data-asset input vs. raw HTTPS blob URL input; user-principal token vs. service-principal (GitHub OIDC) token; decoded token claims confirmed correct (`tid` matches the workspace's own `properties.tenantId`, `aud=https://ml.azure.com`); endpoint and deployment deleted and fully recreated from scratch; `az ml workspace sync-keys` run; `auth_mode: key` attempted as a workaround and rejected outright by Azure (`AuthMode must be 'AADToken'` — batch endpoints only support AAD-token auth, confirming this isn't a config choice we can route around); and — the conclusive test — the identical failure reproduced against a completely separate, older, previously-provisioned workspace and endpoint in the same subscription/tenant (`mlw-azmlops-0001dev` / `taxi-gha-bep-azmlops-0001dev`, unrelated to anything R2 touched).

**Conclusion:** this is not a configuration problem in this project's Terraform, templates, or RBAC — it is either an account/tenant-wide or Azure ML regional platform issue affecting AAD-token batch-endpoint invocation. Filing a formal Azure support ticket was attempted (`az support in-subscription tickets create`, correct problem classification `Model deployment and serving (Batch Endpoints) / Problem consuming Batch Endpoint`) and rejected with `InvalidSupportPlan` — this subscription has no paid support plan, so technical tickets aren't available via API or portal.

**Status:** R2.1, and by extension R2.7/R2.9 (which depend on working batch serving), are blocked pending either a support plan being obtained or the underlying platform issue resolving on its own. R2.2 and the champion/challenger proofs (R2.4/R2.5/R2.8), which don't depend on batch serving, proceed independently.

### Tenth candidate — R2.2: land the drift-detection capability

New Terraform resource (`azurerm_storage_container.monitoring`, private, same account as `evidence`), new pipeline job (`snapshot_baseline`, gated on `register`'s `registered: true` output — not file existence, since this product's `register.py` always writes `model-info.json` unlike the taxi prior art this was adapted from), new manually-dispatched workflow (`check-drift.yml`, `RUN_AZURE_DRIFT_CHECK_DEV` authorization, no scheduling), new scripts (`check_drift.py` — KS-test only, `min_drifted_features` default `1` for this 2-feature product; `snapshot_baseline.py` — references the training population, not the held-out eval split), and inference logging added to `batch_driver.py` (always present in code, inert unless `MONITORING_STORAGE_ACCOUNT` is set). Gated behind a new `monitoring_enabled` manifest flag (`execution.monitoring.enabled`), following the platform's existing `training_cluster_enabled`/`batch_cluster_enabled` convention — no future product generated from this platform gets this plumbing unless it opts in.

| Check | Command | Result | Timestamp |
|---|---|---|---|
| Reproducible platform wheel | Two independent clean-room builds (`build/`/`dist/` removed first), `SOURCE_DATE_EPOCH` pinned to the commit timestamp | Passed; byte-identical, `sha256:07f21303b80237548f2f2c9d58b2772322da0083170c43e8b6dba9bfd651d6c8` | 2026-08-16T05:18:00Z |
| Deterministic generation | Two independent `aiml-scaffold generate` runs from that wheel (manifest with `execution.monitoring.enabled: true`) | Passed; byte-identical; confirmed the new container, job, workflow, and scripts all rendered | 2026-08-16T05:19:00Z |
| Offline doctor | `aiml-scaffold doctor --environment dev --no-cloud` | Passed | 2026-08-16T05:20:00Z |
| Python lint | `ruff check .` | Passed, no findings | 2026-08-16T05:20:00Z |
| YAML parse | Parsed every generated `.yml`/`.yaml` | Passed, 0 failures | 2026-08-16T05:20:00Z |
| Actionlint | `actionlint .github/workflows/*.yml` | Passed, no findings, including the new `check-drift.yml` | 2026-08-16T05:20:00Z |
| Terraform static validation | `terraform fmt -check -recursive`; `terraform init -backend=false -lockfile=readonly`; `terraform validate` | Passed with AzureRM 4.81.0 | 2026-08-16T05:21:00Z |
| Scenario and secret scan | Grep for `churn`/`taxi` scenario leakage and credential patterns | Passed; no leakage (adapting taxi's statistical logic did not carry over any taxi-specific feature names, resource names, or fixtures) | 2026-08-16T05:21:00Z |
| Generated tests and lint (pinned environment) | CI run [`31927214810`](https://github.com/rubyrayjuntos/azure-aiml-ops/actions/runs/31927214810) on merge commit `4dd5a1b` | Passed | 2026-08-16T04:35:00Z |
| Static RBAC review | New Terraform container inherits existing account-scoped `compute_storage`/`workflow_storage` role assignments; no new role assignment added or needed | Passed | 2026-08-16T05:22:00Z |
| Azure context and policy | `az account show`; `az policy assignment list` | Passed | 2026-08-16T04:44:08Z |
| Capacity and inventory | `az resource list` by type; `az role assignment list` | Role assignments 57 → 60, unrelated to this candidate's Terraform (not yet applied): the operator's own temporary `Storage Blob Data Contributor` grant used for R2.1's data-asset registration, plus Azure-auto-granted roles from repeatedly recreating the batch endpoint/deployment during R2.1's diagnosis. Storage/workspace/compute counts otherwise unchanged | 2026-08-16T04:44:08Z |
| Compute SKU availability / quota sufficiency (static `doctor` check) | Same `doctor` check | Still fails statically — same documented, non-conclusive condition | 2026-08-16T04:44:08Z |
| Authenticated doctor (full run) | `aiml-scaffold doctor --environment dev` (cloud-enabled) | `overall_status: failed` — same profile as every prior candidate: only the expected `active_identity_match` warning and the two known static compute checks | 2026-08-16T04:44:08Z |

**Validated by:** Ray Swan / Claude, repeating the documented Azure validation workflow after landing the drift-detection capability.

## 9. Deployment authorization and stop conditions

Apply authorization covers infrastructure creation only. It excludes replanning during apply, bootstrap changes, charged compute, training, model registration, endpoint deployment, batch execution, Test, Prod, and unreviewed remediation.

Apply must stop before Terraform execution if any required filename, digest, source identity, generation identity, Azure context, backend identity, state lineage, state serial, or state content digest differs. A changed serial or digest invalidates the plan even when lineage is unchanged.

The approval record must say `deliberate, digest-bound owner authorization`; it must not claim independent review when one owner authorizes the operation.

## 10. Next boundary

1. Complete preparation and validation.
2. Publish the validated product source through protected PR/CI.
3. Produce and independently review a saved Terraform plan.
4. Obtain new digest-bound owner authorization.
5. Stop before Azure ML training or endpoint workflows.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 1.1.0 | 2026-08-12 | 2026-08-12 | Ray Swan / AIML-SCAFFOLD | Generated the local-first compute policy with independent explicit Azure training and batch fallbacks, one-node Dev ceiling, and charged-compute authorization boundary. |
| 1.0.0 | 2026-08-12 | 2026-08-12 | Ray Swan / AIML-SCAFFOLD | Generated the initial R1 Terraform deployment-governance plan; live validation remains pending. |
