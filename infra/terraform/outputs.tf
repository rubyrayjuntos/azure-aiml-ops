output "resource_group_name" { value = data.azurerm_resource_group.environment.name }
output "workspace_name" { value = azurerm_machine_learning_workspace.this.name }
output "storage_account_name" { value = azurerm_storage_account.this.name }
output "evidence_container_id" { value = azurerm_storage_container.evidence.id }

output "training_compute_name" { value = azurerm_machine_learning_compute_cluster.training.name }


output "batch_compute_name" { value = azurerm_machine_learning_compute_cluster.batch.name }

output "workspace_identity_principal_id" { value = azurerm_machine_learning_workspace.this.identity[0].principal_id }

output "compute_identity_id" { value = azurerm_user_assigned_identity.compute.id }
output "compute_identity_principal_id" { value = azurerm_user_assigned_identity.compute.principal_id }


output "compute_storage_role_assignment_id" { value = azurerm_role_assignment.compute_storage.id }

output "workflow_storage_role_assignment_id" { value = azurerm_role_assignment.workflow_storage.id }
output "storage_account_id" { value = azurerm_storage_account.this.id }
output "resource_group_id" { value = data.azurerm_resource_group.environment.id }
