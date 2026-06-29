# AutoForge — Complete Deployment Guide
## Automobile Manufacturing App | Docker + ECR + Terraform + GitHub Actions

---

## What You Are Deploying

A Flask web application containerised with Docker, stored in Amazon ECR,
infrastructure provisioned by Terraform, deployed to EC2 via GitHub Actions.

```
GitHub push → CI/CD pipeline → Docker build → ECR push → Terraform → EC2 deploy
```

**Tech stack:** Python/Flask · MySQL 8 · Docker · Amazon ECR · EC2 · Terraform · GitHub Actions

---

## Prerequisites (install these on your Windows machine)

| Tool | Download |
|------|----------|
| Git | https://git-scm.com/download/win |
| AWS CLI v2 | https://aws.amazon.com/cli/ |
| Terraform | https://developer.hashicorp.com/terraform/install |
| VS Code (optional) | https://code.visualstudio.com |

Verify installs in PowerShell:
```powershell
git --version
aws --version
terraform --version
```

---

## PHASE 1 — AWS Account Setup (do this once, manually)

### Step 1.1 — Create IAM user for GitHub Actions

1. Open AWS Console → IAM → Users → Create user
2. Username: `github-actions-user`
3. Select: **Attach policies directly**
4. Attach these policies:
   - `AmazonEC2FullAccess`
   - `AmazonECR_FullAccess` (or `AmazonEC2ContainerRegistryFullAccess`)
   - `AmazonS3FullAccess`
   - `AmazonDynamoDBFullAccess`
   - `IAMFullAccess`
5. Create user → Go to user → Security credentials tab
6. Create access key → Use case: **CLI**
7. **Save the Access Key ID and Secret Access Key** — you will not see the secret again

### Step 1.2 — Configure AWS CLI on your machine

```powershell
aws configure
```

Enter when prompted:
```
AWS Access Key ID: <your access key>
AWS Secret Access Key: <your secret key>
Default region name: ap-south-1
Default output format: json
```

Verify:
```powershell
aws sts get-caller-identity
```

You should see your account ID, user ID, and ARN.

### Step 1.3 — Create S3 bucket for Terraform state

```powershell
aws s3api create-bucket `
  --bucket automobile-tfstate-bucket `
  --region ap-south-1 `
  --create-bucket-configuration LocationConstraint=ap-south-1

aws s3api put-bucket-versioning `
  --bucket automobile-tfstate-bucket `
  --versioning-configuration Status=Enabled
```

### Step 1.4 — Create DynamoDB table for Terraform state locking

```powershell
aws dynamodb create-table `
  --table-name automobile-tfstate-lock `
  --attribute-definitions AttributeName=LockID,AttributeType=S `
  --key-schema AttributeName=LockID,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST `
  --region ap-south-1
```

### Step 1.5 — Create EC2 Key Pair

```powershell
aws ec2 create-key-pair `
  --key-name automobile-key `
  --region ap-south-1 `
  --query "KeyMaterial" `
  --output text | Out-File -FilePath "$HOME\.ssh\automobile-key.pem" -Encoding ascii

# Fix permissions (PowerShell)
icacls "$HOME\.ssh\automobile-key.pem" /inheritance:r /grant:r "${env:USERNAME}:R"
```

View the private key content (you will need this for GitHub secrets):
```powershell
Get-Content "$HOME\.ssh\automobile-key.pem"
```

---

## PHASE 2 — GitHub Repository Setup

### Step 2.1 — Create GitHub repository

1. Go to https://github.com/new
2. Repository name: `automobile-app`
3. Visibility: **Private** (recommended — contains infra code)
4. Do NOT initialise with README (we already have code)
5. Click **Create repository**

### Step 2.2 — Push your code

Open PowerShell in your project folder:

```powershell
cd path\to\automobile-app

