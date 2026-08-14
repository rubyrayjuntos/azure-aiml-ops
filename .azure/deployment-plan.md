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
| Azure ML clusters | 2 (training `cpu-training`, batch `cpu-batch`; both scale-to-zero, max 1 node) | 0 | 2 | 200 | ARM inventory; pass |
| VM-family vCPUs (`Standard_D2s_v3`, `standardDSv3Family`) | Up to 4 (2 nodes x 2 vCPUs, both max 1) | `Standard DSv3 Family vCPUs`: 0/65; `Total Regional vCPUs`: 0/73 (raised from 65 after a support-approved increase); `Dedicated vCPUs`: 0/0 (unchanged) | Not measured | See result | **`az vm list-skus` still reports `Standard_D2s_v3` `NotAvailableForSubscription` in `eastus`, identical to before the quota increase.** The approved increase raised `Total Regional vCPUs` but not whatever gates the SKU catalog restriction. This is the exact condition this candidate exists to test live, via `terraform apply` and a real `train.yml` job dispatch, rather than a static check |
| Azure ML workspace | 0 more (already live) | 3 | 3 | No count quota exposed by `az quota` | ARM inventory; pass |
| Storage account | 0 more (already live) | 7 | 7 | 250 per region/subscription default | ARM inventory; pass |
| Key Vault | 0 more (already live) | 4 | 4 | No count quota exposed | ARM inventory; pass |
| Log Analytics workspace | 0 more (already live) | 2 | 2 | No applicable count quota surfaced | ARM inventory; pass |
| Application Insights component | 0 more (already live) | 4 | 4 | No component-count quota surfaced | ARM inventory; pass |
| User-assigned identity | 1 (new: project compute identity `id-azure-ai-ml-ops-dev-compute`) | 2 | 3 | Provider limit or documented boundary | ARM inventory; pass |
| Azure role assignments | 1 more (new: `compute_storage`, `Storage Blob Data Contributor` on the project storage account) | 56 | 57 | 4,000 per subscription | ARM inventory; pass |

## 7. Validation checklist

- [x] Confirm the manifest tenant, subscription, region, environment, backend, and intended deployment identity.
- [x] Verify generation receipt and immutable platform/package provenance.
- [x] Run generated tests and Ruff.
- [x] Run the local lifecycle and retain local-only evidence without claiming Azure execution. (Not repeated this cycle; unchanged since the last local-first proof — this candidate only adds cloud compute opt-in, the local path is unaffected.)
- [x] Parse generated YAML and run Actionlint.
- [x] Run `terraform fmt -check -recursive`.
- [x] Run `terraform init -backend=false -lockfile=readonly` and `terraform validate`.
- [x] Review identity and RBAC references statically.
- [x] Run authenticated read-only quota, policy, backend, OIDC, RBAC, and state checks.
- [x] Populate validation proof and set `Validated` through the documented Azure validation workflow, including the one check that failed and why that's expected.

## 8. Validation proof

First candidate with cloud training/batch compute enabled (explicit opt-in; the local-first Dev profile requests zero Azure compute by default). This validation pass has **one deliberately-failing check**: `compute_sku_availability` / `compute_quota_sufficiency`. That's not being hidden or waived — it's the exact condition this whole candidate exists to test, live, via `terraform apply` and a real `train.yml` GitHub Actions job dispatch, per owner authorization on 2026-08-14 to resume Gate 1 workload evidence this way after ad-hoc CLI testing proved inconclusive (an unrelated storage-RBAC gap in the testing identity, not a compute-provisioning result).

