# TEMPLATE ONLY - NOT plan/apply validated against a live tenancy.
# Built-in resources: OCI Logging log group + custom log with explicit retention.

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0"
    }
  }
}

variable "compartment_id" {
  type        = string
  description = "OCID of the compartment"
}

resource "oci_logging_log_group" "this" {
  compartment_id = var.compartment_id
  display_name   = "prod-app"
  freeform_tags  = { tier = "prod" }
}

# Retention is a built-in service setting: 30-day increments, 30-180 days.
# The console default for a new log is 30 days, so set it explicitly.
resource "oci_logging_log" "audit_trail" {
  display_name       = "audit-trail"
  log_group_id       = oci_logging_log_group.this.id
  log_type           = "CUSTOM"
  retention_duration = 180

  configuration {
    source {
      source_type = "OCISERVICE"
      service     = "objectstorage"
      resource    = "*"
      category    = "all"
    }
  }
}
