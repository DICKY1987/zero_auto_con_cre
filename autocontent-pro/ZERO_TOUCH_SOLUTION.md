# Zero‑Touch Solution — AI‑Driven Development & Deployment Guide

> **Goal:** Push a repo → CI deploys to AWS with no local setup → you click **Authorize** once in the Setup Portal → the system schedules and **autonomously creates & publishes videos** (YouTube, Facebook/IG, TikTok). All further development is performed by **AI via pull requests**, with CI redeploying automatically.

---

## 1) What “zero‑touch” means here
- **No local installs** are required (no AWS CLI/SAM/Docker on your laptop). Deployment is done by **GitHub Actions** using **OIDC** (short‑lived auth, no static keys).
- **No terminal prompts** for secrets. All secrets go into **GitHub Secrets**; infra parameters are written to **AWS SSM Parameter Store** by CI.
- **Only unavoidable step:** each platform’s **OAuth** (YouTube, Facebook/IG, TikTok) must be authorized **once** in the Setup Portal after the first deploy. Everything else is hands‑off.

> We intentionally **exclude a local PowerShell deploy script** from the zero‑touch path because it depends on your workstation state and prompts for secrets. If you still want one, see **Appendix A** for an optional Windows bootstrap script.

---

## 2) One‑time AWS setup for CI (OIDC role)
This lets your GitHub Actions workflow deploy to AWS **without** long‑lived keys.

### 2.1 Create the OIDC provider + deploy role (CloudShell)
Open **AWS CloudShell** and run:

```bash
# Save a minimal CloudFormation template:
cat > github-oidc-role.yaml <<'YAML'
Parameters:
  GitHubOwner: { Type: String }
  GitHubRepo:  { Type: String }
Resources:
  GitHubOIDC:
    Type: AWS::IAM::OIDCProvider
    Properties:
      Url: https://token.actions.githubusercontent.com
      ClientIdList: [ sts.amazonaws.com ]
      ThumbprintList: [ 6938fd4d98bab03faadb97b34396831e3780aea1 ]
  GitHubDeployRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: autocontent-pro-deploy
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Federated: !Ref GitHubOIDC
            Action: sts:AssumeRoleWithWebIdentity
            Condition:
              StringLike:
                token.actions.githubusercontent.com:sub: !Sub "repo:${GitHubOwner}/${GitHubRepo}:ref:refs/heads/main"
              StringEquals:
                token.actions.githubusercontent.com:aud: sts.amazonaws.com
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AdministratorAccess
Outputs:
  RoleArn:
    Value: !GetAtt GitHubDeployRole.Arn
YAML

# Deploy it (replace placeholders):
aws cloudformation deploy   --stack-name autocontent-oidc-role   --template-file github-oidc-role.yaml   --parameter-overrides GitHubOwner=YOUR_GH_OWNER GitHubRepo=YOUR_REPO   --capabilities CAPABILITY_NAMED_IAM
```

Copy the **RoleArn** output; you’ll put it into GitHub Secrets as `AWS_OIDC_ROLE_ARN`.

---

## 3) Put the repo under CI control
1. **Push the code** (e.g., contents of `autocontent-pro/`) to a new GitHub repo’s **main** branch.  
2. Set **GitHub Actions Secrets** (replace values as appropriate):  

```bash
# AWS
gh secret set AWS_OIDC_ROLE_ARN --body 'arn:aws:iam::<account-id>:role/autocontent-pro-deploy'
gh secret set AWS_REGION         --body 'us-east-1'
gh secret set AWS_ACCOUNT_ID     --body '<account-id>'

# OAuth apps
gh secret set YOUTUBE_CLIENT_ID       --body '<youtube-client-id>'
gh secret set YOUTUBE_CLIENT_SECRET   --body '<youtube-client-secret>'
gh secret set FACEBOOK_APP_ID         --body '<facebook-app-id>'
gh secret set FACEBOOK_APP_SECRET     --body '<facebook-app-secret>'
gh secret set TIKTOK_CLIENT_KEY       --body '<tiktok-client-key>'
gh secret set TIKTOK_CLIENT_SECRET    --body '<tiktok-client-secret>'

# Optional ops
gh secret set BUDGET_EMAIL            --body 'you@example.com'
```

3. The included **`.github/workflows/deploy.yml`** runs automatically on push: it builds with SAM, deploys the stack, seeds SSM parameters, and kicks the first Step Functions execution.

---

## 4) Authorize platforms once (Setup Portal)
After CI finishes:
1. In AWS → **CloudFormation → Stacks → your stack → Outputs**, open **`PortalURL`**.  
2. Click **Connect YouTube**, **Connect Facebook/IG**, **Connect TikTok**. This stores tokens/IDs in DynamoDB automatically.  
3. The pipeline runs on schedule (`rate(8 hours)`) and publishes in parallel. Change cadence in `infra/template.yaml` if desired.

