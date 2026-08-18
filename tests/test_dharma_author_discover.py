from pangram_lab import dharma_author_discover as da


def test_bold_speaker_scanner_keeps_only_person_like_labels():
    html = """
    <div>
      <b>Joel Rosenblum:</b>text
      <strong>Greg Goode</strong>text
      <b>NOT A PERSON HEADING</b>
      <b>Interesting</b>
    </div>
    """
    assert da._speaker_labels(html) == ["Joel Rosenblum", "Greg Goode"]


def test_atom_scan_returns_only_target_posts_and_explicit_labels():
    body = b'''<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>tag:blogger.com,1999:blog-1.post-1</id>
        <title>Thread with Joel</title>
        <published>2013-01-01T00:00:00Z</published>
        <link rel="alternate" href="http://example.blogspot.com/2013/01/thread.html"/>
        <content type="html">&lt;div&gt;&lt;b&gt;Joel Rosenblum:&lt;/b&gt;One.&lt;b&gt;Greg Goode:&lt;/b&gt;Two.&lt;/div&gt;</content>
      </entry>
      <entry>
        <id>tag:blogger.com,1999:blog-1.post-2</id>
        <title>Thread without Joel</title>
        <published>2013-01-02T00:00:00Z</published>
        <link rel="alternate" href="http://example.blogspot.com/2013/01/no-joel.html"/>
        <content type="html">&lt;div&gt;&lt;b&gt;Greg Goode:&lt;/b&gt;Two.&lt;/div&gt;</content>
      </entry>
    </feed>'''
    rows, next_url = da.scan_atom_page(body, target_speaker="Joel Rosenblum")
    assert next_url is None
    assert len(rows) == 1
    row = rows[0]
    assert row["title"] == "Thread with Joel"
    assert row["url"] == "https://example.blogspot.com/2013/01/thread.html"
    assert row["target_label_count"] == 1
    assert row["explicit_speaker_labels"] == ["Joel Rosenblum", "Greg Goode"]


def test_discovery_counts_control_speakers_by_independent_target_thread(monkeypatch):
    pages = [
        b'''<feed xmlns="http://www.w3.org/2005/Atom">
          <link rel="next" href="http://example.blogspot.com/feeds/posts/default?start-index=2"/>
          <entry><id>1</id><title>A</title><published>2013-01-01T00:00:00Z</published>
          <link rel="alternate" href="http://example.blogspot.com/a.html"/>
          <content type="html">&lt;b&gt;Joel Rosenblum:&lt;/b&gt;x&lt;b&gt;Greg Goode:&lt;/b&gt;y&lt;b&gt;Greg Goode:&lt;/b&gt;z</content></entry>
        </feed>''',
        b'''<feed xmlns="http://www.w3.org/2005/Atom">
          <entry><id>2</id><title>B</title><published>2013-01-02T00:00:00Z</published>
          <link rel="alternate" href="http://example.blogspot.com/b.html"/>
          <content type="html">&lt;b&gt;Joel Rosenblum:&lt;/b&gt;x&lt;b&gt;Greg Goode:&lt;/b&gt;y&lt;b&gt;John Ahn:&lt;/b&gt;q</content></entry>
        </feed>''',
    ]

    def fake_fetch(url, timeout=30):
        body = pages.pop(0)
        return body, "sha"

    monkeypatch.setattr(da, "fetch_atom", fake_fetch)
    result = da.discover_dharma_authors("https://example.blogspot.com/")
    assert result["target_post_count"] == 2
    candidates = {row["speaker"]: row for row in result["control_speaker_candidates"]}
    assert candidates["Greg Goode"]["thread_count"] == 2
    assert candidates["Greg Goode"]["marker_count"] == 3
    assert candidates["John Ahn"]["thread_count"] == 1
