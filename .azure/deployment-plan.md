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
| Azure ML clusters | 0 more (already live) | 2 | 2 | 200 | ARM inventory; pass |
| VM-family vCPUs (`Standard_D2s_v3`) | 0 more | Same documented condition as the prior three candidates | Not measured | See result | Unrelated to this fix (CLI stdout-suppression only) |
| Azure ML workspace | 0 more (already live) | 3 | 3 | No count quota exposed by `az quota` | ARM inventory; pass |
| Storage account | 0 more (already live) | 5 | 5 | 250 per region/subscription default | ARM inventory; pass |
| Key Vault | 0 more (already live) | 3 | 3 | No count quota exposed | ARM inventory; pass |
| Log Analytics workspace | 0 more (already live) | 3 | 3 | No applicable count quota surfaced | ARM inventory; pass |
| Application Insights component | 0 more (already live) | 3 | 3 | No component-count quota surfaced | ARM inventory; pass |
| User-assigned identity | 0 more (already live) | 3 | 3 | Provider limit or documented boundary | ARM inventory; pass |
| Azure role assignments | 0 more (already live) | 57 | 57 | 4,000 per subscription | ARM inventory; pass |

Storage account and Key Vault counts dropped from the prior candidate (7→5, 4→3) due to the separately authorized cost-hygiene cleanup of the sibling `azure-mlops` taxi reference project (unused `ml-registry` resource group deletion); unrelated to this fix.

## 7. Validation checklist

- [x] Confirm the manifest tenant, subscription, region, environment, backend, and intended deployment identity.
- [x] Verify generation receipt and immutable platform/package provenance.
- [x] Run generated tests and Ruff.
- [x] Run the local lifecycle and retain local-only evidence without claiming Azure execution. (Not repeated; unaffected — workflow-only CLI-flag fix.)
- [x] Parse generated YAML and run Actionlint.
- [x] Run `terraform fmt -check -recursive`.
- [x] Run `terraform init -backend=false -lockfile=readonly` and `terraform validate`.
- [x] Review identity and RBAC references statically.
- [x] Run authenticated read-only quota, policy, backend, OIDC, RBAC, and state checks.
- [x] Populate validation proof and set `Validated` through the documented Azure validation workflow, including the same known-failing compute check as before.

## 8. Validation proof

Fourth cloud-compute candidate, correcting a real workflow bug found via the first live `train.yml` dispatch: after the `-w`/`-n` flag fix, the workflow reached `az ml workspace show` but the az CLI's extension auto-upgrade check printed `WARNING` lines to stdout during that call, and `$(...)` captured those lines instead of the tsv value — observed live as a corrupted `--storage-account "utils.py)"` argument to `emit_evidence.py`. The same pattern affects `az ml job create`, `az ml batch-endpoint invoke`, and the second `az ml workspace show` in `deploy-batch.yml`. Fixed by adding `--only-show-errors` to all four command substitutions (platform commit `c5c67ed90ff2e570771714ae894408788d19fd43`). Unrelated to the compute-quota question; `compute_sku_availability`/`compute_quota_sufficiency` are expected to keep failing statically, same documented condition as every candidate since cloud compute was enabled.

| Check | Command | Result | Timestamp |
|---|---|---|---|
| Reproducible platform wheel | Two independent clean-room builds, `SOURCE_DATE_EPOCH` pinned to the commit timestamp | Passed; byte-identical, `sha256:7c23acc39797be07d454da0d90fad03494530deb6829bfbb584abfb9c695f412` | 2026-08-15T05:30:00Z |
| Deterministic generation | Two independent `aiml-scaffold generate` runs from that wheel | Passed; byte-identical; confirmed `--only-show-errors` present on all four command substitutions in both workflows | 2026-08-15T05:31:00Z |
| Offline doctor | `aiml-scaffold doctor --environment dev --no-cloud` | Passed | 2026-08-15T05:32:00Z |
| Python lint | `ruff check .` | Passed, no findings | 2026-08-15T05:32:00Z |
| YAML parse | Parsed every generated `.yml`/`.yaml` | Passed, 0 failures | 2026-08-15T05:32:00Z |
| Actionlint | `actionlint .github/workflows/*.yml` | Passed, no findings | 2026-08-15T05:32:00Z |
| Terraform static validation | `terraform fmt -check -recursive`; `terraform init -backend=false -lockfile=readonly`; `terraform validate` | Passed with AzureRM 4.81.0 | 2026-08-15T05:33:00Z |
| Scenario and secret scan | Grep for `churn`/`taxi` scenario leakage and credential patterns | Passed; no leakage | 2026-08-15T05:33:00Z |
| Generated tests and lint (pinned environment) | CI run [`31846441252`](https://github.com/rubyrayjuntos/azure-aiml-ops/actions/runs/31846441252) on merge commit `9ce75e2` | Passed | 2026-08-15T05:36:00Z |
| Static RBAC review | No RBAC changes in this fix; unaffected | Passed | 2026-08-15T05:37:00Z |
| Azure context and policy | `az account show`; `az policy assignment list` | Passed | 2026-08-15T05:38:00Z |
| Capacity and inventory | `az resource list` by type; `az role assignment list` | Passed; counts unchanged by this fix (no new infra); storage/Key Vault drop reflects the separately authorized taxi-project cleanup, recorded in section 6 | 2026-08-15T05:45:00Z |
| Compute SKU availability / quota sufficiency | Same `doctor` check | Failed, same documented reason as every candidate since cloud compute was enabled — not a regression from this fix | 2026-08-15T05:52:01Z |
| Authenticated doctor (full run) | `aiml-scaffold doctor --environment dev` (cloud-enabled) | `overall_status: failed` — same profile as the prior three candidates: only the expected `active_identity_match` warning and the two known compute checks | 2026-08-15T05:52:01Z |

**Validated by:** Ray Swan / Claude, repeating the documented Azure validation workflow after fixing the CLI stdout-pollution bug.

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
