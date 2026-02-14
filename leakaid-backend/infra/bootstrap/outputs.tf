# =============================================================================
# Bootstrap 出力（メイン infra の backend 設定で同じ名前を使う）
# =============================================================================

output "bucket_name" {
  description = "作成した State 用バケット名。infra/provider.tf の backend gcs bucket にこの値を合わせること。"
  value       = google_storage_bucket.tfstate.name
}
