variable "project_id" {
  description = "Project ID"
  default = "pandoras-box-257207"
}

variable "prefix" {
    default = "spannerhammer-"
}

variable "spanner_regions" {
    description = "Spanner instance locations"
    type = map
    default = {
        belgium = "regional-europe-west1"
        us = "regional-us-central1"
        singapore = "regional-asia-southeast1"
        europe = "eur3"
        global = "nam-eur-asia1"
    }
}

variable "probe_regions" {
    description = "Virtual machine probe locations"
    type = map
    default = {
        us-east1-b = "us-east1-b"
        europe-west1-b = "europe-west1-b"
        asia-east1-b = "asia-east1-b"
        asia-northeast1-b = "asia-northeast1-b"
        asia-southeast1-b = "asia-southeast1-b"
        europe-west4-a = "europe-west4-a"
        us-central1-c = "us-central1-c"
        us-west2-a = "us-west2-a"

    }
}