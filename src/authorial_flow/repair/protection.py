from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
import subprocess


def file_hash(path:Path)->str:
    return sha256(path.read_bytes()).hexdigest() if path.is_file() else '<missing>'


@dataclass(frozen=True)
class ProtectionReport:
    pass_: bool
    mutated: tuple[str,...]=()
    source_hardcoding_hits: tuple[str,...]=()
    diff_text: str=''


@dataclass(frozen=True)
class ProtectedSnapshot:
    paths: tuple[str,...]
    hashes: dict[str,str]
    prefixes: tuple[str,...]=()

    @classmethod
    def capture(cls,root:Path,protected_paths:list[str]|tuple[str,...])->'ProtectedSnapshot':
        root=Path(root)
        files:set[str]=set()
        prefixes:list[str]=[]
        for raw in protected_paths:
            rel=str(raw).replace('\\','/').strip()
            candidate=root/rel.rstrip('/')
            if rel.endswith('/') or candidate.is_dir():
                prefix=rel.rstrip('/')+'/'
                prefixes.append(prefix)
                if candidate.is_dir():
                    for path in candidate.rglob('*'):
                        if path.is_file():
                            files.add(path.relative_to(root).as_posix())
            else:
                files.add(rel)
        paths=tuple(sorted(files))
        return cls(paths,{rel:file_hash(root/rel) for rel in paths},tuple(sorted(set(prefixes))))

    def validate(self,root:Path)->ProtectionReport:
        root=Path(root)
        mutated={rel for rel in self.paths if file_hash(root/rel)!=self.hashes[rel]}
        known=set(self.paths)
        for prefix in self.prefixes:
            directory=root/prefix.rstrip('/')
            if directory.is_dir():
                for path in directory.rglob('*'):
                    if path.is_file():
                        rel=path.relative_to(root).as_posix()
                        if rel not in known:
                            mutated.add(rel)
        ordered=tuple(sorted(mutated))
        return ProtectionReport(not ordered,ordered)


_EXCLUDED_PREFIXES=('project/','policy/','.state/','docs/','supervisor-evidence/')
_PRODUCTION_SUFFIXES={'.py','.md','.txt','.json','.sh','.toml'}


def _added_guarded_text(diff:str)->str:
    current=''
    added=[]
    for line in diff.splitlines():
        if line.startswith('+++ b/'):
            current=line[6:]
            continue
        if not line.startswith('+') or line.startswith('+++'):
            continue
        if not current or current.startswith(_EXCLUDED_PREFIXES):
            continue
        if Path(current).suffix.lower() not in _PRODUCTION_SUFFIXES:
            continue
        added.append(line[1:])
    return '\n'.join(added)


def _source_hardcoding_hits(added:str,source_texts:list[str],min_span:int=70)->tuple[str,...]:
    normalized_added=re.sub(r'\s+',' ',added)
    hits=[]
    for source in source_texts:
        normalized=re.sub(r'\s+',' ',source).strip()
        if len(normalized)<min_span:
            continue
        # Sliding spans make the guard robust to surrounding code syntax while requiring a long,
        # source-specific literal. This is a canary, not a general similarity detector.
        for start in range(0,max(1,len(normalized)-min_span+1),20):
            span=normalized[start:start+min_span]
            if len(span)>=min_span and span in normalized_added:
                hits.append(span)
                break
    return tuple(hits)


def validate_candidate_diff(repo:Path,base_commit:str,source_texts:list[str],
                            protected_snapshot:ProtectedSnapshot|None=None)->ProtectionReport:
    repo=Path(repo)
    p=subprocess.run(['git','diff','--binary',base_commit,'--'],cwd=repo,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    diff=p.stdout
    mutated=()
    if protected_snapshot is not None:
        mutated=protected_snapshot.validate(repo).mutated
    hits=_source_hardcoding_hits(_added_guarded_text(diff),source_texts)
    return ProtectionReport(not mutated and not hits,mutated,hits,diff)
