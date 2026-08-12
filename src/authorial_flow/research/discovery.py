from __future__ import annotations

import os
import re
import httpx

from .base import SearchHit


_URL_RE=re.compile(r'https?://[^\s<>"\']+')


class DirectURLProvider:
    def __init__(self,text:str):
        seen=[]
        for raw in _URL_RE.findall(text):
            url=raw.rstrip('.,);]}')
            if url not in seen: seen.append(url)
        self.urls=seen

    def search(self,query:str,limit:int)->list[SearchHit]:
        return [SearchHit(title=url,url=url,primary_hint=True) for url in self.urls[:limit]]


class BraveSearchProvider:
    def __init__(self,api_key:str|None=None,client:httpx.Client|None=None):
        self.api_key=(api_key or os.environ.get('BRAVE_SEARCH_API_KEY') or '').strip()
        if not self.api_key:
            raise RuntimeError('BRAVE_SEARCH_API_KEY is unavailable')
        self.client=client or httpx.Client(base_url='https://api.search.brave.com',timeout=30)

    def search(self,query:str,limit:int)->list[SearchHit]:
        response=self.client.get('/res/v1/web/search',params={'q':query,'count':limit},headers={
            'Accept':'application/json','X-Subscription-Token':self.api_key,
        })
        response.raise_for_status()
        rows=((response.json().get('web') or {}).get('results') or [])
        return [SearchHit(title=str(r.get('title') or ''),url=str(r.get('url') or ''),snippet=str(r.get('description') or '')) for r in rows[:limit]]
