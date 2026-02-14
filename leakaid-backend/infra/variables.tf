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
  description = "Compute / Cloud SQL 用のゾーン（同一リージョン内）"
  type        = string
  default     = "asia-northeast1-a"
}

# -----------------------------------------------------------------------------
# データベース
# -----------------------------------------------------------------------------
variable "db_password" {
  description = "Cloud SQL (Temporal 用) の temporal ユーザーパスワード"
  type        = string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# ネットワーク（オプション）
# -----------------------------------------------------------------------------
variable "ssh_allowed_cidrs" {
  description = "SSH (22) を許可する CIDR のリスト。開発時は [\"0.0.0.0/0\"] も可だが本番では厳格にすること。"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
