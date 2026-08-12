import json, os, stat, textwrap
from pathlib import Path
from pangram_lab.codex_stream import CodexRunner


def test_codex_output_is_streamed_and_key_is_removed(tmp_path,capsys):
    exe=tmp_path/"fake-codex"
    exe.write_text("""#!/usr/bin/env python3
import os,sys,json
print('working line', flush=True)
print('KEY='+str(os.getenv('PANGRAM_API_KEY')), flush=True)
out=sys.argv[sys.argv.index('-o')+1]
open(out,'w').write(json.dumps({'ok':True}))
""")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    os.environ['PANGRAM_API_KEY']='topsecret'
    runner=CodexRunner(binary=str(exe), heartbeat_seconds=0.05)
    out=tmp_path/'o.json'; log=tmp_path/'log.txt'; schema=tmp_path/'s.json'; schema.write_text('{}')
    result=runner.run_json('designer','prompt',schema,out,log)
    shown=capsys.readouterr().out
    assert '[codex:designer] working line' in shown
    assert 'KEY=None' in shown
    assert 'topsecret' not in log.read_text()
    assert result == {'ok':True}


def test_status_stream_surfaces_agent_message_and_command_without_reasoning_text():
    msg = CodexRunner._status_from_jsonl(json.dumps({
        "type": "item.completed",
        "item": {"type": "agent_message", "text": "I found three interacting factors; testing the smallest valid grid next."},
    }))
    assert msg == "agent: I found three interacting factors; testing the smallest valid grid next."

    cmd = CodexRunner._status_from_jsonl(json.dumps({
        "type": "item.started",
        "item": {"type": "command_execution", "command": "python analyze.py --case romance"},
    }))
    assert cmd == "command started: python analyze.py --case romance"

    reasoning = CodexRunner._status_from_jsonl(json.dumps({
        "type": "item.completed",
        "item": {"type": "reasoning", "text": "private reasoning contents should never be printed"},
    }))
    assert reasoning == "reasoning completed"
    assert "private reasoning" not in reasoning


def test_status_stream_surfaces_completed_command_result_compactly():
    status = CodexRunner._status_from_jsonl(json.dumps({
        "type": "item.completed",
        "item": {
            "type": "command_execution",
            "command": "python check.py",
            "aggregated_output": "37 tests passed\n",
            "exit_code": 0,
            "status": "completed",
        },
    }))
    assert status == "command completed exit=0: python check.py → 37 tests passed"
