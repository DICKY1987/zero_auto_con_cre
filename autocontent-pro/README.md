# AutoContent Pro — Zero/Min‑Touch Omni‑Channel Video Automation (AWS + OSS‑first)

**Push a repo → CI deploys → Click “Authorize” once → Videos publish on schedule.**

This repository implements a production‑minded pipeline on AWS using **SAM**, **Step Functions**,
**Lambda (Python)**, and a **container-image Lambda** for video rendering (MoviePy/FFmpeg).
Omni‑channel uploaders for **YouTube**, **Facebook Pages/Instagram Reels**, **TikTok** are included.

> **Note:** Creating business accounts is *not* automated due to KYC/ToS. One‑time OAuth linking is required.

## What’s inside

- **State machine**: Topic → Research → Script → QA → Voice (Polly) → Video (16:9 + 9:16) → Parallel Publish (YT/FB/IG/TikTok)
- **Setup Portal** (S3 static website) with buttons to authorize all platforms
- **OAuth handlers** for YouTube, Facebook/IG (long‑lived page token), TikTok
- **Idempotency** (DynamoDB) for uploads, **retries** with backoff (Step Functions default)
- **Dedupe** in topic intake (simple recency window)
- **CloudWatch Dashboard & Alarms**; **AWS Budget** (optional) with email alert
- **CI/CD** via GitHub Actions with **AWS OIDC** (no static keys)
- **Providers**: swap LLM/TTS later; default uses simple script + Polly

## One‑time setup

1. Create OAuth apps:
   - **YouTube**: Google Cloud console → OAuth (Desktop or Web) → scopes: `youtube.upload`
   - **Facebook/IG**: Meta App (Facebook Login + Pages/IG permissions). After linking, the callback stores a **long‑lived page token** and **page id** automatically.
   - **TikTok**: TikTok for Developers (Open API) → OAuth client key/secret (scopes: `video.upload`).
2. In GitHub repo → **Settings → Secrets and variables → Actions**, set:
   - `AWS_OIDC_ROLE_ARN`, `AWS_REGION`, `AWS_ACCOUNT_ID`
   - `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`
   - `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`
   - `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`
   - *(optional)* `BUDGET_EMAIL`
3. Push to `main`. CI deploys with SAM and seeds params.
4. Open **PortalURL** (stack output) and click **Connect** for each platform once.

## Run cadence

Default: `rate(8 hours)`. Change in `infra/template.yaml` (EventBridge Rule).

## Cost tips

- This design uses standard Lambdas and a container Lambda for rendering. For heavier workloads,
  swap to **ECS Fargate Spot** with the same interface.
