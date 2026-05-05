# Humanlike Chatbot — Infrastructure as Code

This directory contains the Terraform configuration that provisions the complete
AWS infrastructure for the humanlike-chatbot application. Running `bash setup.sh`
creates everything from scratch: networking, database, cache, storage, CDN, and
application server. All environment variables are wired automatically — there is
nothing to configure in the AWS console after apply completes.

---

## What gets created

| Resource | Type | Purpose |
|---|---|---|
| VPC | 10.0.0.0/16 across 2 AZs | Private network — nothing reaches the DB or cache except the app |
| Public subnets | 10.0.1/24, 10.0.2/24 | Load balancer and application instances |
| Private subnets | 10.0.10/24, 10.0.11/24 | RDS and ElastiCache — no internet route |
| Security groups | 4 (ALB → EB → RDS/Cache) | Least-privilege firewall chain |
| RDS MariaDB 10.11 | db.t3.micro (staging) | Primary database, encrypted, automated backups |
| ElastiCache Serverless Redis | TLS-only | Django session cache |
| S3 frontend bucket | Private + CloudFront OAC | Compiled React app |
| S3 data bucket | Private + CORS | Avatars, uploads, voice audio |
| CloudFront distribution | OAC, SPA routing | CDN for the React app |
| Elastic Beanstalk | Docker on AL2023, ALB | Django API server |
| IAM instance role | Least privilege | App reads/writes S3, calls Bedrock — no hardcoded keys |
| IAM GitHub OIDC role | Scoped to this repo | GitHub Actions deploys without storing AWS keys |
| Terraform state | S3 + DynamoDB | Shared, locked, encrypted — created by bootstrap |

---

## Prerequisites

Install these before running anything:

```bash
# Terraform >= 1.9
brew install terraform          # macOS
# or: https://developer.hashicorp.com/terraform/install

# AWS CLI v2
brew install awscli             # macOS
# or: https://aws.amazon.com/cli/

# Verify
terraform version               # should show >= 1.9.x
aws --version                   # should show aws-cli/2.x
```

Your AWS credentials must have permission to create IAM roles, VPCs, RDS
instances, ElastiCache clusters, S3 buckets, CloudFront distributions, and
Elastic Beanstalk environments. The simplest approach for a fresh account is
to use an IAM user or role with `AdministratorAccess` during initial setup,
then tighten permissions afterward.

---

## First-time deployment

### Step 1 — Configure AWS credentials

```bash
aws configure
# AWS Access Key ID: <your key>
# AWS Secret Access Key: <your secret>
# Default region name: us-east-1
# Default output format: json
```

Verify it works:
```bash
aws sts get-caller-identity
# Should print your account ID and ARN — no error
```

### Step 2 — Fill in your secrets

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Open `terraform.tfvars` and fill in every value. The five required secrets are:

| Variable | Where to get it |
|---|---|
| `openai_api_key` | platform.openai.com → API keys |
| `anthropic_api_key` | console.anthropic.com → API keys |
| `db_password` | Make up a strong password (letters + numbers, min 8 chars) |
| `django_secret_key` | Run the command below |
| `environment` | `"staging"` or `"production"` |

Generate a Django secret key:
```bash
cd ../generic_chatbot
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
cd ../terraform
```

### Step 3 — Deploy everything

```bash
bash setup.sh
```

This takes approximately 15–20 minutes. RDS and ElastiCache take the longest.
The script will pause after `terraform plan` and ask you to confirm before
making any changes.

What the script does:
1. Checks that `terraform`, `aws`, and credentials are ready
2. Runs the bootstrap step (creates the S3 state bucket and DynamoDB lock table)
3. Runs `terraform init` pointing at that state bucket
4. Shows you the full plan — review it before confirming
5. Applies the plan
6. Prints 9 GitHub secrets to configure

### Step 4 — Configure GitHub Actions secrets

After `setup.sh` finishes, it prints output like:

```
AWS_ACCOUNT_ID                                    123456789012
AWS_ROLE_NAME                                     humanlike-chatbot-staging-github-actions
AWS_S3_BUCKET_NAME_FRONTEND                       humanlike-chatbot-staging-frontend
...
```

Go to `https://github.com/<org>/<repo>/settings/secrets/actions` and add each
value as a repository secret using the exact name shown.

You can re-print these values at any time:
```bash
cd terraform
terraform output
```

### Step 5 — First application deployment

Push to the branch that triggers your workflow:

```bash
git push origin staging    # triggers .github/workflows/staging.yml
```

The workflow builds the React app, syncs it to S3, invalidates CloudFront, and
deploys the Django backend to Elastic Beanstalk. The first deploy takes about
5 minutes.

When it completes, visit the URLs from terraform output:
```bash
terraform output frontend_url    # https://xxxx.cloudfront.net
terraform output backend_api_url # http://xxxx.elasticbeanstalk.com
```

Test the backend health check:
```bash
curl $(terraform output -raw backend_api_url)/health/
# {"status": "ok"}
```

---

## Testing on a separate AWS account

Use this to validate Terraform changes without touching the existing staging
or production deployment.

### On your machine (Terraform apply)

Configure credentials for the test account in a named profile:

```bash
aws configure --profile test-account
# Enter the test account keys when prompted
```

Run setup with that profile:
```bash
cd terraform
AWS_PROFILE=test-account bash setup.sh
# Enter environment="staging" and a test project_name (e.g. "chatbot-test")
# in terraform.tfvars to keep resource names distinct
```

