# =============================================================================
# 変数定義
# =============================================================================
# 実際の値は terraform.tfvars で指定（terraform.tfvars は Git に含めないこと）。
# =============================================================================

variable "project_id" {
  description = "GCP プロジェクト ID"
  type        = string
}

variable "region" {
  description = "デフォルトリージョン（VPC, Cloud Run, Artifact Registry 等）"
  type        = string
  default     = "asia-northeast1"
}

variable "zone" {
  description = "Compute 用のゾーン（同一リージョン内）"
  type        = string
  default     = "asia-northeast1-a"
}
