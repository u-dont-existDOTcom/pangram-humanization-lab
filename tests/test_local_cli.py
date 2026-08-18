from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from pangram_lab import local_cli


def test_parse_expected_sha_requires_explicit_valid_mapping() -> None:
    digest = "a" * 64
    assert local_cli._parse_expected_sha([f"part.txt={digest}"]) == {"part.txt": digest}
    assert local_cli._parse_expected_sha([]) is None

    with pytest.raises(RuntimeError, match="PATH_OR_NAME=SHA256"):
        local_cli._parse_expected_sha(["part.txt"])
    with pytest.raises(RuntimeError, match="invalid --expect-sha"):
        local_cli._parse_expected_sha(["part.txt=not-a-digest"])


def test_output_root_must_remain_inside_repository(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    assert local_cli._resolve_output_root(repo, Path("state/gui-runs")) == (
        repo / "state" / "gui-runs"
    ).resolve()
    with pytest.raises(RuntimeError, match="inside the repository"):
        local_cli._resolve_output_root(repo, tmp_path / "outside")
    with pytest.raises(RuntimeError, match="cannot be the repository root"):
        local_cli._resolve_output_root(repo, repo)


def test_manifest_validation_fails_closed_when_exact_boundary_moves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = {
        "schema_version": 1,
        "reader_visible_sha256": local_cli.CURRENT_ROMANCE_READER_SHA256,
        "total_words": local_cli.CURRENT_ROMANCE_TOTAL_WORDS,
        "part1_sha256": local_cli.CURRENT_ROMANCE_PARTS[0]["sha256"],
        "part1_words": local_cli.CURRENT_ROMANCE_PARTS[0]["words"],
        "part2_sha256": local_cli.CURRENT_ROMANCE_PARTS[1]["sha256"],
        "part2_words": local_cli.CURRENT_ROMANCE_PARTS[1]["words"],
    }
    local_cli._validate_manifest(manifest)

    manifest["part2_words"] = int(manifest["part2_words"]) + 1
    with pytest.raises(RuntimeError, match="no longer matches"):
        local_cli._validate_manifest(manifest)


def test_current_romance_materialization_uses_live_commit_and_exact_blob_gates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    part1 = "one two three\n".encode()
    part2 = "four five\n".encode()
    digest1 = hashlib.sha256(part1).hexdigest()
    digest2 = hashlib.sha256(part2).hexdigest()
    reader_digest = "c" * 64
    parts = (
        {
            "number": 1,
            "name": "pangram-part-1.txt",
            "source_path": "work/pangram-part-1.txt",
            "sha256": digest1,
            "words": 3,
        },
        {
            "number": 2,
            "name": "pangram-part-2.txt",
            "source_path": "work/pangram-part-2.txt",
            "sha256": digest2,
            "words": 2,
        },
    )
    manifest = {
        "schema_version": 1,
        "reader_visible_sha256": reader_digest,
        "total_words": 5,
        "part1_sha256": digest1,
        "part1_words": 3,
        "part2_sha256": digest2,
        "part2_words": 2,
    }
    manifest_bytes = (json.dumps(manifest) + "\n").encode()
    commit = "d" * 40

    monkeypatch.setattr(local_cli, "CURRENT_ROMANCE_PARTS", parts)
    monkeypatch.setattr(local_cli, "CURRENT_ROMANCE_READER_SHA256", reader_digest)
    monkeypatch.setattr(local_cli, "CURRENT_ROMANCE_TOTAL_WORDS", 5)
    monkeypatch.setattr(local_cli, "CURRENT_ROMANCE_MANIFEST_PATH", "work/manifest.json")
    monkeypatch.setattr(local_cli, "_fetch_current_romance_commit", lambda root, no_fetch: commit)

    blobs = {
        "work/manifest.json": manifest_bytes,
        "work/pangram-part-1.txt": part1,
        "work/pangram-part-2.txt": part2,
    }
    monkeypatch.setattr(
        local_cli,
        "_read_git_file",
        lambda root, selected_commit, path: blobs[path],
    )
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path / "home"))

    prepared = local_cli.materialize_current_romance_inputs(tmp_path / "repo", no_fetch=False)

    assert [path.read_bytes() for path in prepared.paths] == [part1, part2]
    assert prepared.expected_sha256 == {
        str(prepared.paths[0]): digest1,
        str(prepared.paths[1]): digest2,
    }
    assert prepared.source_receipt is not None
    assert prepared.source_receipt["source_commit"] == commit
    assert prepared.source_receipt["reader_visible_sha256"] == reader_digest
    source = prepared.source_metadata[str(prepared.paths[0])]
    assert source["source_commit"] == commit
    assert source["source_path"] == "work/pangram-part-1.txt"


def test_current_romance_materialization_rejects_blob_hash_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = {
        "schema_version": 1,
        "reader_visible_sha256": local_cli.CURRENT_ROMANCE_READER_SHA256,
        "total_words": local_cli.CURRENT_ROMANCE_TOTAL_WORDS,
        "part1_sha256": local_cli.CURRENT_ROMANCE_PARTS[0]["sha256"],
        "part1_words": local_cli.CURRENT_ROMANCE_PARTS[0]["words"],
        "part2_sha256": local_cli.CURRENT_ROMANCE_PARTS[1]["sha256"],
        "part2_words": local_cli.CURRENT_ROMANCE_PARTS[1]["words"],
    }
    monkeypatch.setattr(local_cli, "_fetch_current_romance_commit", lambda root, no_fetch: "d" * 40)

    def read(root: Path, commit: str, path: str) -> bytes:
        if path == local_cli.CURRENT_ROMANCE_MANIFEST_PATH:
            return json.dumps(manifest).encode()
        return b"wrong bytes\n"

    monkeypatch.setattr(local_cli, "_read_git_file", read)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path / "home"))

    with pytest.raises(RuntimeError, match="failed exact byte SHA-256 gate"):
        local_cli.materialize_current_romance_inputs(tmp_path / "repo", no_fetch=False)


def test_git_evidence_preflight_syncs_existing_exact_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    class FakeGitSync:
        def __init__(self, root: Path, *, require_remote: bool) -> None:
            calls.append(("init", (root, require_remote)))

        def sync_paths(self, paths: object, reason: str) -> None:
            calls.append(("sync_paths", (tuple(paths), reason)))

        def ensure_remote_durable(self, reason: str) -> None:
            calls.append(("push", reason))

    monkeypatch.setattr(local_cli, "GitSync", FakeGitSync)
    repo = tmp_path / "repo"
    output = repo / "state" / "gui-runs"
    repo.mkdir()
    digest = "a" * 64
    existing = output / "pangram-4" / digest
    existing.mkdir(parents=True)

    durability = local_cli.GitEvidenceDurability(repo, output)
    durability.preflight({Path("part.txt"): digest})

    assert calls[1][0] == "sync_paths"
    paths, reason = calls[1][1]
    assert paths == (existing,)
    assert "before browser work" in reason


def test_environment_only_status_never_requires_git_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sentinel_config = object()
    monkeypatch.setattr(local_cli, "_config", lambda args: sentinel_config)
    monkeypatch.setattr(
        local_cli,
        "environment_status",
        lambda config: {"playwright_available": True, "headed": True},
    )
    monkeypatch.setattr(
        local_cli,
        "repository_root",
        lambda: (_ for _ in ()).throw(AssertionError("Git must not be consulted")),
    )

    assert local_cli.main(["status", "--environment-only"]) == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["environment"]["playwright_available"] is True
    assert receipt["authentication"]["status"] == "not_checked"