---

## 5) Let AI “develop the system” (hands‑off)
Your AI acts as the **brain**; GitHub Actions is the **hands**.

### 5.1 Control prompt for your AI
Paste this when you want AI to implement changes or new features in the repo:

```text
ROLE: You are the Zero‑Touch DevOps AI for the AutoContent Pro repo.
GOAL: Ensure the repo deploys and runs unattended on AWS via GitHub Actions + OIDC, producing and publishing videos to YouTube/Facebook/IG/TikTok.

WHAT TO DO:
1) Generate/modify repo files exactly as needed (SAM template, Step Functions, Lambdas, OAuth portal, CI workflow).
2) Output changes as a git‑ready patch (unified diff) or a complete file list with full contents.
3) If AWS OIDC role isn’t set, emit the CloudFormation template + CLI to create it.
4) Emit gh secret set commands for all required secrets.
5) After deploy, tell me where to find PortalURL and what to click to authorize.

CONSTRAINTS:
- Non‑interactive deploy only (no local prompts).
- Secrets go to GitHub Secrets; infra secrets go to SSM at deploy time.
- Idempotent, retry‑safe, and cost‑aware.

DONE WHEN:
- First scheduled run uploads a private video on at least one channel.

OUTPUT FORMAT:
- ### PATCH
- ### AWS BOOTSTRAP
- ### GH SECRETS
- ### VERIFY
```

### 5.2 Continuous development loop
- Open a GitHub **Issue** (e.g., “Add real web research via Bedrock + search API”).  
- Have the AI post a **PATCH** (diffs) in the issue or PR.  
- You approve/merge → CI redeploys automatically → new behavior goes live.

---

## 6) Verify it’s working (checklist)
- **CloudFormation Outputs** show `PortalURL`, `HttpApiUrl`, `StateMachineArn`.
- **CloudWatch Dashboard** (created by the stack) shows Step Functions executions and Lambda metrics.
- **YouTube**: a **private** video appears after a scheduled run (portrait “Short” if ≤ 60s).  
- **DynamoDB** (`*-idem`) contains entries per channel/video key (idempotency marks).  
- **S3** assets bucket has `/audio/…` and `/videos/…` objects for each run.

---

## 7) Troubleshooting quick fixes
- **CI deploy fails**: check GitHub Actions logs; ensure `AWS_OIDC_ROLE_ARN` is correct and OIDC role trusts `repo:OWNER/REPO:ref:refs/heads/main`.
- **Portal callbacks 403**: verify `HttpApiUrl` is correct and that your OAuth app redirect URI matches the callback endpoints.
- **YouTube upload fails**: ensure the Google Cloud OAuth app is **in production** and has `youtube.upload` scope enabled; re‑connect in the Portal.
- **FB/IG fails**: the Facebook App must have the proper permissions; ensure the Page is selected and the IG Business Account is linked to the Page.
- **TikTok fails**: verify developer app scopes and that your account type supports API uploads.
- **Video rendering times out**: increase container‑image Lambda memory/timeout or migrate the render step to ECS Fargate Spot.

---

## 8) Security & cost notes
- OIDC avoids persistent AWS keys; all deploy auth is short‑lived.  
- Keep secrets in **GitHub Secrets**; let CI write them to **SSM**.  
- A monthly **AWS Budget** is included; set `BUDGET_EMAIL` to get alerts.  
- For heavier videos, move rendering to **ECS Fargate Spot** to control spend.

---

## Appendix A — Optional Windows local bootstrap (non‑zero‑touch)
If you insist on local deployment (not recommended), use the provided script to install tools via **winget**, read a `autocontent.secrets.json`, and deploy with SAM:

- Script: **`ZeroTouch-Windows-Bootstrap.ps1`** (provided separately)  
- Secrets file shape:

```json
{
  "AWS_REGION": "us-east-1",
  "YOUTUBE_CLIENT_ID": "xxx",
  "YOUTUBE_CLIENT_SECRET": "xxx",
  "FACEBOOK_APP_ID": "xxx",
  "FACEBOOK_APP_SECRET": "xxx",
  "TIKTOK_CLIENT_KEY": "xxx",
  "TIKTOK_CLIENT_SECRET": "xxx",
  "BUDGET_EMAIL": "you@example.com"
}
```

> This path can still prompt (e.g., Docker Desktop). The CI/OIDC path above is the true zero/min‑touch solution.

---

## TL;DR
1) Create the **OIDC deploy role** in AWS (CloudShell snippet above).  
2) Push the repo and set **GitHub Secrets**.  
3) CI builds & deploys automatically.  
4) Click **Connect** in the **Portal** once for YouTube/FB/IG/TikTok.  
5) From then on, have your **AI propose patches**; CI redeploys with **zero local work**.
