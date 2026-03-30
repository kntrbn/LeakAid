# =============================================================================
# 出力値
# =============================================================================
# apply 後に参照できる値。他モジュールやローカル設定に利用する。
# =============================================================================

output "logs_bucket_name" {
  description = "ログ保存用バケット名"
  value       = google_storage_bucket.logs.name
}

output "logs_bucket_url" {
  description = "ログ保存用バケット URL"
  value       = google_storage_bucket.logs.url
}

output "logs_writer_email" {
  description = "ログ書き込み用サービスアカウント"
  value       = google_service_account.logs_writer.email
}

output "logs_writer_key" {
  description = "ログ書き込み用サービスアカウントキー (base64)"
  value       = google_service_account_key.logs_writer.private_key
  sensitive   = true
}

output "cloud_run_url" {
  description = "Cloud Run (FastAPI プレースホルダー) の URL"
  value       = google_cloud_run_v2_service.api.uri
}

output "artifact_registry_repository" {
  description = "Artifact Registry リポジトリ名（Docker push 先）"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}"
}
