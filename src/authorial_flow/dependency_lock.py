from __future__ import annotations

from hashlib import sha256
import argparse
import json
from pathlib import Path
import re
from typing import Any


_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def build_hashed_lock_from_pip_report(
    report_path: Path,
    output_path: Path,
    *,
    source_requirements: Path,
    metadata_path: Path | None = None,
) -> dict[str, Any]:
    report=json.loads(Path(report_path).read_text(encoding="utf-8"))
    installs=report.get("install")
    if not isinstance(installs,list) or not installs:
        raise ValueError("pip report contains no install records")

    resolved: dict[str, tuple[str,str]]={}
    for row in installs:
        if not isinstance(row,dict):
            raise ValueError("pip report install record is not an object")
        metadata=row.get("metadata") or {}
        name=_canonical_name(str(metadata.get("name") or "").strip())
        version=str(metadata.get("version") or "").strip()
        hashes=((row.get("download_info") or {}).get("archive_info") or {}).get("hashes") or {}
        digest=str(hashes.get("sha256") or "").lower()
        if not name or not version:
            raise ValueError("pip report install record is missing package name/version")
        if not _HASH_RE.fullmatch(digest):
            raise ValueError(f"pip report package {name}=={version} is missing a valid sha256")
        prior=resolved.get(name)
        current=(version,digest)
        if prior is not None and prior != current:
            raise ValueError(f"pip report contains conflicting records for {name}")
        resolved[name]=current

    source_requirements=Path(source_requirements)
    source_hash=_file_sha256(source_requirements)
    lines=[
        "# Generated before installation from pip --dry-run --report.",
        f"# source-requirements-sha256: {source_hash}",
        "# Every resolved artifact is installed under pip --require-hashes.",
    ]
    for name,(version,digest) in sorted(resolved.items()):
        lines.append(f"{name}=={version} --hash=sha256:{digest}")
    payload="\n".join(lines)+"\n"
    output_path=Path(output_path)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(payload,encoding="utf-8")

    result={
        "format":"authorial-flow-resolved-dependency-lock-v1",
        "source_requirements":str(source_requirements),
        "source_requirements_sha256":source_hash,
        "pip_report_sha256":_file_sha256(Path(report_path)),
        "resolved_lock_sha256":sha256(payload.encode("utf-8")).hexdigest(),
        "package_count":len(resolved),
    }
    if metadata_path is not None:
        metadata_path=Path(metadata_path)
        metadata_path.parent.mkdir(parents=True,exist_ok=True)
        metadata_path.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return result


def lock_is_current(source_requirements: Path, metadata_path: Path, resolved_lock: Path) -> bool:
    source_requirements=Path(source_requirements)
    metadata_path=Path(metadata_path)
    resolved_lock=Path(resolved_lock)
    if not metadata_path.is_file() or not resolved_lock.is_file() or not source_requirements.is_file():
        return False
    try:
        meta=json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return bool(
        meta.get("format")=="authorial-flow-resolved-dependency-lock-v1"
        and meta.get("source_requirements_sha256")==_file_sha256(source_requirements)
        and meta.get("resolved_lock_sha256")==_file_sha256(resolved_lock)
    )


def _main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(prog="python -m authorial_flow.dependency_lock")
    sub=parser.add_subparsers(dest="command",required=True)
    build=sub.add_parser("build")
    build.add_argument("--report",type=Path,required=True)
    build.add_argument("--source",type=Path,required=True)
    build.add_argument("--out",type=Path,required=True)
    build.add_argument("--metadata",type=Path,required=True)
    check=sub.add_parser("check")
    check.add_argument("--source",type=Path,required=True)
    check.add_argument("--lock",type=Path,required=True)
    check.add_argument("--metadata",type=Path,required=True)
    args=parser.parse_args(argv)
    if args.command=="build":
        build_hashed_lock_from_pip_report(
            args.report,args.out,source_requirements=args.source,metadata_path=args.metadata
        )
        return 0
    if args.command=="check":
        return 0 if lock_is_current(args.source,args.metadata,args.lock) else 1
    return 2


if __name__=="__main__":
    raise SystemExit(_main())
