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
| Azure ML workspace | 0 more (all 8 resources already created by prior apply attempts) | 4 | 4 | No count quota exposed by `az quota` | ARM inventory; pass |
| Storage account | 0 more | 7 | 7 | 250 per region/subscription default | ARM inventory; pass |
| Key Vault | 0 more | 4 | 4 | No count quota exposed | ARM inventory; pass |
| Log Analytics workspace | 0 more | 2 | 2 | No applicable count quota surfaced | ARM inventory; pass |
| Application Insights component | 0 more | 4 | 4 | No component-count quota surfaced | ARM inventory; pass |
| User-assigned identity | 0 | 2 | 2 | Provider limit or documented boundary | Not requested by local-first profile |
| Azure role assignments | 0 more | 63 | 63 | 4,000 per subscription | ARM inventory; pass |

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

Fourth candidate in this deployment sequence, correcting a third finding. Plan run [31661241595](https://github.com/rubyrayjuntos/azure-aiml-ops/actions/runs/31661241595) (after the workspace-RBAC and evidence-retry fix) showed 7 clean no-ops but one unexpected replace on `azurerm_role_assignment.workflow_storage` (`replace_because_cannot_update`): the `role_definition_id` recorded at creation used the subscription-scoped ARM path while `data.azurerm_role_definition` resolved the same built-in role to the global path on this plan. This candidate switches both role assignments to `role_definition_name`, removing the data source and the path-format ambiguity entirely. No infrastructure was created or modified by this validation pass; all eight resources from the prior apply attempts remain and are expected to appear as no-op in the next plan, this time including `workflow_storage`.

| Check | Command | Result | Timestamp |
|---|---|---|---|
| Reproducible platform wheel | Two independent clean-room `git archive` + `python -m build --wheel` builds, `SOURCE_DATE_EPOCH` pinned to the commit timestamp | Passed; byte-identical, `sha256:c8a73fac24186f987c7b9341a0068645c85ba1dd828ea26100eb3af26a14704b` | 2026-08-13T02:44:00Z |
| Deterministic generation | Two independent `aiml-scaffold generate` runs from the reproducible wheel | Passed; byte-identical, `generated_files_digest sha256:959303afc27021645c779960ec05b87e3169ebe2880ef56ba9b8285f18014aa3` | 2026-08-13T02:45:00Z |
| Offline doctor | `aiml-scaffold doctor --environment dev --no-cloud` | Passed | 2026-08-13T02:46:00Z |
| Python lint | `ruff check .` | Passed, no findings | 2026-08-13T02:46:00Z |
| YAML parse | Parsed every generated `.yml`/`.yaml` | Passed, 0 failures | 2026-08-13T02:46:00Z |
| Actionlint | `actionlint .github/workflows/*.yml` | Passed, no findings | 2026-08-13T02:46:00Z |
| Terraform static validation | `terraform fmt -check -recursive`; `terraform init -backend=false -lockfile=readonly`; `terraform validate` | Passed with AzureRM 4.81.0; confirmed no `role_definition_id`/`azurerm_role_definition` remains in the rendered `main.tf`, and `terraform fmt` produces byte-identical output to the template | 2026-08-13T02:46:00Z |
| Scenario and secret scan | Grep for `churn`/`taxi` scenario leakage and credential patterns | Passed; no leakage | 2026-08-13T02:47:00Z |
| Generated tests and lint (pinned environment) | CI run [`31662153371`](https://github.com/rubyrayjuntos/azure-aiml-ops/actions/runs/31662153371) on merge commit `fb103f23d88b3c828cc48ab4093f85d9b3d085c9`: `pip install -c constraints.txt -e '.[dev]'`, `ruff check .`, `pytest`, `terraform fmt/init/validate` under Python 3.11 | Passed | 2026-08-13T02:52:29Z |
| Static RBAC review | Manual review of `infra/terraform/main.tf` | Passed; `workflow_storage` grants `Storage Blob Data Contributor` by name, scoped to the project storage account only | 2026-08-13T02:48:00Z |
| Azure context and policy | `az account show`; `az policy assignment list` | Passed; active tenant/subscription match the manifest; one enforced `SecurityCenterBuiltIn` policy assignment | 2026-08-13T02:49:00Z |
| Capacity and inventory | `az resource list` by type; `az role assignment list` | Passed; all eight resources from the prior apply attempts remain live and unchanged (workspace 4, storage 7, Key Vault 4, Log Analytics 2, App Insights 4, role assignments 63 subscription-wide) | 2026-08-13T02:54:00Z |
| Authenticated doctor | `aiml-scaffold doctor --environment dev` (cloud-enabled) against the merged candidate, with the intended GitHub deployment identity | `overall_status: warning`; only the expected `active_identity_match` warning; all other checks passed live | 2026-08-13T02:54:35Z |

**Validated by:** Ray Swan / Claude, repeating the documented Azure validation workflow after switching to `role_definition_name` (platform source `051432a904fc455925af641fc1e155b1dd8cfb66`).

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
| 1.4.0 | 2026-08-12 | 2026-08-13 | Ray Swan / Claude | Regenerated switching to `role_definition_name` after plan run 31661241595 showed a spurious `workflow_storage` replace caused by ARM path-format ambiguity in the `role_definition_id` data-source lookup. Completed the Azure validation workflow and set status to `Validated`. |
| 1.3.0 | 2026-08-12 | 2026-08-13 | Ray Swan / Claude | Regenerated after removing the redundant `workspace_storage` role assignment (409 conflict with AML's auto-granted RBAC) and adding evidence-write retry for RBAC propagation delay. Completed the Azure validation workflow and set status to `Validated`. |
| 1.0.0 | 2026-08-12 | 2026-08-12 | Ray Swan / AIML-SCAFFOLD | Generated the initial R1 Terraform deployment-governance plan; live validation remains pending. |
