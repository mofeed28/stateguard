"""Local SQLite or shared DynamoDB state with conditional versioned writes."""
import json
import os
import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path

@contextmanager
def connection():
    path=os.getenv('STATEGUARD_DB_PATH',str(Path(tempfile.gettempdir())/'stateguard-sandbox.sqlite3'))
    conn=sqlite3.connect(path,timeout=10)
    try:
        with conn:
            yield conn
    finally:
        conn.close()

def table():
    import boto3
    return boto3.resource('dynamodb').Table(os.environ['STATEGUARD_STATE_TABLE'])

def check_namespace(namespace):
    if namespace not in ('runs','gmail_recovery'):
        raise ValueError('Unknown state namespace')

def get(namespace,key):
    check_namespace(namespace)
    if os.getenv('STATEGUARD_STATE_TABLE'):
        item=table().get_item(Key={'pk':namespace+':'+key},ConsistentRead=True).get('Item')
        if item is None: raise KeyError(key)
        return json.loads(item['data'])
    with connection() as c:
        c.execute(f'CREATE TABLE IF NOT EXISTS {namespace} (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
        row=c.execute(f'SELECT data FROM {namespace} WHERE id=?',(key,)).fetchone()
    if row is None: raise KeyError(key)
    return json.loads(row[0])

def all_records(namespace):
    check_namespace(namespace)
    if os.getenv('STATEGUARD_STATE_TABLE'):
        from boto3.dynamodb.conditions import Attr
        result=[]; options={'FilterExpression':Attr('pk').begins_with(namespace+':'),'ConsistentRead':True}
        while True:
            response=table().scan(**options)
            result.extend(json.loads(i['data']) for i in response.get('Items',[]))
            if 'LastEvaluatedKey' not in response: return result
            options['ExclusiveStartKey']=response['LastEvaluatedKey']
    with connection() as c:
        c.execute(f'CREATE TABLE IF NOT EXISTS {namespace} (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
        return [json.loads(row[0]) for row in c.execute(f'SELECT data FROM {namespace}').fetchall()]

def mutate(namespace,key,action,initial=None,create_only=False):
    """Callbacks only change local state; never send external requests inside them."""
    check_namespace(namespace)
    if os.getenv('STATEGUARD_STATE_TABLE'):
        from botocore.exceptions import ClientError
        t=table(); pk=namespace+':'+key
        for _ in range(8):
            item=t.get_item(Key={'pk':pk},ConsistentRead=True).get('Item')
            if item and create_only: raise ValueError('State already exists')
            if not item and initial is None: raise KeyError(key)
            state=json.loads(item['data']) if item else initial()
            action(state)
            revision=int(item['revision'])+1 if item else 1
            options={'ConditionExpression':'attribute_not_exists(pk)'} if not item else {'ConditionExpression':'revision = :previous','ExpressionAttributeValues':{':previous':item['revision']}}
            try:
                t.put_item(Item={'pk':pk,'revision':revision,'data':json.dumps(state)},**options)
                return state
            except ClientError as exc:
                if exc.response['Error']['Code']!='ConditionalCheckFailedException': raise
        raise ValueError('State changed concurrently. Refresh and retry.')
    with connection() as c:
        c.execute(f'CREATE TABLE IF NOT EXISTS {namespace} (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
        c.execute('BEGIN IMMEDIATE')
        row=c.execute(f'SELECT data FROM {namespace} WHERE id=?',(key,)).fetchone()
        if row and create_only: raise ValueError('State already exists')
        if not row and initial is None: raise KeyError(key)
        state=json.loads(row[0]) if row else initial()
        action(state)
        c.execute(f'INSERT OR REPLACE INTO {namespace} VALUES (?,?)',(key,json.dumps(state)))
    return state
