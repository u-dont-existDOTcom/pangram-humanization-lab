import json
import httpx
import pytest
from authorial_flow.models.pangram import PangramClient


def test_async_api_uses_x_api_key_and_documented_submit_payload():
    calls = []
    payloads = []
    headers = []
    def handler(req: httpx.Request):
        calls.append((req.method, req.url.path))
        headers.append(req.headers)
        if req.url.path == "/task/00000000-0000-0000-0000-000000000000":
            return httpx.Response(404, request=req)
        if req.url.path == "/task" and req.method == "POST":
            payloads.append(json.loads(req.read().decode()))
            return httpx.Response(200, json={"task_id": "t1"}, request=req)
        return httpx.Response(200, json={"stage": "STAGE_SUCCESS", "version": "4.0", "prediction_short": "Human", "fraction_ai": 0, "fraction_ai_assisted": 0, "windows": []}, request=req)
    client = PangramClient("k", httpx.Client(transport=httpx.MockTransport(handler), base_url="https://text.external-api.pangram.com"))
    client.ensure_access()
    task = client.submit("hello", "abc")
    result = client.poll(task.task_id)
    assert result.is_human is True
    assert calls.count(("POST", "/task")) == 1
    assert payloads == [{"text":"hello","public_dashboard_link":False}]
    assert all(h.get("x-api-key") == "k" for h in headers)
    assert all("authorization" not in h for h in headers)


def test_access_probe_accepts_authenticated_not_found_or_forbidden_without_spending_task():
    for status in (403,404):
        calls=[]
        def handler(req, status=status):
            calls.append((req.method,req.url.path))
            return httpx.Response(status,request=req)
        client=PangramClient("k",httpx.Client(transport=httpx.MockTransport(handler),base_url="https://text.external-api.pangram.com"))
        client.ensure_access()
        assert calls == [("GET","/task/00000000-0000-0000-0000-000000000000")]


def test_access_probe_rejects_invalid_key():
    def handler(req):
        return httpx.Response(401,request=req)
    client=PangramClient("k",httpx.Client(transport=httpx.MockTransport(handler),base_url="https://text.external-api.pangram.com"))
    with pytest.raises(httpx.HTTPStatusError):
        client.ensure_access()


def test_resume_polls_existing_task_without_resubmission():
    calls=[]
    def handler(req):
        calls.append((req.method, req.url.path))
        if req.url.path.startswith("/task/"):
            return httpx.Response(200, json={"stage":"STAGE_SUCCESS","version":"4.0","prediction_short":"Human","fraction_ai":0,"fraction_ai_assisted":0,"windows":[]},request=req)
        raise AssertionError(f"unexpected {req.method} {req.url.path}")
    client=PangramClient("k", httpx.Client(transport=httpx.MockTransport(handler),base_url="https://text.external-api.pangram.com"))
    result=client.evaluate("hello","abc",pending={client.request_identity("abc"):"existing"})
    assert result.is_human
    assert all(method != "POST" for method,_ in calls)


def test_ai_window_prevents_human_acceptance():
    result=PangramClient.parse_result({"stage":"STAGE_SUCCESS","version":"4.0","prediction_short":"Human","fraction_ai":0,"fraction_ai_assisted":0,"windows":[{"prediction_short":"AI"}]})
    assert result.is_human is False


def test_non_v4_result_never_counts_as_pangram4_human():
    result=PangramClient.parse_result({"stage":"STAGE_SUCCESS","version":"3.3","prediction_short":"Human","fraction_ai":0,"fraction_ai_assisted":0,"windows":[]})
    assert result.is_human is False
