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
| Azure ML clusters | 2 | Not measured | Not measured | 200 | Not exercised |
| Azure ML serverless training | Disabled | Not measured | Not measured | Exact SKU quota when enabled | Not exercised |
| VM-family vCPUs | Exact explicit-SKU discovery required | Not measured | Not measured | Not measured | Not exercised |
| Azure ML workspace | 1 | Not measured | Not measured | Provider limit or documented boundary | Not exercised |
| Storage account | 1 | Not measured | Not measured | Provider limit or documented boundary | Not exercised |
| Key Vault | 1 | Not measured | Not measured | Provider limit or documented boundary | Not exercised |
| Log Analytics workspace | 1 | Not measured | Not measured | Provider limit or documented boundary | Not exercised |
| Application Insights component | 1 | Not measured | Not measured | Provider limit or documented boundary | Not exercised |
| User-assigned identity | 1 | Not measured | Not measured | Provider limit or documented boundary | Not exercised |
| Azure role assignments | 3 | Not measured | Not measured | 4,000 per subscription | Not exercised |

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

Not yet executed. Record the exact commands, sanitized results, and timestamps here before setting status to `Validated`.

| Check | Command | Result | Timestamp |
|---|---|---|---|
| Azure validation workflow | Not exercised | Not exercised | Not exercised |

**Validated by:** Not yet validated.

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
