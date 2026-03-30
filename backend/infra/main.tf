# =============================================================================
# LeakAid インフラ定義 (GCP)
# =============================================================================
# Temporal と FastAPI 用の基盤。低コスト・フラット構成。
# =============================================================================

# -----------------------------------------------------------------------------
# API 有効化（必要に応じてコメント解除）
# -----------------------------------------------------------------------------
# resource "google_project_service" "artifactregistry" {
#   service            = "artifactregistry.googleapis.com"
#   disable_on_destroy = false
# }
# resource "google_project_service" "run" {
#   service            = "run.googleapis.com"
#   disable_on_destroy = false
# }

# =============================================================================
# 1. Network (VPC)
# =============================================================================

resource "google_compute_network" "vpc" {
  name                    = "leakaid-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "subnet" {
  name          = "leakaid-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
}


# =============================================================================
# 2. Artifact Registry（Docker イメージ格納）
# =============================================================================

resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "leakaid-repo"
  description   = "LeakAid Docker イメージ用"
  format        = "DOCKER"
}

# =============================================================================
# 3. Cloud Storage（ログ保存用）
# =============================================================================

resource "google_storage_bucket" "logs" {
  name          = "${var.project_id}-logs"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# ログバケット用のサービスアカウントとキー
resource "google_service_account" "logs_writer" {
  account_id   = "leakaid-logs-writer"
  display_name = "LeakAid Logs Writer"
}

resource "google_storage_bucket_iam_member" "logs_writer" {
  bucket = google_storage_bucket.logs.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.logs_writer.email}"
}

resource "google_service_account_key" "logs_writer" {
  service_account_id = google_service_account.logs_writer.name
}

# =============================================================================
# 4. Cloud Run（FastAPI 用プレースホルダー）
# =============================================================================

resource "google_cloud_run_v2_service" "api" {
  name     = "leakaid-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "api_public" {
  location = google_cloud_run_v2_service.api.location
  name    = google_cloud_run_v2_service.api.name
  role    = "roles/run.invoker"
  member  = "allUsers"
}
