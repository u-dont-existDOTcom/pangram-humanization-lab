

def test_live_smoke_main_reports_failed_subchecks_before_nonzero_exit(tmp_path,monkeypatch,capsys):
    import scripts.live_smoke as live_smoke

    monkeypatch.setattr(live_smoke,'_model_smoke',lambda *args,**kwargs:{'status':'fail','detail':'schema mismatch'})
    monkeypatch.setattr(live_smoke,'run_heartbeat_check',lambda **kwargs:{'status':'pass'})
    out=tmp_path/'report.json'
    rc=live_smoke.main(['--claude','--out',str(out)])
    captured=capsys.readouterr()
    assert rc == 2
    assert 'live_smoke_failed=claude' in captured.err
    assert 'schema mismatch' in captured.err
    assert f'live_smoke_report={out}' in captured.out


def test_live_smoke_marks_pangram_unauthorized_as_credential_required(tmp_path,monkeypatch,capsys):
    import httpx
    import json
    import scripts.live_smoke as live_smoke

    request=httpx.Request('GET','https://text.external-api.pangram.com/task/00000000-0000-0000-0000-000000000000')
    response=httpx.Response(401,request=request)
    def fail(_args):
        raise httpx.HTTPStatusError('unauthorized',request=request,response=response)
    monkeypatch.setattr(live_smoke,'_pangram_smoke',fail)
    monkeypatch.setenv('PANGRAM_API_KEY','rejected-key')
    out=tmp_path/'report.json'

    rc=live_smoke.main(['--pangram','--out',str(out)])
    captured=capsys.readouterr()
    report=json.loads(out.read_text())
    assert rc == 3
    assert report['credential_required'] == 'PANGRAM_API_KEY'
    assert report['credential_status_code'] == 401
    assert 'live_smoke_credential_required=PANGRAM_API_KEY' in captured.err


def test_live_smoke_marks_pangram_payment_required_as_account_action(tmp_path,monkeypatch,capsys):
    import httpx
    import json
    import scripts.live_smoke as live_smoke

    request=httpx.Request('GET','https://text.external-api.pangram.com/task/00000000-0000-0000-0000-000000000000')
    response=httpx.Response(402,request=request)
    def fail(_args):
        raise httpx.HTTPStatusError('payment required',request=request,response=response)
    monkeypatch.setattr(live_smoke,'_pangram_smoke',fail)
    monkeypatch.setenv('PANGRAM_API_KEY','valid-but-empty-account')
    out=tmp_path/'report.json'
    rc=live_smoke.main(['--pangram','--out',str(out)])
    captured=capsys.readouterr()
    report=json.loads(out.read_text())
    assert rc == 4
    assert report['account_action_required'] == 'PANGRAM_CREDITS'
    assert report['account_status_code'] == 402
    assert 'live_smoke_account_action_required=PANGRAM_CREDITS' in captured.err
