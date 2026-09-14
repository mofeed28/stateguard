# AWS deployment

The full app runs on the existing `stateguard` Lambda in `us-east-1`:

https://gzmrlkrayb3oz3qe22g2v5tv7e0qoqfa.lambda-url.us-east-1.on.aws/

The September 14 update includes the sandbox, Gmail recovery, OpenAI investigations and corrected architecture. See `aws-live-verification.json` for validation evidence.

## Resources

- Lambda: Python 3.11, `stateguard.app.handler`, 1024 MB, 120-second timeout.
- DynamoDB: `stateguard-state`, on-demand capacity, string key `pk`; conditional writes protect shared state.
- Secrets Manager: `stateguard/runtime` holds OpenAI and demo keys, Gmail OAuth token and original claim. None are in the deployment ZIP.
- IAM: `StateGuardRuntime` grants the Lambda role GetItem/PutItem/Scan on this table and GetSecretValue on this secret.
- EventBridge: `stateguard-worker` invokes the sandbox worker every minute. It sends no real email or notification.

AWS state is separate from local SQLite. API and cloud worker share DynamoDB. Locally set `STATEGUARD_DB_PATH` to a persistent file.

## Updating

GitHub pushes do not deploy automatically. With AWS profile `stateguard` authenticated:

```powershell
python scripts/deploy_cloud.py provision
python scripts/deploy_cloud.py package
python scripts/deploy_cloud.py deploy
python scripts/deploy_cloud.py schedule
python scripts/verify_cloud.py
```

This maintenance script targets the existing deployment; it is not a clean-account bootstrap. It uses the backed-up Linux ZIP `.secrets/aws-original.zip` and additional Linux Python 3.11 wheels in `build/cloud-extra-v2`. Install those with:

```powershell
python -m pip install --target build/cloud-extra-v2 --platform manylinux2014_x86_64 --implementation cp --python-version 3.11 --only-binary=:all: 'google-api-python-client>=2.0.0' 'google-auth-oauthlib>=1.2.0' 'openai==2.54.0' 'python-dotenv>=1.0.0'
```

Provision reads ignored local secrets, uploads them to the scoped secret and preserves unrelated Lambda settings. Package scans content for secrets. Deploy checks Lambda revisions. The preceding ZIP and configuration remain in ignored backups.

Enter the value from `.stateguard-live-key` in the masked demo access field, never a provider API key. AWS sandbox writes, live investigations and Gmail actions require it. Read-only examples and architecture are public. Protected actions reject cross-origin requests.

## Operational limits

The worker scans a small demo table. Production needs bounded retention, scalable dispatch, individual authentication and provider idempotency. Test Gmail OAuth grants can expire and require reconnecting. Bedrock remains quota-blocked; errors do not substitute fabricated analysis. The legacy custom-text live preview still uses Bedrock; use sandbox or Gmail for verified OpenAI investigations.

Verification checks public pages, exact diagram content, access controls, concurrent sandbox updates, live model calls and existing-message Gmail reconciliation. It never sends email. Model checks incur normal API usage. AWS resources and the secret have normal ongoing service charges.
