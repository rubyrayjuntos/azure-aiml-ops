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
| Storage account | 1 | 6 | 7 | 250 per region/subscription default | ARM inventory; pass |
| Key Vault | 1 | 3 | 4 | No count quota exposed | ARM inventory; pass |
| Log Analytics workspace | 1 | 1 | 2 | No applicable count quota surfaced | ARM inventory; pass |
| Application Insights component | 1 | 3 | 4 | No component-count quota surfaced | ARM inventory; pass |
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

| Check | Command | Result | Timestamp |
|---|---|---|---|
| Reproducible platform wheel | Two independent clean-room `git archive` + `python -m build --wheel` builds with `SOURCE_DATE_EPOCH` pinned to the commit timestamp | Passed; byte-identical, `sha256:a107e628d415c1281a194f7dba86dbc200ae126c180a59b67bfa372ea092248f` | 2026-08-12T22:28:22Z |
| Deterministic generation | Two independent `aiml-scaffold generate` runs from the reproducible wheel | Passed; byte-identical, `generated_files_digest sha256:e3f14de3bd67f1384c185e6f3432df4721f835dc3cb9c99f6b11eef475ee9a82` | 2026-08-12T22:30:41Z |
| Manifest validation and maturity review | `aiml-scaffold validate` | Passed; `preview` release status under `allow_preview` manifest policy, `dev_live_pending` boundary | 2026-08-12T22:29:00Z |
| Offline doctor | `aiml-scaffold doctor --environment dev --no-cloud` | Passed; generation receipt and all constituent digests valid | 2026-08-12T22:31:00Z |
| Python lint | `ruff check .` | Passed, no findings | 2026-08-12T22:32:00Z |
| YAML parse | Parsed every generated `.yml`/`.yaml` | Passed, 0 failures | 2026-08-12T22:32:00Z |
| Actionlint | `actionlint .github/workflows/*.yml` | Passed, no findings | 2026-08-12T22:33:00Z |
| Terraform static validation | `terraform fmt -check -recursive`; `terraform init -backend=false -lockfile=readonly`; `terraform validate` | Passed with AzureRM 4.81.0; no plan or state mutation | 2026-08-12T22:34:00Z |
| Scenario and secret scan | Grep for `churn`/`taxi` scenario leakage and common credential patterns across the generated tree | Passed; no leakage; the two credential-pattern matches are the redaction guard in `plan_artifact.py`/`emit_evidence.py` and the documented fake example in `artifact-uri-conformance.json` | 2026-08-12T22:35:00Z |
| Generated tests and lint (pinned environment) | CI run [`31654411635`](https://github.com/rubyrayjuntos/azure-aiml-ops/actions/runs/31654411635) on merge commit `4c422adf6d7cc50cf92c206f7873a7e950389176`: `pip install -c constraints.txt -e '.[dev]'`, `ruff check .`, `pytest`, `terraform fmt/init/validate` under Python 3.11 | Passed | 2026-08-13T00:26:17Z |
| Local lifecycle proof | `python scripts/run_local_lifecycle.py --output .local-runs/proof-1` (prepare/train/evaluate/package/score/evidence) | Passed; prepare receipt `sha256:ccc56e426a6ad19e1304bdb3e5d6a0728f5309ca3015313dba18efb24d5dd666`, train receipt `sha256:28721d0ef0ccb694de899c4381407ef891fe152ebe1f52794e44636b7f0f1258`; run under an unpinned local Python 3.13 environment (outside `constraints.txt`) because the generated package requires Python `>=3.11,<3.13` and no 3.11/3.12 interpreter is available locally — local evidence only, not a substitute for the CI-pinned run above | 2026-08-12T22:36:00Z |
| Static RBAC review | Manual review of `infra/terraform/main.tf` role assignments | Passed; both `workspace_storage` and `workflow_storage` grant `Storage Blob Data Contributor` scoped to the exact project storage account only; no Owner, no subscription-level scope, no unrelated role | 2026-08-13T00:15:00Z |
| Azure context and policy | `az account show`; `az policy assignment list` | Passed; active tenant `90a7175b-82cd-4815-9050-8cbae3a1d234` and subscription `5b452321-32fd-4b1c-8bbf-6d69a5a587ad` match the manifest; one enforced `SecurityCenterBuiltIn` policy assignment, no assignment conflicts with the reviewed contract | 2026-08-13T00:20:00Z |
| Capacity and inventory | `az resource list` by type | Passed; current/planned counts recorded in section 6; no resource-count boundary is approached | 2026-08-13T00:22:00Z |
| Authenticated doctor | `aiml-scaffold doctor --environment dev` (cloud-enabled) against the merged candidate, with `AZURE_CLIENT_ID`/`AZURE_CLIENT_OBJECT_ID` set to the intended GitHub deployment identity | `overall_status: warning`; every check passed except `active_identity_match`, which correctly reports the active Azure CLI identity is the operator's user account, not the intended GitHub Actions deployment identity — a known, expected condition, not a failure. Backend management/data-plane visibility, container existence, shared-key-disabled posture, OIDC federated-credential match, environment-scoped RBAC, and subscription-Owner absence all passed live | 2026-08-13T00:28:00Z |

**Validated by:** Ray Swan / Claude, repeating the documented Azure validation workflow after the local-first compute regeneration (platform source `ef56abc1a8af0b18c8487763ae85267b738144ec`).

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
| 1.2.0 | 2026-08-12 | 2026-08-13 | Ray Swan / Claude | Completed the Azure validation workflow: reproducible wheel/generation, static conformance, CI-pinned tests/Ruff, local lifecycle proof, static RBAC review, and live authenticated doctor. Set status to `Validated`. |
| 1.1.0 | 2026-08-12 | 2026-08-12 | Ray Swan / AIML-SCAFFOLD | Generated the local-first compute policy with independent explicit Azure training and batch fallbacks, one-node Dev ceiling, and charged-compute authorization boundary. |
| 1.0.0 | 2026-08-12 | 2026-08-12 | Ray Swan / AIML-SCAFFOLD | Generated the initial R1 Terraform deployment-governance plan; live validation remains pending. |
