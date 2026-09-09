# Deployment

StateGuard should use AWS App Runner for the hackathon demo URL. It is the fastest AWS-native path for a public HTTPS endpoint while keeping the production story aligned with AgentCore, Bedrock, EventBridge, SQS, DynamoDB, and CloudWatch.

## Canonical Repo

- Repo: `https://github.com/mofeed28/stateguard`
- Visibility: private until final submission
- Branch: `main`
- Health check: `/api/health`
- Runtime port: `8787` locally, or `$PORT` in hosted environments

## App Runner Path

Recommended path:

1. Create an App Runner service.
2. Source from `mofeed28/stateguard`.
3. Use branch `main`.
4. Build from the repository Dockerfile, or build and push the image to ECR if the console path requires an image source.
5. Set service port to `8787` unless App Runner injects `$PORT`.
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
