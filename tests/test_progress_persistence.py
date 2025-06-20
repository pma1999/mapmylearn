import asyncio
import json
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.api import app, save_progress_event, active_generations, active_generations_lock

class DummyRedis:
    def __init__(self):
        self.store = {}
    async def rpush(self, key, value):
        self.store.setdefault(key, []).append(value)
    async def lrange(self, key, start, end):
        data = self.store.get(key, [])
        if end == -1:
            end = None
        else:
            end += 1
        return data[start:end]
    async def expire(self, key, ttl):
        pass
    async def ping(self):
        return True

def async_run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

def test_save_progress_to_redis():
    redis = DummyRedis()
    async def fake_get():
        return redis
    with patch('backend.api.get_redis_client', fake_get):
        async_run(save_progress_event('task123', {'message':'hi'}, 1))
        assert json.loads(redis.store['progress:task123'][0])['message'] == 'hi'

def test_last_event_id_resume():
    redis = DummyRedis()
    async def fake_get():
        return redis
    # preload events
    async_run(redis.rpush('progress:taskx', json.dumps({'id':1,'message':'one'})))
    async_run(redis.rpush('progress:taskx', json.dumps({'id':2,'message':'two'})))
    with patch('backend.api.get_redis_client', fake_get):
        async_run(active_generations_lock.acquire())
        active_generations['taskx'] = {'status':'completed','progress_stream':[], 'last_event_id':2}
        active_generations_lock.release()
        client = TestClient(app)
        resp = client.get('/api/learning-path/taskx/progress-stream', headers={'Last-Event-ID':'1'})
        body = resp.content.decode()
        assert 'two' in body and 'one' not in body
