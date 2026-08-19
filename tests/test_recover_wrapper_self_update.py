from pathlib import Path


def test_recovery_wrapper_reexecs_after_self_update() -> None:
    root = Path(__file__).resolve().parents[1]
    script = (root / "scripts" / "pangram_local_romance_recover_resume_safe.sh").read_text(
        encoding="utf-8"
    )

    assert 'self_hash_before="$(git hash-object "$self_path" 2>/dev/null)"' in script
    assert 'self_hash_after="$(git hash-object "$self_path" 2>/dev/null)"' in script
    assert 'PANGRAM_RECOVER_WRAPPER_REEXEC=1 exec bash "$self_path"' in script
    assert '"${PANGRAM_RECOVER_WRAPPER_REEXEC:-0}" != "1"' in script
