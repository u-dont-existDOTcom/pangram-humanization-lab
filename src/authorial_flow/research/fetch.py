from __future__ import annotations

from hashlib import sha256
import time
import httpx

from .base import RetrievedSource
from .evidence import AccessLevel


class HTTPFetcher:
    def __init__(self,client:httpx.Client|None=None,max_bytes:int=2_000_000):
        self.client=client or httpx.Client(follow_redirects=True,timeout=30)
        self.max_bytes=max_bytes

    def fetch(self,url:str)->RetrievedSource:
        response=self.client.get(url)
        response.raise_for_status()
        raw=response.content[:self.max_bytes]
        mime=str(response.headers.get('content-type') or '').split(';',1)[0].lower()
        text=raw.decode(response.encoding or 'utf-8',errors='replace')
        limitation=''
        if 'text/html' in mime and '<script' in text.lower() and len(re.sub(r'<[^>]+>',' ',text).strip()) < 200:
            limitation='possibly JS-rendered; v1 does not execute JavaScript'
        return RetrievedSource(
            url=url,final_url=str(response.url),mime_type=mime,body=text,
            body_sha256=sha256(raw).hexdigest(),retrieved_at=time.time(),
            access_level=AccessLevel.FULL_TEXT,headers={str(k):str(v) for k,v in response.headers.items()},
            access_limitation=limitation,
        )

import re
