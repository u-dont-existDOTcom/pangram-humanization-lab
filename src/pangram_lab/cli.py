from __future__ import annotations

import argparse, getpass, json, os, shutil, subprocess, sys
from pathlib import Path
from .blogger_discover import add_cli_parsers as add_blogger_cli_parsers, run_cli as run_blogger_cli
from .cache import PangramCache, text_sha256
from .codex_stream import CodexRunner
from .corpus_acquire import add_cli_parsers as add_corpus_cli_parsers, run_cli as run_corpus_cli
from .engine import Engine
from .git_sync import GitSync, GitSyncError
from .idiolect import add_cli_parsers as add_idiolect_cli_parsers, run_cli as run_idiolect_cli
from .legacy_import import import_legacy_tree
from .pangram4 import PangramClient


DEFAULT_PANGRAM_BASE_URL = "https://text.external-api.pangram.com"


def root(): return Path(__file__).resolve().parents[2]


def parser():
    p=argparse.ArgumentParser(prog="pangram-lab")
    sp=p.add_subparsers(dest="cmd",required=True)
    r=sp.add_parser("run"); r.add_argument("ai_file"); r.add_argument("human_file"); r.add_argument("--max-rounds",type=int,default=6); r.add_argument("--max-calls",type=int,default=64); r.add_argument("--no-github",action="store_true")
    d=sp.add_parser("detect-file",help="Measure one exact UTF-8 text file through the cached Pangram API path.")
    d.add_argument("input_file")
    d.add_argument("--expect-sha",required=True,help="Required exact SHA-256 gate for the UTF-8 detector input.")
    d.add_argument("--measurement-key",default="base",help="Stable cache/checkpoint identity for this exact measurement.")
    d.add_argument("--base-url",default=os.environ.get("PANGRAM_BASE_URL",DEFAULT_PANGRAM_BASE_URL),help="Pangram API base URL; defaults to PANGRAM_BASE_URL or the standard async endpoint.")
    d.add_argument("--allow-public-cache",action="store_true",help="Required acknowledgement that the current cache stores the exact input text and may be pushed to this public repository.")
    d.add_argument("--no-github",action="store_true")
    i=sp.add_parser("import-legacy"); i.add_argument("paths",nargs="*")
    g=sp.add_parser("github-ensure"); g.add_argument("--repo-name",default="pangram-humanization-lab")
    s=sp.add_parser("cache-summary")
    add_idiolect_cli_parsers(sp)
    add_corpus_cli_parsers(sp)
    add_blogger_cli_parsers(sp)
    return p


def default_legacy_paths():
    d=Path.home()/"Téléchargements"
    return [d/"pangram-codex-autopilot-v1.1",d/"pangram-experiment-harness-v1",d/"pangram4-owner-calibration-r27",d/"pangram4-terminal-validation-r26"]


def get_key():
    k=os.environ.get("PANGRAM_API_KEY","").strip()
    return k or getpass.getpass("Pangram API key (hidden; never saved): ").strip()


def import_paths(paths):
    cache=PangramCache(root()/"cache")
    reports=[]
    for p in paths:
        rep=import_legacy_tree(Path(p).expanduser(),cache); reports.append(rep)
        print(f"[legacy] {rep['source']}: imported Pangram4 successes={rep['v4_success_imported']}, saw v3={rep['v3_records_seen']}",flush=True)
    (root()/"state").mkdir(exist_ok=True)
    (root()/"state/legacy-import-report.json").write_text(json.dumps(reports,indent=2)+"\n",encoding="utf-8")
    return reports


