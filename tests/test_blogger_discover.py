import json
from pathlib import Path

from pangram_lab import blogger_discover as bd


def atom(entries):
    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<feed xmlns="http://www.w3.org/2005/Atom">']
    for row in entries:
        body.extend(
            [
                '<entry>',
                f'<id>{row["id"]}</id>',
                f'<published>{row["published"]}</published>',
                f'<updated>{row.get("updated", row["published"])}</updated>',
                f'<title>{row["title"]}</title>',
                f'<link rel="alternate" type="text/html" href="{row["url"]}"/>',
                *(f'<category term="{label}"/>' for label in row.get("labels", [])),
                '<content type="html">THIS CONTENT MUST NEVER ENTER DISCOVERY OUTPUT</content>',
                '</entry>',
            ]
        )
    body.append('</feed>')
    return ''.join(body).encode()


def test_root_from_specific_post_becomes_https_blog_root():
    assert bd._root_from_url('http://Example.Blogspot.com/2020/01/post.html?x=1') == (
        'https://example.blogspot.com'
    )


def test_parse_atom_keeps_metadata_not_content():
    body = atom(
        [
            {
                'id': 'tag:blogger.com,1999:blog-1.post-2',
                'published': '2019-01-02T03:04:05Z',
                'title': 'A title',
                'url': 'http://Example.Blogspot.com/2019/01/a-title.html?m=1',
                'labels': ['one', 'two'],
            }
        ]
    )
    posts = bd.parse_atom_posts(body)
    assert len(posts) == 1
    assert posts[0].url == 'https://example.blogspot.com/2019/01/a-title.html'
    assert posts[0].labels == ('one', 'two')
    assert 'CONTENT' not in repr(posts[0])


def test_discover_blog_pages_and_applies_pre_llm_cutoff(monkeypatch):
    pages = {
        1: atom(
            [
                {'id': 'old-1', 'published': '2019-01-01T00:00:00Z', 'title': 'Old one', 'url': 'https://x.blogspot.com/2019/01/old-one.html'},
                {'id': 'new-1', 'published': '2024-01-01T00:00:00Z', 'title': 'New one', 'url': 'https://x.blogspot.com/2024/01/new-one.html'},
            ]
        ),
        3: atom(
            [
                {'id': 'old-2', 'published': '2020-01-01T00:00:00Z', 'title': 'Old two', 'url': 'https://x.blogspot.com/2020/01/old-two.html'},
            ]
        ),
    }

    def fake_fetch(url, timeout=30):
        start = 1 if 'start-index=1' in url else 3
        return pages[start], f'sha-{start}'

    monkeypatch.setattr(bd, 'fetch_atom', fake_fetch)
    result = bd.discover_blog(
        'https://x.blogspot.com/post/path',
        published_before='2022-11-30T00:00:00Z',
        page_size=2,
    )
    assert result['post_count'] == 2
    assert [p['entry_id'] for p in result['posts']] == ['old-1', 'old-2']
    assert len(result['pages']) == 2


def test_discovery_queue_contains_metadata_only(tmp_path, monkeypatch):
    queue = {
        'blogs': [
            {
                'source_id': 'blog-a',
                'blog_url': 'https://a.blogspot.com/',
                'published_before': '2022-11-30T00:00:00Z',
                'provenance': 'natural-owner-confirmed',
                'owner_confirmation': 'confirmed',
            }
        ]
    }
    path = tmp_path / 'queue.json'
    path.write_text(json.dumps(queue), encoding='utf-8')
    monkeypatch.setattr(
        bd,
        'discover_blog',
        lambda *a, **k: {
            'blog_root': 'https://a.blogspot.com',
            'published_before': k['published_before'],
            'pages': [],
            'post_count': 1,
            'posts': [
                {
                    'entry_id': 'post-1',
                    'title': 'Title',
                    'published': '2020-01-01T00:00:00Z',
                    'updated': None,
                    'url': 'https://a.blogspot.com/2020/01/title.html',
                    'labels': [],
                }
            ],
        },
    )
    result = bd.discover_queue(path)
    encoded = json.dumps(result)
    assert result['content_included'] is False
    assert result['errors'] == []
    assert 'post body' not in encoded.lower()
    assert result['results'][0]['provenance'] == 'natural-owner-confirmed'
