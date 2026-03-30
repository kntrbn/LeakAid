# =============================================================================
# Terraform 設定・プロバイダー
# =============================================================================
# State は GCS で管理。バケットは infra/bootstrap/ で Terraform 管理。
# 初回: cd infra/bootstrap && terraform init && terraform apply
# 以降: cd infra && terraform init && terraform plan/apply
# =============================================================================

terraform {
  required_version = ">= 1.0"

  backend "gcs" {
    # 変数は backend ブロックで使えないため、ここを環境に合わせて書き換えるか、
    # terraform init -backend-config="bucket=YOUR_BUCKET" -backend-config="prefix=leakaid" で指定する。
    bucket = "leakaid-tfstate"
    prefix  = "infra"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
