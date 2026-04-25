terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 6.0"
    }
  }
  required_version = ">= 1.0"
}

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# Oracle Autonomous Database (Always Free eligible)
resource "oci_database_autonomous_database" "biome_db" {
  compartment_id           = var.compartment_ocid
  db_name                  = "BIOMEDB"
  display_name             = "biome-autonomous-db"
  db_workload              = "OLTP"
  compute_model            = "ECPU"
  compute_count            = 1
  data_storage_size_in_tbs = 1
  is_auto_scaling_enabled  = false
  admin_password           = var.db_admin_password

  whitelisted_ips = ["0.0.0.0/0"]

  is_free_tier  = var.use_free_tier
  license_model = var.use_free_tier ? "LICENSE_INCLUDED" : "BRING_YOUR_OWN_LICENSE"
}

# Output important values
output "autonomous_db_id" {
  value = oci_database_autonomous_database.biome_db.id
}

output "autonomous_db_connection_string" {
  value = oci_database_autonomous_database.biome_db.connection_strings[0].high
}

output "autonomous_db_wallet_url" {
  value = "https://console.${var.region}.oraclecloud.com/a/db/autonomousDatabases/${oci_database_autonomous_database.biome_db.id}/wallet"
}
