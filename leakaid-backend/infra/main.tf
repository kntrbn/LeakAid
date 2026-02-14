# =============================================================================
# LeakAid インフラ定義 (GCP)
# =============================================================================
# Temporal と FastAPI 用の基盤。低コスト・フラット構成。
# =============================================================================

# -----------------------------------------------------------------------------
# API 有効化（必要に応じてコメント解除）
# -----------------------------------------------------------------------------
# resource "google_project_service" "compute" {
#   service            = "compute.googleapis.com"
#   disable_on_destroy = false
# }
# resource "google_project_service" "sqladmin" {
#   service            = "sqladmin.googleapis.com"
#   disable_on_destroy = false
# }
# resource "google_project_service" "servicenetworking" {
#   service            = "servicenetworking.googleapis.com"
#   disable_on_destroy = false
# }
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

# -----------------------------------------------------------------------------
# Cloud SQL 用プライベート接続（同一 VPC から Private IP で接続するため）
# -----------------------------------------------------------------------------
resource "google_compute_global_address" "private_ip_range" {
  name          = "leakaid-private-ip-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
}

# -----------------------------------------------------------------------------
# ファイアウォール
# -----------------------------------------------------------------------------
# 警告: 開発用に 0.0.0.0/0 で SSH を開ける場合は本番では必ず絞ること。
resource "google_compute_firewall" "allow_ssh" {
  name    = "leakaid-allow-ssh"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = var.ssh_allowed_cidrs
  target_tags   = ["temporal-server"]
}

# Temporal: gRPC 7233, Web UI 8233（必要に応じて 7233 のみでも可）
resource "google_compute_firewall" "allow_temporal" {
  name    = "leakaid-allow-temporal"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["7233", "8233"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["temporal-server"]
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
# 3. Cloud SQL for PostgreSQL（Temporal 用）
# =============================================================================

resource "google_sql_database_instance" "temporal_db" {
  name             = "leakaid-temporal-db"
  database_version = "POSTGRES_15"
  region           = var.region

  deletion_protection = false # 開発用。本番では true を推奨。

  settings {
    tier              = "db-f1-micro"
    availability_type = "ZONAL"
    disk_size         = 10
    disk_type         = "PD_SSD"

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

resource "google_sql_database" "temporal" {
  name     = "temporal"
  instance = google_sql_database_instance.temporal_db.name
}

resource "google_sql_database" "temporal_visibility" {
  name     = "temporal_visibility"
  instance = google_sql_database_instance.temporal_db.name
}

resource "google_sql_user" "temporal" {
  name     = "temporal"
  instance = google_sql_database_instance.temporal_db.name
  password = var.db_password
}

# =============================================================================
# 4. Compute Engine（Temporal Server）— Spot VM
# =============================================================================

locals {
  # VM 起動時に Temporal auto-setup を Docker で実行するスクリプト。
  # Cloud SQL の Private IP に接続する。
  temporal_startup_script = <<-EOT
    #!/bin/bash
    set -e
    docker run -d --name temporal --restart unless-stopped \
      -p 7233:7233 \
      -e DB=postgres12 \
      -e DB_PORT=5432 \
      -e DBNAME=temporal \
      -e VISIBILITY_DBNAME=temporal_visibility \
      -e POSTGRES_SEEDS=${google_sql_database_instance.temporal_db.private_ip_address} \
      -e POSTGRES_USER=${google_sql_user.temporal.name} \
      -e POSTGRES_PWD=${var.db_password} \
      temporalio/auto-setup:latest
  EOT
}

resource "google_compute_instance" "temporal_server" {
  name         = "leakaid-temporal-server"
  machine_type = "e2-standard-2"
  zone         = var.zone

  tags = ["temporal-server"]

  boot_disk {
    initialize_params {
      image = "cos-cloud/cos-stable"
      size  = 20
      type  = "pd-standard"
    }
  }

  network_interface {
    network    = google_compute_network.vpc.name
    subnetwork = google_compute_subnetwork.subnet.name
    access_config {}
  }

  # VM 起動時に Temporal コンテナを起動（COS で Docker はプリインストール済み）
  metadata_startup_script = local.temporal_startup_script

  # コスト削減: Spot (Preemptible) VM。途中で停止する可能性あり。
  scheduling {
    preemptible                 = true
    automatic_restart           = false
    provisioning_model          = "SPOT"
    instance_termination_action  = "STOP"
  }

  allow_stopping_for_update = true
}

# =============================================================================
# 5. Cloud Run（FastAPI 用プレースホルダー）
# =============================================================================

resource "google_cloud_run_v2_service" "api" {
  name     = "leakaid-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      env {
        name  = "TEMPORAL_DB_IP"
        value = google_sql_database_instance.temporal_db.private_ip_address
      }
      env {
        name  = "TEMPORAL_VM_IP"
        value = google_compute_instance.temporal_server.network_interface[0].access_config[0].nat_ip
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "api_public" {
  location = google_cloud_run_v2_service.api.location
  name    = google_cloud_run_v2_service.api.name
  role    = "roles/run.invoker"
  member  = "allUsers"
}
