# Azure AI ML Ops R1 Dev infrastructure deployment plan

> **Status:** Planning

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
| VM-family vCPUs (`Standard_D2s_v3`) | 0 more | Live job run confirmed `RunningNodeCount:1` on `cpu-training` (run 31887608529); quota restriction resolved | Not measured | See result | Conclusive: quota question answered by this candidate |
| Azure ML workspace | 0 more (already live) | 3 | 3 | No count quota exposed by `az quota` | ARM inventory; pass |
| Storage account | 0 more (already live) | 5 | 5 | 250 per region/subscription default | ARM inventory; pass |
| Key Vault | 0 more (already live) | 3 | 3 | No count quota exposed | ARM inventory; pass |
| Log Analytics workspace | 0 more (already live) | 3 | 3 | No applicable count quota surfaced | ARM inventory; pass |
| Application Insights component | 0 more (already live) | 3 | 3 | No component-count quota surfaced | ARM inventory; pass |
| User-assigned identity | 0 more (already live) | 3 | 3 | Provider limit or documented boundary | ARM inventory; pass |
| Azure role assignments | 0 more (already live) | 57 | 57 | 4,000 per subscription | ARM inventory; pass |

## 7. Validation checklist

- [ ] Confirm the manifest tenant, subscription, region, environment, backend, and intended deployment identity.
- [ ] Verify generation receipt and immutable platform/package provenance.
- [ ] Run generated tests and Ruff.
- [ ] Run the local lifecycle and retain local-only evidence without claiming Azure execution.
- [ ] Parse generated YAML and run Actionlint.
- [ ] Run `terraform fmt -check -recursive`.
- [ ] Run `terraform init -backend=false -lockfile=readonly` and `terraform validate`.
- [ ] Review identity and RBAC references statically.
- [ ] Run authenticated read-only quota, policy, backend, OIDC, RBAC, and state checks.
- [ ] Populate validation proof and set `Validated` only through the documented Azure validation workflow.

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
| Generated tests and lint (pinned environment) | CI on this PR | Recorded after merge | Pending |
| Static RBAC review | No RBAC changes in this fix; unaffected | Passed | 2026-08-15T16:42:00Z |
| Azure context and policy | `az account show`; `az policy assignment list` | Passed | 2026-08-15T16:42:00Z |
| Capacity and inventory | `az resource list` by type; `az role assignment list` | Passed; counts unchanged (no new infra) | 2026-08-15T16:42:00Z |
| Compute SKU availability / quota sufficiency (static `doctor` check) | Same `doctor` check | Still fails statically — same documented, non-conclusive condition | 2026-08-15T16:43:00Z |
| Authenticated doctor (full run) | `aiml-scaffold doctor --environment dev` (cloud-enabled) | Recorded after this candidate's authenticated run | Pending |

**Validated by:** Ray Swan / Claude, repeating the documented Azure validation workflow after fixing the stale environment-version reference.

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
