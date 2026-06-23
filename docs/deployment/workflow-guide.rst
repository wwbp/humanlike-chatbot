Managing ChatLab Infrastructure
===============================

ChatLab includes three GitHub Actions workflows to automate the entire lifecycle
of your AWS environment. These let you **deploy**, **destroy**, or **fully reset**
your cloud infrastructure — safely, consistently, and reproducibly.

Each workflow can be triggered manually in GitHub under
**Actions → Workflow Dispatch**.

.. note::

   These workflows assume that your AWS credentials
   (``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY``)
   are stored securely under your repository's **Settings → Secrets and variables → Actions**.

---

Deploy Workflow
---------------

**Purpose:** Creates or updates all AWS resources needed to host ChatLab.

**When to use:**

- You are setting up ChatLab for the first time.
- You have made changes to the backend, frontend, or Terraform configuration.
- You need to redeploy a clean environment after running the **Reset** workflow.

**What it does:**

- Provisions all required AWS services:
  Elastic Beanstalk, RDS, Redis, S3, CloudFront, and Route53.
- Builds and uploads the frontend to S3.
- Configures DNS and TLS certificates automatically.
- Typically completes in **10-15 minutes**.

---

Destroy Workflow
----------------

**Purpose:** Cleanly removes AWS resources managed by Terraform
while preserving the state backend for later redeployment.

**When to use:**

- You want to temporarily remove your infrastructure.
- You are testing or debugging Terraform changes.
- You want Terraform to release state locks.

**What it does:**

- Deletes all ChatLab AWS resources managed by Terraform.
- Keeps DynamoDB lock table and Terraform state S3 bucket.
- Runs safely and quickly without affecting your configuration files.

---

Reset Workflow
--------------

**Purpose:** Emergency cleanup — removes *everything*, including
Terraform state and AWS backend components.

**When to use:**

- Deployments are failing due to conflicts such as ``AlreadyExists`` or ``LockError``.
- You need a **completely fresh environment**.
- You are migrating ChatLab to a new AWS account or domain.

**What it does:**

- Deletes *all* ChatLab AWS resources:
  Elastic Beanstalk, IAM roles, RDS, Redis, S3, CloudFront, Route53, and DynamoDB.
- Ignores missing resources safely (no workflow failures).
- Can be rerun safely anytime.
- Once complete, rerun the **Deploy** workflow to rebuild the full stack.

---

Recommended Workflow Sequence
-----------------------------

+-----------------------------------+---------------------------------------------+
| **Task**                          | **Workflow to Run**                         |
+===================================+=============================================+
| First-time setup                  | :doc:`deploy <deploy>`                      |
+-----------------------------------+---------------------------------------------+
| Temporary teardown (keep state)   | :doc:`destroy <destroy>`                    |
+-----------------------------------+---------------------------------------------+
| Full environment reset (wipe all) | :doc:`reset <reset>`                        |
+-----------------------------------+---------------------------------------------+

---

Best Practices
--------------

- Always check AWS usage after deployment to ensure billing stays within your limits.
- Use the **Destroy** workflow before **Reset** whenever possible — it's faster and cleaner.
- Wait at least **2-3 minutes** between **Reset** and **Deploy** runs to allow AWS to finalize deletions.
- Keep your domain and AWS credentials consistent between runs.

---

See Also
--------

- :doc:`/deployment/aws-deployment` — full deployment walkthrough  
- :doc:`/deployment/index` — overview of ChatLab's cloud setup  
