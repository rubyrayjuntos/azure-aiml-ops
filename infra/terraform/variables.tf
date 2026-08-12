variable "subscription_id" {
  type        = string
  description = "Azure subscription ID supplied through TF_VAR_subscription_id."
}

variable "resource_group_name" {
  type        = string
  description = "Pre-created environment resource group."
  default     = "rg-azure-ai-ml-ops-dev"
}

variable "location" {
  type    = string
  default = "eastus"
}

variable "project_name" {
  type    = string
  default = "azure-ai-ml-ops"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "workflow_principal_object_id" {
  type        = string
  description = "Object ID of the GitHub OIDC deployment identity."
}

variable "evidence_retention_days" {
  type    = number
  default = 90
  validation {
    condition     = var.evidence_retention_days >= 1 && var.evidence_retention_days <= 3650
    error_message = "Evidence retention must be between 1 and 3650 days."
  }
}