git init
git add .
git commit -m "Initial commit: Flask app + Docker + Terraform + CI/CD"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/automobile-app.git
git push -u origin main
```

### Step 2.3 — Add GitHub Actions secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add each of these:

| Secret name | Value |
|-------------|-------|
| `AWS_ACCESS_KEY_ID` | From Step 1.1 |
| `AWS_SECRET_ACCESS_KEY` | From Step 1.1 |
| `AWS_ACCOUNT_ID` | Run: `aws sts get-caller-identity --query Account --output text` |
| `EC2_KEY_PAIR_NAME` | `automobile-key` |
| `EC2_SSH_PRIVATE_KEY` | Full contents of `automobile-key.pem` (including BEGIN/END lines) |
| `SECRET_KEY` | Any random string e.g. `MyS3cur3Fl@skKey2024!` |
| `DB_USER` | `automobile_user` |
| `DB_PASSWORD` | `automobile_pass` |
| `DB_NAME` | `automobile_db` |
| `MYSQL_ROOT_PASSWORD` | `rootpassword` |

### Step 2.4 — Create production environment with approval gate

1. Go to repo → **Settings** → **Environments** → **New environment**
2. Name: `production`
3. Enable: **Required reviewers**
4. Add yourself as a reviewer
5. Click **Save protection rules**

This is the manual approval gate in Job 5 of the pipeline.

---

## PHASE 3 — Terraform First Run (provision AWS infrastructure)

You only need to do this once. After this, Terraform runs automatically in the pipeline.

### Step 3.1 — Initialise Terraform

```powershell
cd terraform
terraform init
```

Expected output:
```
Initializing the backend...
Successfully configured the backend "s3"!
Initializing provider plugins...
Terraform has been successfully initialized!
```

### Step 3.2 — Preview what Terraform will create

```powershell
terraform plan -var="key_pair_name=automobile-key"
```

You will see a list of resources to be created:
- `aws_ecr_repository.automobile_app`
- `aws_ecr_lifecycle_policy.automobile_app`
- `aws_instance.automobile_app`
- `aws_security_group.automobile_sg`
- `aws_iam_role.automobile_ec2_role`
- `aws_iam_role_policy.automobile_ecr_policy`
- `aws_iam_instance_profile.automobile_profile`

### Step 3.3 — Apply (create infrastructure)

```powershell
terraform apply -var="key_pair_name=automobile-key"
```

Type `yes` when prompted.

Wait 2-3 minutes. At the end you will see:

```
Outputs:
app_url             = "http://X.X.X.X"
ec2_public_ip       = "X.X.X.X"
ec2_public_dns      = "ec2-X-X-X-X.ap-south-1.compute.amazonaws.com"
ecr_repository_url  = "XXXXXXXXXXXX.dkr.ecr.ap-south-1.amazonaws.com/automobile-app"
ecr_repository_name = "automobile-app"
```

**Save the EC2 public IP and ECR repository URL** — you will need these.

---

## PHASE 4 — Trigger the CI/CD Pipeline

### Step 4.1 — Push a change to main

The pipeline triggers on every push to `main`. Make a small change:

```powershell
cd ..  # back to project root

# Edit any file, e.g. add a comment to run.py
# Then:
git add .
git commit -m "Trigger first deployment"
git push origin main
```

### Step 4.2 — Watch the pipeline

1. Go to your GitHub repo → **Actions** tab
2. You will see the pipeline running: `Automobile App — CI/CD Pipeline`
3. Click it to see all 6 jobs

**Job 1 — Lint & test** (~2 min)
- Spins up MySQL service container
- Installs Python dependencies
- Runs flake8 linter
- Seeds the database
- Runs pytest

**Job 2 — Docker build** (~3 min)
- Builds the multi-stage Docker image
- Saves it as a pipeline artifact

**Job 3 — Push to ECR** (~1 min)
- Logs into ECR using your AWS credentials
- Tags image as `:latest` and `:sha-XXXXXXX`
- Pushes both tags to ECR

**Job 4 — Terraform apply** (~2 min)
- Runs `terraform init` and `terraform apply`
- Updates infra if anything changed
- Outputs EC2 IP for the deploy job

**Job 5 — Manual approval** (PAUSED — waiting for you)
- Pipeline pauses here
- You will receive an email from GitHub
- Go to Actions → click the pipeline → click **Review deployments**
- Select `production` → click **Approve and deploy**

**Job 6 — Deploy to EC2** (~2 min)
- SSHs into EC2
- Writes the `.env` file
- Logs into ECR from the EC2 instance
- Pulls the new Docker image
- Runs `docker compose up -d`
- Runs a smoke test on `/auth/login`
- Prints the deployment summary

### Step 4.3 — Verify the deployment

After Job 6 completes successfully:

1. Open your browser
2. Go to `http://YOUR_EC2_PUBLIC_IP`
3. You should see the AutoForge login page

Login with:
- Username: `admin`
- Password: `Admin@123`

---

## PHASE 5 — Using the Application

### What you can do as admin

**Dashboard** — overview of vehicles, orders, pending orders, users

**Vehicles** (admin only)
- Add new vehicles with make, model, year, category, price, stock
- Edit existing vehicles
- Delete vehicles

**Orders**
- As admin: see all orders, update order status
- As regular user: place orders, view own orders

### Add a regular user

1. Log out
2. Go to `/auth/register`
3. Create a new account
4. Log in and place an order

---

## PHASE 6 — Every Subsequent Deployment

For every change after the first deployment, just:

```powershell
# Make your code changes
git add .
git commit -m "Your change description"
git push origin main
```

The pipeline runs automatically → approve at Job 5 → live in ~10 minutes.

---

## Troubleshooting

### Pipeline fails at Job 1 (lint)

