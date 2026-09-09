# Deployment

StateGuard is deployed on AWS Lambda Function URL for the hackathon demo URL. App Runner was the first target, but AWS returned an internal system error during provisioning on this account after the service built successfully. Lambda Function URL gives the same AWS-hosted public HTTPS demo path without waiting on App Runner support.

## Canonical Repo

- Repo: `https://github.com/mofeed28/stateguard`
- Visibility: private during prep; Devpost requires this repo to be public before final submission
- Branch: `main`
- Health check: `/api/health`
- Runtime port: `8787` locally, or `$PORT` in hosted environments
- Live URL: `https://gzmrlkrayb3oz3qe22g2v5tv7e0qoqfa.lambda-url.us-east-1.on.aws/`

## Lambda Function URL Path

The active AWS deployment uses:

- Runtime: Python 3.11
- Handler: `stateguard.app.handler`
- Adapter: Mangum
- Function: `stateguard`
- Function URL auth: public / none
- Optional live Strands mode: disabled by default; enable only after Bedrock model access and Lambda IAM permissions are confirmed. Configure a live demo key before enabling it on a public URL.

The deployment bundle must be built with Python 3.11-compatible Linux wheels. From a non-Lambda Python version, use a platform-targeted install, then copy the app package and frontend assets into the zip root.

Optional live analysis environment variables:

```bash
STATEGUARD_USE_STRANDS_LLM=1
STATEGUARD_BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
STATEGUARD_LIVE_DEMO_KEY=replace-with-a-random-demo-key
STATEGUARD_LIVE_TIMEOUT_SECONDS=18
AWS_REGION=us-east-1
```

The Lambda execution role also needs permission for `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` on the chosen model.

## App Runner Path

Alternative container path:

1. Create an App Runner service.
2. Source from `mofeed28/stateguard`.
3. Use branch `main`.
4. Build from the repository Dockerfile, or build and push the image to ECR if the console path requires an image source.
5. Set service port to `8787` for Docker or `8080` for App Runner managed Python.
6. Set health check path to `/api/health`.
7. Keep environment variables empty for the demo.

The app is deterministic and does not require exchange, email, Bedrock, or model credentials.

## Local Commands

Python smoke test:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest -q
uvicorn stateguard.app:app --app-dir backend --host 127.0.0.1 --port 8787
```

Docker smoke test when Docker is available:

```bash
docker build -t stateguard .
docker run --rm -p 8787:8787 stateguard
curl http://127.0.0.1:8787/api/health
```

## Submission Notes

Use the Lambda Function URL for:

- Devpost demo URL
- Demo video
- README live demo section after deployment

The GitHub repo can stay private during prep, but Devpost requires a public source-code URL before final submission. Flip `mofeed28/stateguard` public only when the submission package is ready.
