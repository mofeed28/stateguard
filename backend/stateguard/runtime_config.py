"""Runtime secrets are local files or a scoped AWS Secrets Manager object."""
import json
import os
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=1)
def cloud_secret():
    import boto3
    response=boto3.client('secretsmanager').get_secret_value(SecretId=os.environ['STATEGUARD_SECRET_ID'])
    return json.loads(response['SecretString'])

def value(name,default=None):
    if os.getenv('STATEGUARD_SECRET_ID'):
        return cloud_secret().get(name,default)
    return os.getenv(name,default)

def gmail_document(name):
    if os.getenv('STATEGUARD_SECRET_ID'):
        return cloud_secret()[name]
    root=Path(__file__).resolve().parents[2]
    return json.loads((root/'.secrets'/name).read_text(encoding='utf-8'))
