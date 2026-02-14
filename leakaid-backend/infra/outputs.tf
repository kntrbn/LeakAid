# =============================================================================
# 出力値
# =============================================================================
# apply 後に参照できる値。他モジュールやローカル設定に利用する。
# =============================================================================

output "cloud_sql_public_ip" {
  description = "Cloud SQL の Public IP（Private のみの場合は空の可能性あり）"
  value       = google_sql_database_instance.temporal_db.public_ip_address
}

output "cloud_sql_private_ip" {
  description = "Cloud SQL の Private IP（同一 VPC 内からの接続用）"
  value       = google_sql_database_instance.temporal_db.private_ip_address
}

output "temporal_vm_public_ip" {
  description = "Temporal Server (GCE) の Public IP（gRPC 7233, UI 8233）"
  value       = google_compute_instance.temporal_server.network_interface[0].access_config[0].nat_ip
}

output "cloud_run_url" {
  description = "Cloud Run (FastAPI プレースホルダー) の URL"
  value       = google_cloud_run_v2_service.api.uri
}

output "artifact_registry_repository" {
  description = "Artifact Registry リポジトリ名（Docker push 先）"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}"
}
