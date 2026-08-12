from pathlib import Path
from pangram_lab.cache import PangramCache
from pangram_lab.engine import Engine

class FailingCodex:
    def run_json(self,role,prompt,schema,out,log):
        log.parent.mkdir(parents=True,exist_ok=True); log.write_text('codex exploded')
        raise RuntimeError('codex exploded')
class NoPangram: model='pangram-4'; expected_version='4.0'
class RecordingGit:
    def __init__(self): self.reasons=[]
    def sync(self,r): self.reasons.append(r)

def test_codex_failure_log_is_checkpointed(tmp_path):
    (tmp_path/'prompts').mkdir(); (tmp_path/'schemas').mkdir(); (tmp_path/'prompts/designer.md').write_text('d'); (tmp_path/'schemas/plan.schema.json').write_text('{}')
    g=RecordingGit(); e=Engine(tmp_path,FailingCodex(),NoPangram(),PangramCache(tmp_path/'cache'),g,max_rounds=1)
    import pytest
    with pytest.raises(RuntimeError,match='codex exploded'): e.run('ai','human')
    case=next((tmp_path/'cases').iterdir()); r=case/'r01'
    assert (r/'designer-attempt01.log').read_text()=='codex exploded'
    assert (r/'failure.json').is_file()
    assert any('designer failure' in x for x in g.reasons)
