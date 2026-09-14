"""Offline contract tests for DynamoDB optimistic concurrency."""
import copy
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import ClientError
from stateguard import storage, workflow

class FakeTable:
    def __init__(self): self.items={}; self.lock=Lock(); self.conflict_once=False
    def get_item(self,Key,**kwargs):
        with self.lock: return {'Item':copy.deepcopy(self.items[Key['pk']])} if Key['pk'] in self.items else {}
    def put_item(self,Item,ConditionExpression,**kwargs):
        with self.lock:
            old=self.items.get(Item['pk'])
            conflict=(old is not None) if ConditionExpression=='attribute_not_exists(pk)' else (old is None or old['revision']!=kwargs['ExpressionAttributeValues'][':previous'])
            if self.conflict_once: self.conflict_once=False; conflict=True
            if conflict: raise ClientError({'Error':{'Code':'ConditionalCheckFailedException'}},'PutItem')
            self.items[Item['pk']]=copy.deepcopy(Item)
    def scan(self,**kwargs): return {'Items':list(self.items.values())}

def test_dynamo_concurrent_worker_sends_once(monkeypatch):
    t=FakeTable();monkeypatch.setenv('STATEGUARD_STATE_TABLE','test');monkeypatch.setattr(storage,'table',lambda:t)
    run=workflow.create_run('healthy')
    with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(lambda _:workflow.tick(run['id']),range(8)))
    assert workflow.get_run(run['id'])['deliveries']==1
    assert workflow.get_run(run['id'])['status']=='completed'

def test_dynamo_retries_conflicting_state_write(monkeypatch):
    t=FakeTable();monkeypatch.setenv('STATEGUARD_STATE_TABLE','test');monkeypatch.setattr(storage,'table',lambda:t)
    run=workflow.create_run('accepted_timeout');t.conflict_once=True
    result=workflow.tick(run['id'])
    assert result['prevented_retries']==1
    assert result['version']==1

def test_dynamo_missing_key_rejected(monkeypatch):
    import pytest
    monkeypatch.setenv('STATEGUARD_STATE_TABLE','test');monkeypatch.setattr(storage,'table',FakeTable)
    with pytest.raises(KeyError): storage.get('runs','missing')
