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
| ML lifecycle | Portable local-first ML | Shared Python lifecycle plus local runner | `data-science/`, `scripts/run_local_lifecycle.py` |
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
| Azure training compute | Disabled; no SKU selected |
| Azure batch compute | Disabled; no SKU selected |
| Compute identity | Not created by the default local-first profile |
| Workflow identity | Administrator-owned Entra OIDC prerequisite |
| Storage data roles | Workload Terraform; exact project-storage scope for workspace and workflow identities |

One resource has one IaC owner. Workload Terraform must not change bootstrap state, the resource group, GitHub/Entra prerequisites, or the backend.

Local lifecycle evidence does not prove Azure ML job submission, managed identity, lineage, registration, endpoint deployment, or batch execution. Every enabled Azure compute workflow requires a deliberate cost-aware authorization phrase. The factory never selects a replacement VM SKU.

## 6. Provisioning-limit checklist

Complete live, read-only quota and inventory checks before approving this plan. No Terraform mutation is permitted during validation.

| Resource or quota | Planned | Current | Total after deployment | Limit | Result |
|---|---:|---:|---:|---:|---|
| Azure ML clusters | 0 | 0 | 0 | 200 | Not requested; local-first profile |
| Azure ML serverless training | Disabled | Not applicable | Not applicable | Exact SKU quota when enabled | Not requested |
| VM-family vCPUs | 0; cloud compute disabled | Not applicable | Not applicable | Not applicable | Not requested |
| Azure ML workspace | 1 | 3 | 4 | No count quota exposed by `az quota` | ARM inventory; pass |
| Storage account | 1 (already created by the prior partial apply) | 7 | 7 | 250 per region/subscription default | ARM inventory; pass |
| Key Vault | 1 (already created by the prior partial apply) | 4 | 4 | No count quota exposed | ARM inventory; pass |
| Log Analytics workspace | 1 (already created by the prior partial apply) | 2 | 2 | No applicable count quota surfaced | ARM inventory; pass |
| Application Insights component | 1 (already created by the prior partial apply) | 4 | 4 | No component-count quota surfaced | ARM inventory; pass |
| User-assigned identity | 0 | 2 | 2 | Provider limit or documented boundary | Not requested by local-first profile |
| Azure role assignments | 2 | 58 | 60 | 4,000 per subscription | ARM inventory; pass |

## 7. Validation checklist

- [x] Confirm the manifest tenant, subscription, region, environment, backend, and intended deployment identity.
- [x] Verify generation receipt and immutable platform/package provenance.
- [x] Run generated tests and Ruff.
- [x] Run the local lifecycle and retain local-only evidence without claiming Azure execution.
- [x] Parse generated YAML and run Actionlint.
- [x] Run `terraform fmt -check -recursive`.
- [x] Run `terraform init -backend=false -lockfile=readonly` and `terraform validate`.
- [x] Review identity and RBAC references statically.
- [x] Run authenticated read-only quota, policy, backend, OIDC, RBAC, and state checks.
- [x] Populate validation proof and set `Validated` only through the documented Azure validation workflow.

## 8. Validation proof

