# -----------------------------------------------------------------------------
# variables.tf — every input this configuration accepts
#
# Sensitive variables (marked sensitive = true) are never printed in plan
# output or stored in plaintext in state. They still live in state as
# encrypted values — which is why the state bucket uses AES-256 encryption.
#
# Fill in actual values in terraform.tfvars (copy from terraform.tfvars.example).
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------
# Core deployment settings
# -----------------------------------------------------------------------

variable "aws_region" {
  description = "The AWS region where I deploy all infrastructure. I default to us-east-1 because that is where the existing ElastiCache cluster and EB environment live."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "A short identifier prepended to every resource name I create. Changing this after the first deploy forces recreation of all resources, so set it once and leave it."
  type        = string
  default     = "humanlike-chatbot"
}

variable "environment" {
  description = "Which deployment environment I am provisioning. I use this to adjust resource sizing and backup retention — staging is cheaper, production is durable."
  type        = string
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "I only accept 'staging' or 'production' as valid environments."
  }
}

# -----------------------------------------------------------------------
# Secrets — these are passed in at deploy time and never hardcoded
# -----------------------------------------------------------------------

variable "openai_api_key" {
  description = "The OpenAI API key I inject into the Django application for chat and content moderation. Generate one at platform.openai.com. Leave empty if using Anthropic only."
  type        = string
  sensitive   = true
  default     = ""
}

variable "anthropic_api_key" {
  description = "The Anthropic API key I inject into the Django application for Claude-based chat models. Generate one at console.anthropic.com. Leave empty if using OpenAI only."
  type        = string
  sensitive   = true
  default     = ""
}

variable "db_password" {
  description = "The master password for the MariaDB database I create on RDS. Use letters and numbers only — special characters can break the MySQL connection string."
  type        = string
  sensitive   = true
}

variable "django_secret_key" {
  description = "The cryptographic signing key Django uses for sessions and CSRF tokens. Leave empty to auto-generate a stable key (recommended — the key is stored in Terraform state and reused on every deploy)."
  type        = string
  sensitive   = true
  default     = ""
}

# -----------------------------------------------------------------------
# GitHub — used to set up passwordless CI/CD via OIDC
# -----------------------------------------------------------------------

variable "github_org" {
  description = "The GitHub organization (or username) that owns this repository. I use this to restrict which GitHub Actions workflows can assume the deployment IAM role."
  type        = string
  default     = "wwbp"
}

variable "github_repo" {
  description = "The GitHub repository name (without the org prefix). I use this alongside github_org to scope OIDC trust to exactly this repo."
  type        = string
  default     = "humanlike-chatbot"
}

# -----------------------------------------------------------------------
# Instance sizing
# -----------------------------------------------------------------------

variable "eb_instance_type" {
  description = "The EC2 instance type I use for the Elastic Beanstalk application servers. t3.small is a good starting point — upgrade to t3.medium if the app feels slow under load."
  type        = string
  default     = "t3.small"
}

variable "eb_max_instances" {
  description = "The maximum number of EC2 instances the auto-scaling group can launch. Set to 1 for most studies. Increase if you expect hundreds of simultaneous conversations."
  type        = number
  default     = 1
}

variable "db_instance_class" {
  description = "The RDS instance class for the MariaDB database. db.t3.micro is sufficient for most studies. Consider db.t3.small for larger deployments."
  type        = string
  default     = "db.t3.micro"
}

variable "admin_panel_password" {
  description = "The password for the Django admin panel. You will use this to log in and configure your chatbot at /api/admin/. Choose something you will remember."
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Optional custom domain to serve the chatbot from (e.g. chatbot.mylab.org). Leave empty to use the auto-assigned CloudFront URL (https://xxxx.cloudfront.net). If set, an SSL certificate will be created — you will need to add a DNS validation record at your registrar."
  type        = string
  default     = ""
}

variable "create_github_oidc_provider" {
  description = "Set to false if a GitHub Actions OIDC provider already exists in this AWS account. Each account allows exactly one OIDC provider per URL — creating a second one for token.actions.githubusercontent.com will fail. Check with: aws iam list-open-id-connect-providers"
  type        = bool
  default     = true
}
