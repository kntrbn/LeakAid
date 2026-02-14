# =============================================================================
# Bootstrap 用変数
# =============================================================================

variable "project_id" {
  description = "GCP プロジェクト ID"
  type        = string
}

variable "bucket_name" {
  description = "Terraform State 用 GCS バケット名（グローバルで一意）"
  type        = string
  default     = "leakaid-tfstate"
}

variable "bucket_location" {
  description = "バケットのロケーション（マルチリージョンまたはリージョン）"
  type        = string
  default     = "asia-northeast1"
}

variable "region" {
  description = "Provider 用リージョン（バケットの location とは別）"
  type        = string
  default     = "asia-northeast1"
}