This candidate exists specifically to correct a live apply failure. Apply run [31657449816](https://github.com/rubyrayjuntos/azure-aiml-ops/actions/runs/31657449816) on the previous candidate created `azurerm_log_analytics_workspace.this`, `azurerm_application_insights.this`, and `azurerm_key_vault.this`, then failed creating `azurerm_storage_account.this`'s data-plane readiness check with `403 KeyBasedAuthenticationNotPermitted` — the AzureRM provider defaulted to key-based auth for that poll against an account with Shared Key correctly disabled. This candidate adds `storage_use_azuread = true` to the provider block. No infrastructure was created or modified by this validation pass; the four resources above remain from the prior partial apply and are expected to appear as no-op in the next plan.

| Check | Command | Result | Timestamp |
|---|---|---|---|
| Reproducible platform wheel | Two independent clean-room `git archive` + `python -m build --wheel` builds, `SOURCE_DATE_EPOCH` pinned to the commit timestamp | Passed; byte-identical, `sha256:a1374bb2711b54512eb8d19505367676eaa24d871d8870ad7b3ae7323de534de` | 2026-08-13T01:35:00Z |
| Deterministic generation | Two independent `aiml-scaffold generate` runs from the reproducible wheel | Passed; byte-identical, `generated_files_digest sha256:5b4d7a20daa6a293d782e2b21b61e775c5f79f3109fb104921295846cb2e29d7` | 2026-08-13T01:37:00Z |
| Offline doctor | `aiml-scaffold doctor --environment dev --no-cloud` | Passed | 2026-08-13T01:38:00Z |
| Python lint | `ruff check .` | Passed, no findings | 2026-08-13T01:38:00Z |
| YAML parse | Parsed every generated `.yml`/`.yaml` | Passed, 0 failures | 2026-08-13T01:38:00Z |
| Actionlint | `actionlint .github/workflows/*.yml` | Passed, no findings | 2026-08-13T01:38:00Z |
| Terraform static validation | `terraform fmt -check -recursive`; `terraform init -backend=false -lockfile=readonly`; `terraform validate` | Passed with AzureRM 4.81.0; `storage_use_azuread = true` present in the rendered provider block | 2026-08-13T01:38:00Z |
| Scenario and secret scan | Grep for `churn`/`taxi` scenario leakage and credential patterns | Passed; no leakage | 2026-08-13T01:38:00Z |
| Generated tests and lint (pinned environment) | CI run [`31659621585`](https://github.com/rubyrayjuntos/azure-aiml-ops/actions/runs/31659621585) on merge commit `cbc5362b20b317424424209ba3131475957deea9`: `pip install -c constraints.txt -e '.[dev]'`, `ruff check .`, `pytest`, `terraform fmt/init/validate` under Python 3.11 | Passed | 2026-08-13T02:03:04Z |
| Static RBAC review | Manual review of `infra/terraform/main.tf` role assignments (unchanged by this fix) | Passed; both role assignments still grant `Storage Blob Data Contributor` scoped to the project storage account only | 2026-08-13T01:40:00Z |
| Azure context and policy | `az account show`; `az policy assignment list` | Passed; active tenant/subscription match the manifest; one enforced `SecurityCenterBuiltIn` policy assignment | 2026-08-13T01:41:00Z |
| Capacity and inventory | `az resource list` by type | Passed; current counts now include the four resources created by the prior partial apply (workspace 3, storage 7, Key Vault 4, Log Analytics 2, App Insights 4); the next plan is expected to show those four as no-op, not create | 2026-08-13T01:42:00Z |
| Authenticated doctor | `aiml-scaffold doctor --environment dev` (cloud-enabled) against the merged candidate, with the intended GitHub deployment identity | `overall_status: warning`; only the expected `active_identity_match` warning (operator identity vs. GitHub deployment identity); all other checks passed live | 2026-08-13T02:05:00Z |

**Validated by:** Ray Swan / Claude, repeating the documented Azure validation workflow after the `storage_use_azuread` fix (platform source `b36beac93db570310a7ea7e920eb65e70371ceb3`).

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
| 1.2.0 | 2026-08-12 | 2026-08-13 | Ray Swan / Claude | Regenerated with `storage_use_azuread = true` after apply run 31657449816 failed on the storage account's data-plane readiness poll. Completed the Azure validation workflow and set status to `Validated`. |
| 1.1.0 | 2026-08-12 | 2026-08-12 | Ray Swan / AIML-SCAFFOLD | Generated the local-first compute policy with independent explicit Azure training and batch fallbacks, one-node Dev ceiling, and charged-compute authorization boundary. |
| 1.0.0 | 2026-08-12 | 2026-08-12 | Ray Swan / AIML-SCAFFOLD | Generated the initial R1 Terraform deployment-governance plan; live validation remains pending. |
