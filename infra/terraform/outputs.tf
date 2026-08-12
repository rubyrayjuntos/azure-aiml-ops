output "resource_group_name" { value = data.azurerm_resource_group.environment.name }
output "workspace_name" { value = azurerm_machine_learning_workspace.this.name }
output "storage_account_name" { value = azurerm_storage_account.this.name }
output "evidence_container_id" { value = azurerm_storage_container.evidence.id }


output "workspace_identity_principal_id" { value = azurerm_machine_learning_workspace.this.identity[0].principal_id }

output "workspace_storage_role_assignment_id" { value = azurerm_role_assignment.workspace_storage.id }

output "workflow_storage_role_assignment_id" { value = azurerm_role_assignment.workflow_storage.id }
output "storage_account_id" { value = azurerm_storage_account.this.id }
output "resource_group_id" { value = data.azurerm_resource_group.environment.id }
