
provider "google" {
  project = var.project_id
}

#temporary storage

resource "google_storage_bucket" "storage" {
  name = "${var.prefix}storage"
  location = "EU"
  force_destroy = true
}

# resource "google_service_account" "spannerhammer_service_account" {
#   account_id = "spannerhammer-service-account"
#   display_name = "Spanner Hammer Service Account"

# }

resource "google_storage_bucket_object" "startup-script" {
  name = "startup-script.sh"
  bucket = "${google_storage_bucket.storage.name}"
  source = "scripts/startup-script.sh"
}

resource "google_storage_bucket_object" "application" {
  bucket = "${google_storage_bucket.storage.name}"
  name = "connect.py"
  source = "scripts/connect.py"
}

#creating spanner instances

resource "google_spanner_instance" "spannerhammer_instance" {
  for_each = var.spanner_regions
    config = each.value
    display_name = "${var.prefix}${each.key}"
    name = "${var.prefix}${each.key}"
}

resource "google_compute_instance"  "probe_instance" {
  for_each = var.probe_regions
    zone = each.value
    name = "${var.prefix}${each.key}-probe"
    boot_disk {
      initialize_params {
        image = "debian-cloud/debian-9"
      }
    }
    network_interface {
      network = "default"

      access_config {
        // Ephemeral IP
      }
    }
    allow_stopping_for_update=true
    service_account {
      scopes = ["cloud-platform"]
    }
    machine_type = "n1-standard-1"
    metadata_startup_script = <<EOT
    #!/bin/bash
    export CONFIG_INSTANCE=${google_spanner_instance.config_instance.name}
    export HOSTNAME
    gsutil cp gs://${google_storage_bucket.storage.name}/startup-script.sh /tmp/
    gsutil cp gs://${google_storage_bucket.storage.name}/connect.py /tmp/
    sudo chmod 755 /tmp/startup-script.sh
    sudo apt-get update
    sudo apt-get install python-pip -y
    pip install google-cloud
    pip install google-cloud-spanner
    /tmp/startup-script.sh
    EOT
}

resource "google_spanner_instance" "config_instance" {
  config = "regional-europe-west1"
  display_name = "${var.prefix}config"
  name = "${var.prefix}config"
}

#creating spanner databases

resource "google_spanner_database" "customer_database" {
  for_each = var.spanner_regions
  instance = "${google_spanner_instance.spannerhammer_instance[each.key].name}"
  name = "testdb"
  ddl = [<<EOT
  CREATE TABLE customers (
    customer_id INT64 NOT NULL,
    created_date DATE,
    customer_name STRING(MAX) NOT NULL,
    ) PRIMARY KEY (customer_id)
  EOT
  ]
}


resource "google_spanner_database" "config_database" {
    instance = "${google_spanner_instance.config_instance.name}"
    name = "config-database"
    ddl = [<<EOT
    CREATE TABLE instances (
    id INT64,
    instance_id STRING(MAX),
    instance_database_id STRING(MAX),
    sample_size INT64,
    staleness INT64,
    is_active BOOL
) PRIMARY KEY (id) 
EOT
,
<<EOT
CREATE TABLE latencyMetrics (
    reading_id STRING(MAX),
    insertedTimestamp TIMESTAMP OPTIONS (allow_commit_timestamp=true),
    instanceName STRING(MAX),
    latency FLOAT64,
    vm_id STRING(MAX),
    zone STRING(MAX),
) PRIMARY KEY (reading_id)
EOT
]
}

