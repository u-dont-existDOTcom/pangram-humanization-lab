from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path


class CodexError(RuntimeError):
    pass


@dataclass
class CodexRunner:
    model: str = "gpt-5.6-sol"
    reasoning_effort: str = "xhigh"
    binary: str = "codex"
    timeout_seconds: int = 900
    heartbeat_seconds: float = 10.0

    def available(self) -> bool:
        return shutil.which(self.binary) is not None or Path(self.binary).is_file()

    @staticmethod
    def _status_from_jsonl(line: str) -> str | None:
        try:
            ev=json.loads(line)
        except Exception:
            return None
        typ=str(ev.get("type") or "")
        if typ == "thread.started":
            tid=str(ev.get("thread_id") or "")
            return f"thread started{f' ({tid[:12]}…)' if tid else ''}"
        if typ == "turn.started": return "turn started — designing/analyzing"
        if typ in {"item.started","item.updated","item.completed"}:
            item=ev.get("item") or {}
            itype=str(item.get("type") or "item")
            phase=typ.split(".")[-1]
            def compact(value, limit=420):
                text=" ".join(str(value or "").split())
                return text if len(text) <= limit else text[: limit-1].rstrip()+"…"
            if itype == "reasoning":
                # Never surface model chain-of-thought; the user-visible progress
                # signal is only that the reasoning item advanced/completed.
                return f"reasoning {phase}"
            if itype == "agent_message":
                text=compact(item.get("text"))
                return f"agent: {text}" if text else f"response {phase}"
            if itype == "command_execution":
                command=compact(item.get("command"),240)
                if phase == "completed":
                    exit_code=item.get("exit_code")
                    output=compact(item.get("aggregated_output"),260)
                    suffix=f" exit={exit_code}" if exit_code is not None else ""
                    result=f": {command}" if command else ""
                    if output: result += f" → {output}"
                    return f"command completed{suffix}{result}"
                return f"command {phase}: {command}" if command else f"command {phase}"
            if itype == "mcp_tool_call":
                name=compact(item.get("tool") or item.get("name"),200)
                return f"tool call {phase}: {name}" if name else f"tool call {phase}"
            labels={"file_change":"file change","web_search":"web search","error":"warning/error item"}
            return f"{labels.get(itype,itype)} {phase}"
        if typ == "turn.completed":
            usage=ev.get("usage") or {}
            total=usage.get("total_tokens")
            return f"turn completed{f' — {total} tokens' if total is not None else ''}"
        if typ in {"turn.failed","error","thread.error"}:
            return f"{typ}: {ev.get('message') or ev.get('error') or 'error'}"
        return typ or None

    def run_json(self, role: str, prompt: str, schema_path: Path, out_path: Path, log_path: Path) -> dict:
        out_path.parent.mkdir(parents=True, exist_ok=True); log_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [self.binary,"exec","--json","--ephemeral","--skip-git-repo-check","--sandbox","read-only","-m",self.model,
               "-c",'approval_policy="never"',"-c",'web_search="disabled"',"-c",f'model_reasoning_effort="{self.reasoning_effort}"',
               "--output-schema",str(schema_path.resolve()),"-o",str(out_path.resolve()),prompt]
        env = os.environ.copy(); env.pop("PANGRAM_API_KEY", None)
        print(f"[codex:{role}] START model={self.model} reasoning={self.reasoning_effort}", flush=True)
        print(f"[codex:{role}] live output follows; full transcript → {log_path}", flush=True)
        started = time.monotonic()
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
        except OSError as exc:
            raise CodexError(f"cannot start Codex: {exc}") from exc
        q: queue.Queue[tuple[str,str|None]] = queue.Queue()
        def pump(name, stream):
            try:
                for line in iter(stream.readline, ""):
                    q.put((name,line.rstrip("\n")))
            finally:
                q.put((name,None))
        threads=[threading.Thread(target=pump,args=("stdout",proc.stdout),daemon=True),threading.Thread(target=pump,args=("stderr",proc.stderr),daemon=True)]
        for t in threads:t.start()
        done=set(); lines=[]; last_output=time.monotonic()
        while len(done)<2:
            if time.monotonic()-started > self.timeout_seconds:
                proc.kill(); raise CodexError(f"{role} Codex exceeded {self.timeout_seconds}s")
            try:
                name,line=q.get(timeout=min(0.5,max(0.05,self.heartbeat_seconds)))
            except queue.Empty:
                if time.monotonic()-last_output >= self.heartbeat_seconds:
                    print(f"[codex:{role}] … still working ({int(time.monotonic()-started)}s)", flush=True); last_output=time.monotonic()
                continue
            if line is None:
                done.add(name); continue
            lines.append(f"[{name}] {line}")
            if name == "stdout":
                status=self._status_from_jsonl(line)
                if status:
                    print(f"[codex:{role}] {status}", flush=True)
                else:
                    print(f"[codex:{role}] {line}", flush=True)
            else:
                # stderr carries CLI/runtime status; stream it without the Pangram
                # credential, which was removed from the child environment.
                print(f"[codex:{role}] {line}", flush=True)
            last_output=time.monotonic()
        rc=proc.wait()
        log_path.write_text(f"role={role}\nreturncode={rc}\n"+"\n".join(lines)+"\n",encoding="utf-8")
        if rc != 0:
            raise CodexError(f"{role} Codex returned {rc}; see {log_path}")
        if not out_path.is_file():
            raise CodexError(f"{role} Codex produced no structured output at {out_path}")
        try:
            obj=json.loads(out_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CodexError(f"{role} Codex structured output is invalid JSON: {exc}") from exc
        print(f"[codex:{role}] DONE ({int(time.monotonic()-started)}s)", flush=True)
        return obj