Check the flake8 output. Usually a line too long (>120 chars) or unused import.

### Pipeline fails at Job 3 (ECR push)

Verify your `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` secrets are correct.
Check that your IAM user has `AmazonEC2ContainerRegistryFullAccess`.

### Pipeline fails at Job 4 (Terraform)

Common causes:
- S3 bucket name mismatch — check `terraform/providers.tf` bucket name matches Step 1.3
- DynamoDB table not created — re-run Step 1.4
- `EC2_KEY_PAIR_NAME` secret doesn't match the key pair name in AWS

### Pipeline fails at Job 6 (deploy — SSH timeout)

EC2 was just created and Docker is still installing via user_data.
Wait 3-5 minutes and re-run just Job 6 from the Actions UI.

### App shows 502 / can't connect after deploy

SSH into EC2 and check container status:

```powershell
ssh -i "$HOME\.ssh\automobile-key.pem" ubuntu@YOUR_EC2_IP
```

On EC2:
```bash
cd /opt/automobile-app
docker compose ps
docker compose logs automobile-app --tail=50
docker compose logs automobile-db --tail=30
```

### Containers keep restarting

Usually a DB connection issue. Check:
```bash
docker compose logs automobile-app | grep "OperationalError\|Can't connect"
```

MySQL takes ~30s to be ready. The healthcheck handles this — if it's failing, check your DB_ environment variables in the `.env` on EC2.

---

## Cost Estimate (ap-south-1)

| Resource | Cost |
|----------|------|
| EC2 t3.micro | ~$8/month |
| ECR storage (5 images) | ~$0.10/month |
| S3 (tfstate) | ~$0.01/month |
| DynamoDB (on-demand) | ~$0/month (tiny usage) |
| **Total** | **~$8-9/month** |

To stop costs: `terraform destroy -var="key_pair_name=automobile-key"`
This deletes EC2 and ECR but keeps the S3 state so you can recreate later.

---

## Project File Reference

```
automobile-app/
├── app/
│   ├── __init__.py          # Flask app factory, registers extensions + blueprints
│   ├── models.py            # SQLAlchemy models: User, Vehicle, Order
│   ├── forms.py             # WTForms: Login, Register, Vehicle, Order, Status
│   ├── routes/
│   │   ├── auth.py          # /auth/login, /auth/logout, /auth/register
│   │   ├── dashboard.py     # / (stats overview)
│   │   ├── vehicles.py      # /vehicles/ CRUD
│   │   └── orders.py        # /orders/ place + manage
│   ├── templates/           # Jinja2 HTML templates (dark theme)
│   └── static/css/          # Dark industrial CSS
├── config.py                # Dev/production Flask config, reads from .env
├── run.py                   # Gunicorn entry point
├── seed.py                  # Creates admin user + 5 sample vehicles
├── requirements.txt         # Pinned Python dependencies
├── Dockerfile               # Multi-stage: builder (gcc) + runtime (slim)
├── .dockerignore            # Excludes .git, venv, terraform from image
├── docker-compose.yml       # Local dev (not used in this deployment)
├── docker-compose.prod.yml  # EC2 production: app + db + volumes + network
├── .env.example             # Template — copy to .env and fill values
├── .gitignore               # Excludes .env, .terraform, __pycache__
├── terraform/
│   ├── providers.tf         # AWS provider + S3 remote backend config
│   ├── variables.tf         # Region, instance type, AMI, key pair name
│   ├── ecr.tf               # ECR repo + lifecycle policy (keep 5 images)
│   ├── security_group.tf    # Ports 22 (SSH), 80 (HTTP), 5000 (Flask)
│   ├── iam.tf               # EC2 instance role with ECR pull permission
│   ├── ec2.tf               # Single t3.micro with user_data bootstrap
│   ├── outputs.tf           # EC2 IP, ECR URL, app URL
│   └── user_data.sh         # Installs Docker + Docker Compose + AWS CLI
└── .github/workflows/
    └── deploy.yml           # 6-job CI/CD pipeline
```

---

## GitHub Secrets Quick Reference

| Secret | Where to get it |
|--------|----------------|
| `AWS_ACCESS_KEY_ID` | IAM → Users → github-actions-user → Security credentials |
| `AWS_SECRET_ACCESS_KEY` | Same as above (save on creation) |
| `AWS_ACCOUNT_ID` | `aws sts get-caller-identity --query Account --output text` |
| `EC2_KEY_PAIR_NAME` | `automobile-key` |
| `EC2_SSH_PRIVATE_KEY` | Contents of `automobile-key.pem` |
| `SECRET_KEY` | Any random string |
| `DB_USER` | `automobile_user` |
| `DB_PASSWORD` | `automobile_pass` |
| `DB_NAME` | `automobile_db` |
| `MYSQL_ROOT_PASSWORD` | `rootpassword` |
