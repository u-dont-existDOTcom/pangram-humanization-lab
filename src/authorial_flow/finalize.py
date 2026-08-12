from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import time
import zipfile

from .config import RuntimeConfig


def _sha(path: Path) -> str:
    h=sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def _copy_checkpoint_consistently(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True,exist_ok=True)
    if not source.exists():
        return
    try:
        src=sqlite3.connect(f"file:{source}?mode=ro",uri=True)
        dst=sqlite3.connect(target)
        with dst:
            src.backup(dst)
        src.close(); dst.close()
    except sqlite3.Error:
        shutil.copy2(source,target)


def build_evidence_package(config: RuntimeConfig, *, reason: str) -> Path:
    if reason not in {'final','bounded-failure','manual'}:
        raise ValueError('unsupported package reason')
    config.state_dir.mkdir(parents=True,exist_ok=True)
    evidence_dir=config.state_dir/'evidence'
    evidence_dir.mkdir(parents=True,exist_ok=True)
    stamp=time.strftime('%Y%m%d-%H%M%S',time.gmtime())
    out=evidence_dir/f"AUTHORIAL-FLOW-EVIDENCE-{reason}-{stamp}.zip"

    with tempfile.TemporaryDirectory(prefix='authorial-flow-evidence-') as td:
        stage=Path(td)/'stage'; stage.mkdir()
        for dirname in ('policy','project'):
            src=config.root/dirname
            if src.is_dir():
                shutil.copytree(src,stage/dirname,symlinks=False)

        state_dst=stage/'.state'; state_dst.mkdir(exist_ok=True)
        if config.event_path.exists():
            shutil.copy2(config.event_path,state_dst/'events.jsonl')
        _copy_checkpoint_consistently(config.checkpoint_db,state_dst/'checkpoints.sqlite')

        # Artifacts are content-addressed machine evidence. Copy them, but never runtime venv/cache.
        if config.artifact_dir.is_dir():
            shutil.copytree(config.artifact_dir,state_dst/'artifacts')
        for dirname in ('learning','final','dependencies'):
            src=config.state_dir/dirname
            if src.is_dir():
                shutil.copytree(src,state_dst/dirname)
        for p in config.state_dir.iterdir() if config.state_dir.exists() else ():
            if p.name in {'artifacts','learning','final','dependencies','events.jsonl','checkpoints.sqlite'}:
                continue
            if p.is_file() and not p.name.endswith(('-wal','-shm')):
                shutil.copy2(p,state_dst/p.name)

        meta={
            'format':'authorial-flow-evidence-v1',
            'reason':reason,
            'built_utc':time.time(),
        }
        (stage/'PACKAGE.json').write_text(json.dumps(meta,sort_keys=True,indent=2)+'\n')

        files=[p for p in sorted(stage.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt']
        sums=''.join(f"{_sha(p)}  {p.relative_to(stage).as_posix()}\n" for p in files)
        (stage/'SHA256SUMS.txt').write_text(sums)

        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for p in sorted(stage.rglob('*')):
                if p.is_file():
                    z.write(p,p.relative_to(stage).as_posix())
    return out
