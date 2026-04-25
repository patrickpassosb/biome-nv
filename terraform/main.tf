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

# VCN and Networking
resource "oci_core_vcn" "biome_vcn" {
  cidr_block     = "10.0.0.0/16"
  compartment_id = var.compartment_ocid
  display_name   = "biome-vcn"
}

resource "oci_core_internet_gateway" "biome_igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.biome_vcn.id
  display_name   = "biome-internet-gateway"
}

resource "oci_core_route_table" "biome_route_table" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.biome_vcn.id
  display_name   = "biome-route-table"

  route_rules {
    network_entity_id = oci_core_internet_gateway.biome_igw.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }
}

resource "oci_core_subnet" "biome_subnet" {
  cidr_block        = "10.0.1.0/24"
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.biome_vcn.id
  display_name      = "biome-subnet"
  route_table_id    = oci_core_route_table.biome_route_table.id
  security_list_ids = [oci_core_security_list.biome_security_list.id]
}

resource "oci_core_security_list" "biome_security_list" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.biome_vcn.id
  display_name   = "biome-security-list"

  ingress_security_rules {
    protocol = "6"  # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 443
      max = 443
    }
  }

  ingress_security_rules {
    protocol = "6"  # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 1522
      max = 1522
    }
  }

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

# Oracle Autonomous Database
resource "oci_database_autonomous_database" "biome_db" {
  compartment_id           = var.compartment_ocid
  db_name                  = "BIOMEDB"
  display_name             = "biome-autonomous-db"
  db_workload              = "OLTP"
  cpu_core_count           = 1
  data_storage_size_in_tbs = 1
  is_auto_scaling_enabled  = false
  admin_password           = var.db_admin_password
  
  # Network access
  whitelisted_ips = ["0.0.0.0/0"]
  
  # Free tier configuration
  is_free_tier = var.use_free_tier
  
  # License model
  license_model = var.use_free_tier ? "BRING_YOUR_OWN_LICENSE" : "LICENSE_INCLUDED"
}

# Object Storage for wallet
resource "oci_objectstorage_bucket" "biome_wallet_bucket" {
  compartment_id = var.compartment_ocid
  name           = "biome-wallet-bucket"
  namespace      = var.object_storage_namespace
  access_type    = "Public"  # Change to "NoPublicAccess" for production
  versioning     = "Disabled"
}

# Output important values
output "autonomous_db_id" {
  value = oci_database_autonomous_database.biome_db.id
}

output "autonomous_db_connection_string" {
  value = oci_database_autonomous_database.biome_db.connection_strings[0].all_connection_strings["high"]
}

output "autonomous_db_wallet_url" {
  value = "https://console.${var.region}.oraclecloud.com/a/db/autonomousDatabases/${oci_database_autonomous_database.biome_db.id}/wallet"
}

output "object_storage_bucket_name" {
  value = oci_objectstorage_bucket.biome_wallet_bucket.name
}