def detect_file(args, rt: Path) -> dict:
    path=Path(args.input_file).expanduser().resolve(strict=False)
    if not path.is_file():
        raise RuntimeError(f"input file missing: {path}")
    expected=str(args.expect_sha or "").strip().lower()
    if len(expected)!=64 or any(ch not in "0123456789abcdef" for ch in expected):
        raise RuntimeError("--expect-sha must be one lowercase/uppercase 64-character SHA-256 value")
    text=path.read_bytes().decode("utf-8")
    observed=text_sha256(text)
    if observed!=expected:
        raise RuntimeError(f"refusing Pangram API work because exact SHA-256 changed: expected={expected} actual={observed}")
    measurement_key=str(args.measurement_key or "").strip()
    if not measurement_key:
        raise RuntimeError("--measurement-key must not be empty")
    if not bool(getattr(args,"allow_public_cache",False)):
        raise RuntimeError(
            "detect-file uses the repository PangramCache, which stores the exact input text. "
            "This repository is public; pass --allow-public-cache only when the detector input is already public-safe."
        )

    git=GitSync(rt,require_remote=not args.no_github)
    if not args.no_github:
        git.ensure_github()
        git.sync(f"pre-detect-file checkpoint {measurement_key} {observed[:16]}")
    else:
        git.sync(f"pre-detect-file local checkpoint {measurement_key} {observed[:16]}")

    key=get_key()
    if not key:
        raise RuntimeError("No Pangram API key supplied")
    base_url=str(args.base_url or DEFAULT_PANGRAM_BASE_URL).strip().rstrip("/")
    if not base_url.startswith(("http://","https://")):
        raise RuntimeError("--base-url must begin with http:// or https://")
    pangram=PangramClient(key,base_url=base_url,sync=git.sync)
    print("[verify] checking Pangram API authentication without a billable submit",flush=True)
    pangram.probe_auth()

    cache=PangramCache(rt/"cache")
    result=pangram.detect_cached(text,cache,measurement_key)
    git.sync(f"detect-file outcome {measurement_key} {observed[:16]}")
    cache_path=cache.path_for(pangram.model,pangram.expected_version,text,measurement_key)
    record=cache.lookup(pangram.model,pangram.expected_version,text,measurement_key) or {}
    return {
        "status":"success",
        "input_name":path.name,
        "input_sha256":observed,
        "word_count_whitespace":len(text.split()),
        "measurement_key":measurement_key,
        "model":pangram.model,
        "expected_version":pangram.expected_version,
        "cache_status":record.get("status"),
        "cache_path":str(cache_path.relative_to(rt)),
        "result":result,
    }


def main(argv=None):
    a=parser().parse_args(argv); rt=root()
    try:
        if a.cmd in {"idiolect-retention","idiolect-ier"}:
            return run_idiolect_cli(a)
        if a.cmd=="idiolect-corpus-acquire":
            if a.inventory=="state/IDIOLECT-CORPUS-SOURCE-INVENTORY-2026-08-18.json":
                a.inventory="state/IDIOLECT-CORPUS-ACQUISITION-QUEUE-2026-08-18.json"
            return run_corpus_cli(a)
        if a.cmd=="idiolect-blogger-discover":
            return run_blogger_cli(a)
        if a.cmd=="github-ensure":
            # Commit the unpacked source locally first; then create/connect the
            # private GitHub repository and push that exact tree.
            GitSync(rt,require_remote=False).sync("initial harness source")
            gs=GitSync(rt,require_remote=True); gs.ensure_github(a.repo_name); gs.sync("bootstrap repository"); return 0
        if a.cmd=="import-legacy":
            import_paths(a.paths or default_legacy_paths()); GitSync(rt,require_remote=False).sync("import legacy evidence"); return 0
        if a.cmd=="cache-summary":
            files=list((rt/"cache").rglob("*.json")); success=pending=failed=0
            for p in files:
                try: st=json.loads(p.read_text()).get("status")
                except Exception: continue
                success+=st=="success"; pending+=st=="pending"; failed+=st=="failed"
            print(f"cache records={len(files)} success={success} pending={pending} failed={failed}"); return 0
        if a.cmd=="detect-file":
            print(json.dumps(detect_file(a,rt),ensure_ascii=False,indent=2)); return 0
        if a.cmd=="run":
            ai_path=Path(a.ai_file).expanduser(); human_path=Path(a.human_file).expanduser()
            if not ai_path.is_file() or not human_path.is_file():
                raise RuntimeError(f"input file missing: {ai_path if not ai_path.is_file() else human_path}")
            # Import before any new request every run; this is idempotent.
            import_paths(default_legacy_paths())
            git=GitSync(rt,require_remote=not a.no_github)
            if not a.no_github:
                git.ensure_github(); git.sync("pre-run sync and legacy import")
            else: git.sync("pre-run local checkpoint")
            key=get_key();
            if not key: raise RuntimeError("No Pangram API key supplied")
            codex=CodexRunner();
            if not codex.available(): raise RuntimeError("Codex CLI not found")
            pangram=PangramClient(key,sync=git.sync)
            print("[verify] checking Pangram async authentication without a billable submit",flush=True); pangram.probe_auth()
            engine=Engine(rt,codex,pangram,PangramCache(rt/"cache"),git,max_rounds=a.max_rounds,max_calls=a.max_calls)
            out=engine.run(ai_path.read_text(encoding="utf-8"),human_path.read_text(encoding="utf-8"))
            git.sync("run outcome")
            print(json.dumps(out,ensure_ascii=False,indent=2)); return 0
    except (RuntimeError,ValueError,OSError,GitSyncError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr); return 1
    return 0
