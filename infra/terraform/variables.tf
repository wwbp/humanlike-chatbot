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
  description = "A short identifier prepended to every resource name I create. Changing this after the first deploy forces recreation of all resources, so set it once and leave it. DO NOT change this to match the chatbotlab repository name: it is the prefix on live S3 buckets, the RDS instance, the EB application and the Terraform state bucket, and renaming it would destroy the production database. The repo name lives in var.github_repo instead. Deliberately has no default — the CI workflows pass it via TF_VAR_project_name from the TF_PROJECT_PREFIX secret, and a wrong or empty value here would rename every resource, so I fail loudly instead of guessing."
  type        = string

  validation {
    condition     = length(var.project_name) > 0
    error_message = "project_name must not be empty — set TF_PROJECT_PREFIX (CI) or project_name in terraform.tfvars (local)."
  }
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
  description = "The OpenAI API key I inject into the Django application for chat and content moderation. Generate one at platform.openai.com."
  type        = string
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "The Anthropic API key I inject into the Django application for Claude-based chat models. Generate one at console.anthropic.com."
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "The master password for the MariaDB database I create on RDS. Use letters and numbers only — special characters can break the MySQL connection string."
  type        = string
  sensitive   = true
}

variable "django_secret_key" {
  description = "The cryptographic signing key Django uses for sessions and CSRF tokens. Must be at least 50 characters. Generate with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.django_secret_key) >= 50
    error_message = "I require the Django secret key to be at least 50 characters to meet Django's minimum security requirement."
  }
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
  description = "The GitHub repository name (without the org prefix). I use this alongside github_org to scope OIDC trust to exactly this repo. Note this is the *repository* name, which is deliberately not the same as project_name — the repo was renamed to chatbotlab, while project_name stays humanlike-chatbot because it names live AWS resources."
  type        = string
  default     = "chatbotlab"
}

# -----------------------------------------------------------------------
# Instance sizing
# -----------------------------------------------------------------------

variable "eb_instance_type" {
  description = "The EC2 instance type I use for the Elastic Beanstalk application servers. t3.small is a good starting point — upgrade to t3.medium if the app feels slow under load."
  type        = string
  default     = "t3.small"
}

variable "db_instance_class" {
  description = "The RDS instance class for the MariaDB database. db.t3.micro is free-tier eligible and sufficient for staging. Consider db.t3.small or db.t3.medium for production."
  type        = string
  default     = "db.t3.micro"
}

variable "create_github_oidc_provider" {
  description = "Set to false if a GitHub Actions OIDC provider already exists in this AWS account. Each account allows exactly one OIDC provider per URL — creating a second one for token.actions.githubusercontent.com will fail. Check with: aws iam list-open-id-connect-providers"
  type        = bool
  default     = true
}
