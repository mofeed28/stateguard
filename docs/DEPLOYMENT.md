# Deployment

StateGuard is deployed on AWS Lambda Function URL for the hackathon demo URL. App Runner was the first target, but AWS returned an internal system error during provisioning on this account after the service built successfully. Lambda Function URL gives the same AWS-hosted public HTTPS demo path without waiting on App Runner support.

## Canonical Repo

- Repo: `https://github.com/mofeed28/stateguard`
- Visibility: private until final submission
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

The deployment bundle must be built with Python 3.11-compatible Linux wheels. From a non-Lambda Python version, use a platform-targeted install, then copy the app package and frontend assets into the zip root.

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

Use the App Runner URL for:

- Devpost demo URL
- Demo video
- README live demo section after deployment

Keep the GitHub repo private until the submission is otherwise ready, then decide whether the hackathon requires public source access.
