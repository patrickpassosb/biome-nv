variable "tenancy_ocid" {
  description = "OCI Tenancy OCID"
  type        = string
}

variable "user_ocid" {
  description = "OCI User OCID"
  type        = string
}

variable "fingerprint" {
  description = "OCI API Key Fingerprint"
  type        = string
}

variable "private_key_path" {
  description = "Path to OCI API Private Key"
  type        = string
}

variable "region" {
  description = "OCI Region"
  type        = string
  default     = "us-ashburn-1"
}

variable "compartment_ocid" {
  description = "OCI Compartment OCID"
  type        = string
}

variable "db_admin_password" {
  description = "Admin password for Autonomous Database"
  type        = string
  sensitive   = true
}

variable "use_free_tier" {
  description = "Use Always Free resources"
  type        = bool
  default     = true
}

variable "object_storage_namespace" {
  description = "OCI Object Storage Namespace"
  type        = string
}
