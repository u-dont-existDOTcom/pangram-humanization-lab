from pangram_lab.cache import PangramCache
from pangram_lab.pangram4 import PangramClient


class FakeTransport:
    def __init__(self):
        self.calls=[]
    def request(self, method, url, headers=None, body=None):
        self.calls.append((method,url,body))
        if method == "POST":
            return {"status":200,"json":{"task_id":"t123"}}
        return {"status":200,"json":{"stage":"STAGE_SUCCESS","version":"4.0","headline":"Human Written","prediction_short":"Human","fraction_ai":0.0,"fraction_ai_assisted":0.0,"fraction_human":1.0,"text":"abc"}}


def test_checkpoint_before_poll_and_reuse_success(tmp_path):
    t=FakeTransport(); cache=PangramCache(tmp_path)
    synced=[]
    client=PangramClient("secret", transport=t, sleep=lambda _:None, sync=lambda reason:synced.append(reason))
    first=client.detect_cached("abc", cache, "base")
    assert first["prediction_short"] == "Human"
    assert [x[0] for x in t.calls] == ["POST","GET"]
    assert cache.lookup("pangram-4","4.0","abc","base")["status"] == "success"
    t.calls.clear()
    second=client.detect_cached("abc", cache, "base")
    assert second["prediction_short"] == "Human"
    assert t.calls == []
    assert any("task checkpoint" in x for x in synced)
    assert any("result" in x for x in synced)


def test_pending_task_polls_without_resubmit(tmp_path):
    t=FakeTransport(); cache=PangramCache(tmp_path)
    cache.save_pending("pangram-4","4.0","abc","base","existing")
    client=PangramClient("secret", transport=t, sleep=lambda _:None, sync=lambda _:None)
    client.detect_cached("abc",cache,"base")
    assert [x[0] for x in t.calls] == ["GET"]

class AmbiguousPostTransport:
    def __init__(self): self.calls=0
    def request(self, method, url, headers=None, body=None):
        self.calls += 1
        raise OSError('connection vanished after write')


def test_ambiguous_submit_is_never_automatically_resubmitted(tmp_path):
    t=AmbiguousPostTransport(); cache=PangramCache(tmp_path)
    client=PangramClient('secret',transport=t,sleep=lambda _:None,sync=lambda _:None)
    import pytest
    with pytest.raises(Exception): client.detect_cached('abc',cache,'base')
    rec=cache.lookup('pangram-4','4.0','abc','base')
    assert rec['status'] == 'submit_ambiguous'
    calls=t.calls
    with pytest.raises(Exception,match='ambiguous'):
        client.detect_cached('abc',cache,'base')
    assert t.calls == calls

class CurrentContractTransport:
    def __init__(self): self.calls=[]
    def request(self,method,url,headers=None,body=None):
        self.calls.append((method,url,headers,body))
        if method=='GET' and url.endswith('/task/00000000-0000-0000-0000-000000000000'):
            return {'status':404,'json':{'detail':'not found'}}
        if method=='POST': return {'status':200,'json':{'task_id':'t9'}}
        return {'status':200,'json':{'stage':'STAGE_SUCCESS','version':'4.0','headline':'Human Written','prediction_short':'Human','fraction_ai':0,'fraction_ai_assisted':0,'fraction_human':1,'text':'abc'}}


def test_current_async_contract_uses_zero_task_auth_probe_and_no_model_field(tmp_path):
    t=CurrentContractTransport(); cache=PangramCache(tmp_path)
    client=PangramClient('secret',transport=t,sleep=lambda _:None,sync=lambda _:None)
    client.probe_auth()
    result=client.detect_cached('abc',cache,'base')
    assert result['version']=='4.0'
    assert not any(url.endswith('/models') for _,url,_,_ in t.calls)
    post=[x for x in t.calls if x[0]=='POST'][0]
    assert post[3] == {'text':'abc','public_dashboard_link':False}
    assert post[2]['x-api-key']=='secret'

class Http500SubmitTransport:
    def __init__(self): self.calls=0
    def request(self, method, url, headers=None, body=None):
        self.calls += 1
        if method == 'POST':
            return {'status':500,'json':{'detail':'server failed after request reached service'}}
        raise AssertionError('poll must not occur without task id')


def test_submit_http_5xx_is_treated_as_ambiguous_and_not_reposted(tmp_path):
    import pytest
    t=Http500SubmitTransport(); cache=PangramCache(tmp_path)
    client=PangramClient('secret',transport=t,sleep=lambda _:None,sync=lambda _:None)
    with pytest.raises(Exception): client.detect_cached('abc',cache,'base')
    rec=cache.lookup('pangram-4','4.0','abc','base')
    assert rec['status']=='submit_ambiguous'
    calls=t.calls
    with pytest.raises(Exception,match='ambiguous'):
        client.detect_cached('abc',cache,'base')
    assert t.calls==calls