### In GitHub Actions (CI testing)

A dedicated workflow at `.github/workflows/test-iac.yml` triggers on the
`tf-iac` branch and uses `TEST_` prefixed secrets so it never touches the
existing staging secrets.

After `setup.sh` finishes on the test account, add these GitHub secrets
(prefix every terraform output name with `TEST_`):

| GitHub secret | Value from `terraform output` |
|---|---|
| `TEST_AWS_ACCOUNT_ID` | `github_secret_AWS_ACCOUNT_ID` |
| `TEST_AWS_ROLE_NAME` | `github_secret_AWS_ROLE_NAME` |
| `TEST_AWS_S3_BUCKET_NAME_FRONTEND` | `github_secret_AWS_S3_BUCKET_NAME_FRONTEND` |
| `TEST_AWS_CLOUDFRONT_DISTRIBUTION_ID` | `github_secret_AWS_CLOUDFRONT_DISTRIBUTION_ID` |
| `TEST_AWS_BACKEND_APPLICATION_NAME` | `github_secret_AWS_BACKEND_APPLICATION_NAME` |
| `TEST_AWS_BACKEND_ENVIRONMENT_NAME` | `github_secret_AWS_BACKEND_ENVIRONMENT_NAME` |
| `TEST_REACT_APP_API_URL` | `http://` + `terraform output -raw backend_api_url` + `/api` |

Then push to `tf-iac` to trigger the test workflow.

### Tear down the test environment

```bash
AWS_PROFILE=test-account terraform destroy -var-file=terraform.tfvars
```

On staging the destroy completes without extra steps.
On production, you must first disable deletion protection:
```bash
# Edit rds.tf: set deletion_protection = false, then:
AWS_PROFILE=test-account terraform apply -var-file=terraform.tfvars
AWS_PROFILE=test-account terraform destroy -var-file=terraform.tfvars
```

---

## Ongoing development

### Deploying application changes

No Terraform involvement. Just push to the appropriate branch:

```bash
git push origin staging     # → staging environment
git push origin main        # → production environment
git push origin tf-iac      # → test environment
```

GitHub Actions builds, syncs, and deploys automatically.

### Changing infrastructure

Edit the relevant `.tf` file, then preview and apply:

```bash
cd terraform
terraform plan -var-file=terraform.tfvars    # review what will change
terraform apply -var-file=terraform.tfvars   # apply it
```

Common changes:

**Scale up the application server:**
```hcl
# terraform.tfvars
eb_instance_type = "t3.medium"   # was t3.small
```

**Scale up the database:**
```hcl
# terraform.tfvars
db_instance_class = "db.t3.small"   # was db.t3.micro
```

**Rotate an API key:**
```hcl
# terraform.tfvars
openai_api_key = "sk-proj-new-key-here"
```
Then `terraform apply` — EB picks up the new env var on the next instance refresh.

**Add a custom domain:**
1. Create an ACM certificate for your domain in us-east-1 (AWS console)
2. Edit `cloudfront.tf`: add `aliases = ["your-domain.com"]` to the distribution
   and replace `cloudfront_default_certificate = true` with:
   ```hcl
   viewer_certificate {
     acm_certificate_arn      = "arn:aws:acm:us-east-1:..."
     ssl_support_method       = "sni-only"
     minimum_protocol_version = "TLSv1.2_2021"
   }
   ```
3. `terraform apply`
4. Point your domain's CNAME at the CloudFront domain name from `terraform output frontend_url`

### Viewing Terraform state

```bash
terraform state list                              # all resources
terraform state show aws_db_instance.main         # one resource in detail
terraform output                                  # all outputs
terraform output -raw redis_url                   # one sensitive output
```

### If something goes wrong mid-apply

Terraform stores what it completed in the state file. Re-running apply is safe —
it only creates or updates what is missing or changed.

```bash
terraform apply -var-file=terraform.tfvars   # picks up from where it left off
```

---

## Pending / Notes

- **GitHub Actions CI/CD not yet configured.** The IAM OIDC role and GitHub deployment role are provisioned by Terraform, but the `TEST_*` GitHub repository secrets have not been added yet. App deployments are currently done manually (see commands below). Wire up CI/CD after the manual flow is verified working end-to-end.

---

## File reference

| File | What it does |
|---|---|
| `bootstrap/main.tf` | Creates the S3 bucket and DynamoDB table for Terraform state. Run once. |
| `main.tf` | AWS provider (v6.4) and empty S3 backend declaration |
| `variables.tf` | All input variables with descriptions |
| `locals.tf` | Shared naming convention and common tags |
| `vpc.tf` | VPC, subnets, internet gateway, route tables, subnet groups |
| `security_groups.tf` | Firewall rules — ALB → instances → database/cache chain |
| `iam.tf` | EB instance profile, EB service role, GitHub OIDC role |
| `rds.tf` | MariaDB 10.11 database |
| `elasticache.tf` | Redis Serverless cache |
| `s3.tf` | Frontend assets bucket and application data bucket |
| `cloudfront.tf` | CloudFront distribution with OAC and SPA routing |
| `elasticbeanstalk.tf` | EB application and environment — all env vars wired here |
| `outputs.tf` | Printed after apply: URLs, GitHub secrets, debug values |
| `terraform.tfvars.example` | Copy to `terraform.tfvars` and fill in secrets |
| `setup.sh` | One-command deploy: bootstrap → init → plan → apply → print secrets |
