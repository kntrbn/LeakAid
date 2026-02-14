# =============================================================================
# Bootstrap: State 用 GCS バケットの作成
# =============================================================================
# 初回のみ実行。backend は local のため、このディレクトリで terraform init && terraform apply。
# 完了後、ひとつ上の infra/ で terraform init すると GCS backend が使える。
# =============================================================================

terraform {
  required_version = ">= 1.0"
  backend "local" {}

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

# State 保存用バケット（バージョニング有効で誤削除・上書きを防止）
resource "google_storage_bucket" "tfstate" {
  name     = var.bucket_name
  location = var.bucket_location
  # 誤って destroy で中身ごと消さないよう false 推奨
  force_destroy = false

  versioning {
    enabled = true
  }
}