| Check | Command | Result | Timestamp |
|---|---|---|---|
| Reproducible platform wheel | Reused the existing reproducible wheel; no platform code changed for this candidate (manifest-only change) | N/A — `sha256:c8a73fac24186f987c7b9341a0068645c85ba1dd828ea26100eb3af26a14704b`, previously verified byte-identical across two independent builds | 2026-08-14T20:20:00Z |
| Deterministic generation | Two independent `aiml-scaffold generate` runs from that wheel with the cloud-enabled manifest | Passed; byte-identical, `generated_files_digest sha256:da4693a0f556645c2d078108bbffc0a2668771980e18aa2406ece74b133e321f` | 2026-08-14T20:21:00Z |
| Offline doctor | `aiml-scaffold doctor --environment dev --no-cloud` | Passed | 2026-08-14T20:22:00Z |
| Python lint | `ruff check .` | Passed, no findings | 2026-08-14T20:22:00Z |
| YAML parse | Parsed every generated `.yml`/`.yaml` | Passed, 0 failures | 2026-08-14T20:22:00Z |
| Actionlint | `actionlint .github/workflows/*.yml` | Passed, no findings (including newly-rendered `train.yml`, `deploy-batch.yml`) | 2026-08-14T20:22:00Z |
| Terraform static validation | `terraform fmt -check -recursive`; `terraform init -backend=false -lockfile=readonly`; `terraform validate` | Passed with AzureRM 4.81.0; confirmed `compute_storage` role assignment uses `role_definition_name` (the earlier fix), not the path-ambiguous `role_definition_id` | 2026-08-14T20:23:00Z |
| Scenario and secret scan | Grep for `churn`/`taxi` scenario leakage and credential patterns | Passed; no leakage | 2026-08-14T20:23:00Z |
| Generated tests and lint (pinned environment) | CI run [`31838927739`](https://github.com/rubyrayjuntos/azure-aiml-ops/actions/runs/31838927739) on merge commit `2783ff79c0ca9840c704a3f431c4a5dae6a83c9c`: `pip install -c constraints.txt -e '.[dev]'`, `ruff check .`, `pytest`, `terraform fmt/init/validate` under Python 3.11 | Passed | 2026-08-14T20:39:45Z |
| Static RBAC review | Manual review of `infra/terraform/main.tf` | Passed; new `compute_storage` role assignment grants `Storage Blob Data Contributor` (by name) to the new compute UAMI, scoped to the project storage account only | 2026-08-14T20:44:00Z |
| Azure context and policy | `az account show`; `az policy assignment list` | Passed; active tenant/subscription match the manifest; one enforced `SecurityCenterBuiltIn` policy assignment | 2026-08-14T20:44:00Z |
| Capacity and inventory | `az resource list` by type; `az role assignment list` | Passed for all non-compute resources; counts recorded in section 6 | 2026-08-14T20:45:00Z |
| **Compute SKU availability** | `az vm list-skus --location eastus --size Standard_D2s_v3 --all` (same invocation `doctor` uses) | **Failed**: `NotAvailableForSubscription`, both `Location` and `Zone` restriction entries — identical to the pre-quota-increase result. A support-approved increase raised `Total Regional vCPUs` 65→73 on 2026-08-14, but `Dedicated vCPUs` remains `0/0` and the SKU catalog restriction is unchanged. Cross-checked: an ad-hoc `az ml compute create` (dedicated tier, min_instances=0) succeeded in creating a cluster *definition*, but that doesn't provision a node; a follow-up job submission to force real node allocation failed on an unrelated storage-RBAC gap in the testing identity before ever reaching the compute layer (`targetNodeCount` stayed `0`), so it produced no evidence either way. Owner reviewed this and authorized proceeding to a real plan/apply/job-dispatch as the only conclusive test | 2026-08-14T20:39:00Z |
| Compute quota sufficiency | Same `doctor` check, downstream of the SKU check above | Failed, same root cause | 2026-08-14T20:39:00Z |
| Authenticated doctor (full run) | `aiml-scaffold doctor --environment dev` (cloud-enabled) against the merged candidate | `overall_status: failed` — every check passed except the expected `active_identity_match` warning and the two compute checks above. No other regressions | 2026-08-14T20:39:00Z |

**Validated by:** Ray Swan / Claude. Status is set to `Validated` deliberately alongside a known-failing compute check, per explicit owner authorization to resume Gate 1 by testing the real quota question through `terraform apply` and a live `train.yml` dispatch rather than trusting either static signal (SKU catalog vs. ad-hoc cluster-creation test), which disagreed with each other.

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
| 1.2.0 | 2026-08-12 | 2026-08-14 | Ray Swan / Claude | Enabled cloud training and batch compute (explicit opt-in, `Standard_D2s_v3`, dedicated, scale-to-zero). Completed the Azure validation workflow and set status to `Validated`, deliberately alongside a documented failing `compute_sku_availability` check — that check is the exact thing this candidate exists to test live via apply and a real job dispatch. |
| 1.1.0 | 2026-08-12 | 2026-08-12 | Ray Swan / AIML-SCAFFOLD | Generated the local-first compute policy with independent explicit Azure training and batch fallbacks, one-node Dev ceiling, and charged-compute authorization boundary. |
| 1.0.0 | 2026-08-12 | 2026-08-12 | Ray Swan / AIML-SCAFFOLD | Generated the initial R1 Terraform deployment-governance plan; live validation remains pending. |
