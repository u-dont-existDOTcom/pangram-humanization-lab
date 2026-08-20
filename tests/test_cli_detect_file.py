from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

import pytest

from pangram_lab import cli
from pangram_lab.cache import text_sha256


class FakeGit:
    instances = []

    def __init__(self, root: Path, *, require_remote: bool = True):
        self.root = Path(root)
        self.require_remote = require_remote
        self.reasons = []
        self.ensure_called = False
        type(self).instances.append(self)

    def ensure_github(self, repo_name: str = "pangram-humanization-lab") -> None:
        self.ensure_called = True

    def sync(self, reason: str) -> None:
        self.reasons.append(reason)


class FakeCache:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.record = {"status": "success"}

    def path_for(self, model: str, version: str, text: str, measurement_key: str = "base") -> Path:
        return self.root / model / version / text_sha256(text) / f"{measurement_key}.json"

    def lookup(self, model: str, version: str, text: str, measurement_key: str = "base"):
        return self.record


class FakeClient:
    instances = []

    def __init__(self, api_key: str, *, base_url: str, sync):
        assert api_key == "secret"
        self.base_url = base_url
        self.sync = sync
        self.model = "pangram-4"
        self.expected_version = "4.0"
        self.probed = False
        self.detected = None
        type(self).instances.append(self)

    def probe_auth(self) -> None:
        self.probed = True

    def detect_cached(self, text: str, cache, measurement_key: str = "base"):
        self.detected = (text, measurement_key)
        self.sync(f"fake checkpoint {measurement_key}")
        return {
            "stage": "STAGE_SUCCESS",
            "version": "4.0",
            "fraction_human": 0.95,
            "fraction_ai": 0.05,
            "fraction_ai_assisted": 0.0,
        }


def args_for(path: Path, digest: str, **overrides):
    values = {
        "input_file": str(path),
        "expect_sha": digest,
        "measurement_key": "romance-pass2",
        "base_url": "https://pangram.example.test/",
        "no_github": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_detect_file_is_hash_gated_and_uses_cached_client(tmp_path, monkeypatch):
    text = "A reader-visible Pangram boundary.\n"
    path = tmp_path / "candidate.txt"
    path.write_text(text, encoding="utf-8")
    digest = text_sha256(text)

    FakeGit.instances.clear()
    FakeClient.instances.clear()
    monkeypatch.setattr(cli, "GitSync", FakeGit)
    monkeypatch.setattr(cli, "PangramCache", FakeCache)
    monkeypatch.setattr(cli, "PangramClient", FakeClient)
    monkeypatch.setattr(cli, "get_key", lambda: "secret")

    result = cli.detect_file(args_for(path, digest), tmp_path)

    assert result["status"] == "success"
    assert result["input_sha256"] == digest
    assert result["measurement_key"] == "romance-pass2"
    assert result["model"] == "pangram-4"
    assert result["expected_version"] == "4.0"
    assert result["cache_status"] == "success"
    assert result["result"]["fraction_human"] == 0.95

    git = FakeGit.instances[-1]
    client = FakeClient.instances[-1]
    assert git.ensure_called is True
    assert git.require_remote is True
    assert len(git.reasons) >= 3
    assert client.base_url == "https://pangram.example.test"
    assert client.probed is True
    assert client.detected == (text, "romance-pass2")


def test_detect_file_rejects_hash_mismatch_before_credentials(tmp_path, monkeypatch):
    path = tmp_path / "candidate.txt"
    path.write_text("exact text\n", encoding="utf-8")
    called = {"key": False}

    def unexpected_key():
        called["key"] = True
        raise AssertionError("credential access should not happen after a hash mismatch")

    monkeypatch.setattr(cli, "get_key", unexpected_key)

    with pytest.raises(RuntimeError, match="exact SHA-256 changed"):
        cli.detect_file(args_for(path, "0" * 64), tmp_path)

    assert called["key"] is False


def test_detect_file_rejects_invalid_base_url_before_client(tmp_path, monkeypatch):
    text = "exact text\n"
    path = tmp_path / "candidate.txt"
    path.write_text(text, encoding="utf-8")

    monkeypatch.setattr(cli, "GitSync", FakeGit)
    monkeypatch.setattr(cli, "get_key", lambda: "secret")
    monkeypatch.setattr(cli, "PangramCache", FakeCache)

    with pytest.raises(RuntimeError, match="--base-url must begin"):
        cli.detect_file(args_for(path, text_sha256(text), base_url="pangram.local"), tmp_path)
