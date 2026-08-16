data "azurerm_resource_group" "environment" {
  name = var.resource_group_name
}

locals {
  compact_name = substr(replace(var.project_name, "-", ""), 0, 12)
  suffix       = substr(md5("${var.subscription_id}-${var.project_name}-${var.environment}"), 0, 8)
  tags = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "aiml-scaffold-terraform"
  }
}

resource "azurerm_log_analytics_workspace" "this" {
  name                = "log-${var.project_name}-${var.environment}"
  location            = var.location
  resource_group_name = data.azurerm_resource_group.environment.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.tags
}

resource "azurerm_application_insights" "this" {
  name                = "appi-${var.project_name}-${var.environment}"
  location            = var.location
  resource_group_name = data.azurerm_resource_group.environment.name
  workspace_id        = azurerm_log_analytics_workspace.this.id
  application_type    = "web"
  tags                = local.tags
}

resource "azurerm_storage_account" "this" {
  name                            = "st${local.compact_name}${local.suffix}"
  resource_group_name             = data.azurerm_resource_group.environment.name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  public_network_access_enabled   = var.environment != "prod"
  shared_access_key_enabled       = false
  allow_nested_items_to_be_public = false
  blob_properties {
    versioning_enabled = true
    delete_retention_policy { days = 7 }
    container_delete_retention_policy { days = 7 }
  }
  tags = local.tags
}

resource "azurerm_storage_container" "evidence" {
  name                  = "platform-evidence"
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}


resource "azurerm_storage_container" "monitoring" {
  name                  = "monitoring"
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}


resource "azurerm_storage_management_policy" "evidence" {
  storage_account_id = azurerm_storage_account.this.id
  rule {
    name    = "evidence-retention"
    enabled = true
    filters {
      prefix_match = ["platform-evidence/v1/"]
      blob_types   = ["blockBlob"]
    }
    actions {
      base_blob { delete_after_days_since_modification_greater_than = var.evidence_retention_days }
      version { delete_after_days_since_creation = var.evidence_retention_days }
    }
  }
}

resource "azurerm_key_vault" "this" {
  name                          = "kv-${local.compact_name}-${local.suffix}"
  location                      = var.location
  resource_group_name           = data.azurerm_resource_group.environment.name
  tenant_id                     = data.azurerm_client_config.current.tenant_id
  sku_name                      = "standard"
  rbac_authorization_enabled    = true
  soft_delete_retention_days    = 7
  purge_protection_enabled      = var.environment == "prod"
  public_network_access_enabled = var.environment != "prod"
  tags                          = local.tags
}

data "azurerm_client_config" "current" {}

resource "azurerm_machine_learning_workspace" "this" {
  name                          = "mlw-${var.project_name}-${var.environment}"
  location                      = var.location
  resource_group_name           = data.azurerm_resource_group.environment.name
  application_insights_id       = azurerm_application_insights.this.id
  key_vault_id                  = azurerm_key_vault.this.id
  storage_account_id            = azurerm_storage_account.this.id
  storage_account_access_type   = "Identity"
  public_network_access_enabled = var.environment != "prod"
  identity { type = "SystemAssigned" }
  tags = local.tags

  # Azure ML auto-provisions and attaches a Container Registry the first
  # time a job builds a custom environment image. container_registry_id
  # is a ForceNew attribute in the AzureRM provider, so without this the
  # next plan after any successful custom-environment job would want to
  # destroy and recreate the entire workspace just to reconcile a field
  # Terraform never set and does not own. Confirmed live: run 31887608529's
  # prepare step triggered this auto-attachment.
  lifecycle {
    ignore_changes = [container_registry_id]
  }
}


# Enabled Azure ML cluster compute requires a user-assigned compute identity for model and MLflow
# input/output operations when Shared Key access is disabled. The identity is
# project-owned; its principal ID is expected to be known only after apply.
resource "azurerm_user_assigned_identity" "compute" {
  name                = "id-${var.project_name}-${var.environment}-compute"
  location            = var.location
  resource_group_name = data.azurerm_resource_group.environment.name
  tags                = local.tags
}

resource "azurerm_role_assignment" "compute_storage" {
  scope                            = azurerm_storage_account.this.id
  role_definition_name             = "Storage Blob Data Contributor"
  principal_id                     = azurerm_user_assigned_identity.compute.principal_id
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
}


# The Microsoft.MachineLearningServices resource provider automatically grants
# the workspace's system-assigned identity Storage Blob Data Contributor (and
# Storage File Data Privileged Contributor) on its default storage account
# whenever storage_account_access_type is "Identity". A separate Terraform-
# managed role assignment for the same principal/role/scope conflicts with
# that auto-provisioned one (409 RoleAssignmentExists), confirmed live against
# a real Dev apply. Do not add an explicit workspace-storage role assignment.

resource "azurerm_role_assignment" "workflow_storage" {
  scope                = azurerm_storage_account.this.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.workflow_principal_object_id
  principal_type       = "ServicePrincipal"
}


resource "azurerm_machine_learning_compute_cluster" "training" {
  name                          = "cpu-training"
  location                      = var.location
  vm_priority                   = "Dedicated"
  vm_size                       = "Standard_D2s_v3"
  machine_learning_workspace_id = azurerm_machine_learning_workspace.this.id
  scale_settings {
    min_node_count                       = 0
    max_node_count                       = 1
    scale_down_nodes_after_idle_duration = "PT2M"
  }
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.compute.id]
  }
  depends_on = [azurerm_role_assignment.compute_storage]
}



resource "azurerm_machine_learning_compute_cluster" "batch" {
  name                          = "cpu-batch"
  location                      = var.location
  vm_priority                   = "Dedicated"
  vm_size                       = "Standard_D2s_v3"
  machine_learning_workspace_id = azurerm_machine_learning_workspace.this.id
  scale_settings {
    min_node_count                       = 0
    max_node_count                       = 1
    scale_down_nodes_after_idle_duration = "PT2M"
  }
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.compute.id]
  }
  depends_on = [azurerm_role_assignment.compute_storage]
}

