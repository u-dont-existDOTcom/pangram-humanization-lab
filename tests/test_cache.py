import json
from pathlib import Path
from pangram_lab.cache import PangramCache, text_sha256


def test_success_cache_is_reused_by_model_version_hash(tmp_path):
    c = PangramCache(tmp_path)
    text = "hello"
    c.save_success("pangram-4", "4.0", text, "base", "t1", {"stage":"STAGE_SUCCESS","version":"4.0","headline":"Human Written","prediction_short":"Human","fraction_ai":0.0,"fraction_ai_assisted":0.0,"fraction_human":1.0,"text":text})
    rec = c.lookup("pangram-4", "4.0", text, "base")
    assert rec["status"] == "success"
    assert rec["text_sha256"] == text_sha256(text)
    assert rec["task_id"] == "t1"


def test_pending_task_survives_restart(tmp_path):
    text = "same"
    PangramCache(tmp_path).save_pending("pangram-4", "4.0", text, "base", "task-7")
    rec = PangramCache(tmp_path).lookup("pangram-4", "4.0", text, "base")
    assert rec["status"] == "pending"
    assert rec["task_id"] == "task-7"


def test_repeat_identity_is_separate_from_base(tmp_path):
    text = "same text"
    c = PangramCache(tmp_path)
    c.save_success("pangram-4", "4.0", text, "base", "tb", {"stage":"STAGE_SUCCESS","version":"4.0","headline":"Human Written","prediction_short":"Human","fraction_ai":0,"fraction_ai_assisted":0,"fraction_human":1,"text":text})
    assert c.lookup("pangram-4", "4.0", text, "r01:P1:r2") is None
    assert c.lookup("pangram-4", "4.0", text, "base") is not None
