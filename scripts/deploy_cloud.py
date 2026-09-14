"""Update the existing StateGuard Lambda; credentials never enter its ZIP."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / '.secrets'
CLI = Path(os.environ['LOCALAPPDATA']) / 'Programs/Amazon/AWSCLIV2/aws.exe'

def aws(*args, allow_missing=False):
    result = subprocess.run([str(CLI), *args, '--profile', 'stateguard', '--region', 'us-east-1', '--output', 'json'], capture_output=True, text=True)
    if result.returncode:
        if allow_missing and any(code in result.stderr for code in ('ResourceNotFoundException', 'NoSuchEntity')):
            return None
        # AWS errors may contain secret parameters; do not echo them.
        raise RuntimeError('AWS operation failed: ' + ' '.join(args[:2]))
    return json.loads(result.stdout) if result.stdout.strip() else {}

def private_json(name, data):
    target = PRIVATE / name
    target.write_text(json.dumps(data), encoding='utf-8')
    return 'file://' + target.as_posix()

def provision():
    from dotenv import dotenv_values
    config = aws('lambda', 'get-function-configuration', '--function-name', 'stateguard')
    private_json('aws-before-full-config.json', config)
    table = aws('dynamodb', 'describe-table', '--table-name', 'stateguard-state', allow_missing=True)
    if not table:
        table = aws('dynamodb', 'create-table', '--table-name', 'stateguard-state', '--billing-mode', 'PAY_PER_REQUEST', '--attribute-definitions', 'AttributeName=pk,AttributeType=S', '--key-schema', 'AttributeName=pk,KeyType=HASH')
    aws('dynamodb', 'wait', 'table-exists', '--table-name', 'stateguard-state')
    values = dotenv_values(ROOT / '.env')
    key = values.get('STATEGUARD_LIVE_DEMO_KEY') or (ROOT / '.stateguard-live-key').read_text().strip()
    secret_data = {'OPENAI_API_KEY': values['OPENAI_API_KEY'], 'STATEGUARD_LIVE_DEMO_KEY': key}
    for name in ('gmail-token.json', 'gmail-demo-attempt.json'):
        secret_data[name] = json.loads((PRIVATE / name).read_text(encoding='utf-8-sig'))
    secret_file = private_json('aws-runtime-secret.json', secret_data)
    secret = aws('secretsmanager', 'describe-secret', '--secret-id', 'stateguard/runtime', allow_missing=True)
    if secret:
        aws('secretsmanager', 'put-secret-value', '--secret-id', secret['ARN'], '--secret-string', secret_file)
    else:
        secret = aws('secretsmanager', 'create-secret', '--name', 'stateguard/runtime', '--secret-string', secret_file)
    table_arn = aws('dynamodb', 'describe-table', '--table-name', 'stateguard-state')['Table']['TableArn']
    policy = {'Version':'2012-10-17','Statement':[
        {'Effect':'Allow','Action':['dynamodb:GetItem','dynamodb:PutItem','dynamodb:Scan'],'Resource':table_arn},
        {'Effect':'Allow','Action':['secretsmanager:GetSecretValue'],'Resource':secret['ARN']}]}
    aws('iam','put-role-policy','--role-name',config['Role'].split('/')[-1],'--policy-name','StateGuardRuntime','--policy-document',private_json('aws-runtime-policy.json',policy))
    env = config.get('Environment', {}).get('Variables', {})
    for name in ('AWS_PROFILE','OPENAI_API_KEY','STATEGUARD_LIVE_DEMO_KEY'):
        env.pop(name, None)
    env.update(STATEGUARD_STATE_TABLE='stateguard-state',STATEGUARD_SECRET_ID=secret['ARN'],STATEGUARD_USE_STRANDS_LLM='1',STATEGUARD_MODEL_PROVIDER='openai',STATEGUARD_OPENAI_MODEL_ID='gpt-5-mini')
    private_json('aws-full-environment.json', {'Variables':env})
    print('Shared table, runtime secret and scoped Lambda permissions ready.')

def package():
    extra = ROOT / 'build/cloud-extra-v2'
    assert (extra / 'openai').is_dir()
    entries = {}
    with zipfile.ZipFile(PRIVATE / 'aws-original.zip') as old:
        for name in old.namelist():
            if not name.endswith('/') and not name.startswith(('stateguard/','frontend/','docs/')) and '__pycache__' not in name:
                entries[name] = old.read(name)
    # Overwrite matching files while retaining shared namespace modules.
    for path in extra.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            rel = path.relative_to(extra).as_posix()
            if rel.startswith('googleapiclient/discovery_cache/documents/') and not rel.endswith('/gmail.v1.json'):
                continue
            entries[rel] = path.read_bytes()
    for folder, prefix in [('backend/stateguard','stateguard'),('frontend','frontend'),('docs','docs')]:
        for path in (ROOT / folder).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                entries[prefix + '/' + path.relative_to(ROOT / folder).as_posix()] = path.read_bytes()
    secret = json.loads((PRIVATE / 'aws-runtime-secret.json').read_text())
    sensitive = [secret['OPENAI_API_KEY'],secret['STATEGUARD_LIVE_DEMO_KEY']]
    sensitive.extend(secret['gmail-token.json'].get(k,'') for k in ('token','refresh_token','client_secret'))
    for name, data in entries.items():
        assert not any(value and value.encode() in data for value in sensitive), 'Secret detected in deployment content'
        assert not name.startswith(('.secrets/','.env'))
    target = PRIVATE / 'aws-full-update.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items(): archive.writestr(name,data)
    assert sum(map(len,entries.values())) < 250 * 1024**2
    print(f'Package ready: {target.stat().st_size:,} bytes; secret scan passed.')

def deploy():
    archive = PRIVATE / 'aws-full-update.zip'
    assert archive.stat().st_size < 50 * 1024**2, 'Use S3 for packages over 50 MB'
    config = aws('lambda','get-function-configuration','--function-name','stateguard')
    aws('lambda','update-function-configuration','--function-name','stateguard','--revision-id',config['RevisionId'],'--timeout','120','--memory-size','1024','--environment','file://' + (PRIVATE/'aws-full-environment.json').as_posix())
    aws('lambda','wait','function-updated-v2','--function-name','stateguard')
    config = aws('lambda','get-function-configuration','--function-name','stateguard')
    result = aws('lambda','update-function-code','--function-name','stateguard','--revision-id',config['RevisionId'],'--zip-file','fileb://' + archive.as_posix())
    aws('lambda','wait','function-updated-v2','--function-name','stateguard')
    print('Lambda updated; code SHA256: ' + result['CodeSha256'])

def schedule():
    rule = aws('events','put-rule','--name','stateguard-worker','--schedule-expression','rate(1 minute)','--state','ENABLED')
    config = aws('lambda','get-function-configuration','--function-name','stateguard')
    policy = aws('lambda','get-policy','--function-name','stateguard',allow_missing=True)
    if not policy or not any(s['Sid']=='StateGuardWorkerSchedule' for s in json.loads(policy['Policy'])['Statement']):
        aws('lambda','add-permission','--function-name','stateguard','--statement-id','StateGuardWorkerSchedule','--action','lambda:InvokeFunction','--principal','events.amazonaws.com','--source-arn',rule['RuleArn'])
    result = aws('events','put-targets','--rule','stateguard-worker','--targets',private_json('aws-worker-target.json',[{'Id':'stateguard','Arn':config['FunctionArn'],'Input':json.dumps({'source':'stateguard.worker'})}]))
    assert result['FailedEntryCount']==0
    print('Cloud sandbox worker scheduled every minute.')

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['provision','package','deploy','schedule'])
    globals()[parser.parse_args().action]()
