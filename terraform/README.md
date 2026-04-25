# Terraform Deployment for Biome on OCI

## Prerequisites

1. **OCI CLI installed** and configured with API key
2. **Terraform installed** (v1.0+)
3. **OCI Compartment** created

## Setup

1. Copy `terraform.tfvars.example` to `terraform.tfvars`:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Fill in your OCI credentials in `terraform.tfvars`:
   - Get OCIDs from OCI Console
   - Get API key fingerprint from `~/.oci/config`
   - Get Object Storage namespace from OCI Console → Object Storage → Namespace Information

## Deploy

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## After Deployment

Terraform will output:
- **autonomous_db_connection_string**: Your DSN for `.env`
- **autonomous_db_wallet_url**: Link to download wallet
- **object_storage_bucket_name**: Bucket name for wallet storage

### Manual Step: Download Wallet

1. Visit the `autonomous_db_wallet_url` from Terraform output
2. Download the wallet (set a password - remember it!)
3. Extract to `backend/wallet/` directory
4. Update `backend/.env` with:
   ```
   ORACLE_DSN=<connection_string_from_output>
   ORACLE_WALLET_PASSWORD=<wallet-password>
   ORACLE_USER=admin
   ORACLE_PASSWORD=<db_admin_password_from_terraform>
   ```

## Destroy

```bash
terraform destroy
```
