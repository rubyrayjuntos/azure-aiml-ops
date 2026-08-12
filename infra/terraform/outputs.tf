output "resource_group_name" { value = data.azurerm_resource_group.environment.name }
output "workspace_name" { value = azurerm_machine_learning_workspace.this.name }
output "storage_account_name" { value = azurerm_storage_account.this.name }
output "evidence_container_id" { value = azurerm_storage_container.evidence.id }
output "training_compute_name" { value = azurerm_machine_learning_compute_cluster.training.name }
output "batch_compute_name" { value = azurerm_machine_learning_compute_cluster.batch.name }
