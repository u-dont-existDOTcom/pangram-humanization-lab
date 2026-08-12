from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from authorial_flow.artifacts import ArtifactStore
from authorial_flow.config import RuntimeConfig
from authorial_flow.models.common import ModelResult
from authorial_flow.runtime import RuntimeServices, build_runtime_dependencies, seed_initial_state


class RoleAdapter:
    def __init__(self, provider: str, responses: dict[str, object]):
        self.provider = provider
        self.responses = responses
        self.calls = []

    def call(self, call, runner, store):
        self.calls.append(call)
        response = self.responses[call.role]
        if callable(response):
            response = response(call)
        text = response if isinstance(response, str) else json.dumps(response)
        return ModelResult(
            provider=self.provider,
            role=call.role,
            request_id=call.request_id or f"{self.provider}-{call.role}",
            model=f"fake-{self.provider}",
            cli_version="fake",
            parsed=response,
            text=text,
            stdout_ref="",
            stderr_ref="",
        )


@dataclass
class HumanResult:
    stage: str = "STAGE_SUCCESS"
    version: str = "4.0"
    prediction_short: str = "Human"
    fraction_ai: float = 0.0
    fraction_ai_assisted: float = 0.0
    windows: tuple = ()
    raw: dict = None
    is_human: bool = True


class FakePangram:
    def __init__(self):
        self.calls = []

    def evaluate(self, text, candidate_hash, pending=None):
        self.calls.append((text, candidate_hash, pending))
        return HumanResult(raw={"stage": "STAGE_SUCCESS", "version": "4.0", "prediction_short": "Human"})


def _fake_services(tmp_path: Path):
    representation = {
        "section_job": "follow the free-will question until the actual point of uncertainty",
        "semantic_sanity": {
            "status": "PASS", "defect_types": [], "research_trigger": False,
            "recommended_escalation": "BASIC", "owner_question": "",
        },
        "units": [
            {"id": "u001", "text": "Conditioned choice raises a live agency question", "reason": "conceptual content"},
            {"id": "u002", "text": "The writer is uncertain about a chooser outside conditions", "reason": "stopping pressure"},
        ],
    }
    codex = RoleAdapter("codex", {
        "representation": representation,
        "entry_edge": {"verdict": "PASS", "confidence": 0.92, "failure_type": "none", "reason": "", "challenge": ""},
        "full_edge": {"verdict": "PASS", "confidence": 0.91, "failure_type": "none", "reason": "", "challenge": ""},
        "fidelity_guard": {"verdict": "PASS", "confidence": 0.94, "failure_type": "none", "reason": "", "covered_unit_ids": ["u001"]},
        "cold_audit": {"defects": [], "semantic_sanity": True, "curious_reader_chain": True, "stopping_point_ok": True, "fidelity_ok": True},
    })
    claude = RoleAdapter("claude", {
        "writer": "If my choices arise from conditions too, what exactly would a chooser outside those conditions even be doing?",
        "pressure_reader": {"state": "NATURAL_STOP", "confidence": 0.96, "live_pressure": "The question has reached its unresolved boundary", "previous_move_function": "locates the problem", "already_settled": [], "backward_reopen_risks": [], "why_stop_might_be_natural": "The sentence lands on the unresolved chooser question."},
    })
    # Codex pressure reader is separate from its other roles.
    codex.responses["pressure_reader"] = {"state": "NATURAL_STOP", "confidence": 0.94, "live_pressure": "The question has reached its unresolved boundary", "previous_move_function": "locates the problem", "already_settled": [], "backward_reopen_risks": [], "why_stop_might_be_natural": "Further explanation would reopen rather than advance."}
    return RuntimeServices.for_tests(
        claude=claude, codex=codex, pangram=FakePangram(),
        artifact_store=ArtifactStore(tmp_path / ".state" / "artifacts"),
    )


def test_runtime_dependencies_execute_real_basic_thought_flow_without_owner_gold_in_writer(tmp_path):
    root = Path(__file__).resolve().parents[2]
    cfg = RuntimeConfig.from_root(tmp_path)
    services = _fake_services(tmp_path)
    deps = build_runtime_dependencies(cfg, project_root=root, services=services)
    state = seed_initial_state(cfg, project_root=root, source_path=root / "project" / "INPUT.md", services=services)

    state.update(deps.regressions(state))
    assert state["final_local_gates"]["regressions_hard_pass"] is True

    state.update(deps.representation(state))
    assert state["source_provenance"] == "AI_FROM_OWNER_INPUTS"
    assert state["task_mode"] in {"P2S", "P3"}
    assert state["atom_refs"]

    state.update(deps.generation(state))
    assert state["accepted_moves"]
    writer_calls = [c for c in services.claude.calls if c.role == "writer"]
    assert writer_calls
    writer_prompt = writer_calls[-1].prompt
    owner_gold = (root / "project" / "HUMAN-FLOW-GOLD.json").read_text()
    assert "owner-neg-sidestep-live-question" not in writer_prompt
    assert owner_gold not in writer_prompt
    assert "The free-will question bothered me for almost the same reason" not in writer_prompt

    # Second generation call precommits a natural stop and ends before inventing aftercare.
    state.update(deps.generation(state))
    assert state["status"] == "generated"

    state.update(deps.cold_audit(state))
    assert state["final_local_gates"]["hard_pass"] is True

    state.update(deps.freeze(state))
    assert state["candidate_ref"]

    state.update(deps.detector(state))
    assert state["pangram_result_ref"]
    assert services.pangram.calls


def test_seed_initial_state_snapshots_source_and_authority_inputs_content_addressably(tmp_path):
    root = Path(__file__).resolve().parents[2]
    cfg = RuntimeConfig.from_root(tmp_path)
    services = _fake_services(tmp_path)
    state = seed_initial_state(cfg, project_root=root, source_path=root / "project" / "INPUT.md", services=services)
    for key in ["source_ref", "requirements_ref", "author_context_ref", "owner_gold_ref", "semantic_gold_ref", "diagnostic_positive_ref"]:
        assert services.artifact_store.find(state[key]) is not None


def test_next_attempt_directive_is_consumed_after_one_checkpointed_generation(tmp_path):
    root = Path(__file__).resolve().parents[2]
    cfg = RuntimeConfig.from_root(tmp_path)
    services = _fake_services(tmp_path)
    proposals = iter([
        "First advance. Second advance.",
        "If my choices arise from conditions too, what exactly would a chooser outside those conditions even be doing?",
    ])
    services.claude.responses["writer"] = lambda _call: next(proposals)
    deps = build_runtime_dependencies(cfg, project_root=root, services=services)
    state = seed_initial_state(cfg, project_root=root, source_path=root / "project" / "INPUT.md", services=services)
    state.update(deps.representation(state))
    state["owner_directives"] = [{
        "id": "d1",
        "instruction": "Start from the concrete contradiction.",
        "scope": "NEXT_ATTEMPT",
        "restart_depth": "CURRENT_STAGE",
        "consumed": False,
    }]

    first = deps.generation(state)
    first_prompt = [call for call in services.claude.calls if call.role == "writer"][-1].prompt
    assert "CONFIRMED OWNER DIRECTIONS" in first_prompt
    assert "Start from the concrete contradiction." in first_prompt
    assert "d1" in first["consumed_directive_ids"]

    state.update(first)
    deps.generation(state)
    second_prompt = [call for call in services.claude.calls if call.role == "writer"][-1].prompt
    assert "Start from the concrete contradiction." not in second_prompt


def test_generation_acceptance_records_exact_per_move_coverage(tmp_path):
    root = Path(__file__).resolve().parents[2]
    cfg = RuntimeConfig.from_root(tmp_path)
    services = _fake_services(tmp_path)
    deps = build_runtime_dependencies(cfg, project_root=root, services=services)
    state = seed_initial_state(cfg, project_root=root, source_path=root / "project" / "INPUT.md", services=services)
    state.update(deps.representation(state))

    update = deps.generation(state)

    move = update["accepted_moves"][-1]
    assert update["accepted_move_coverage"] == [{
        "move_sha256": sha256(move.encode("utf-8")).hexdigest(),
        "covered_unit_ids": ["u001"],
    }]
    assert update["coverage_reconciliation_required"] is False


def test_rejected_proposal_and_owner_reason_reach_writer_but_owner_gold_does_not(tmp_path):
    root = Path(__file__).resolve().parents[2]
    cfg = RuntimeConfig.from_root(tmp_path)
    services = _fake_services(tmp_path)
    deps = build_runtime_dependencies(cfg, project_root=root, services=services)
    state = seed_initial_state(cfg, project_root=root, source_path=root / "project" / "INPUT.md", services=services)
    state.update(deps.representation(state))
    rejected_text = "Do not repeat this proposal."
    rejected_ref = services.artifact_store.put_text(rejected_text, "md", {"kind": "proposal"}).sha256
    state["rejected_proposals"] = [{
        "proposal_ref": rejected_ref,
        "proposal_sha256": rejected_ref,
        "reason": "It dodges the live question.",
    }]

    deps.generation(state)
    prompt = [call for call in services.claude.calls if call.role == "writer"][-1].prompt

    assert rejected_text in prompt
    assert "It dodges the live question." in prompt
    assert "owner-neg-sidestep-live-question" not in prompt
    assert "The free-will question bothered me for almost the same reason" not in prompt


def test_meaning_correction_is_represented_as_owner_grounded_without_changing_source(tmp_path):
    root = Path(__file__).resolve().parents[2]
    cfg = RuntimeConfig.from_root(tmp_path)
    services = _fake_services(tmp_path)
    deps = build_runtime_dependencies(cfg, project_root=root, services=services)
    state = seed_initial_state(cfg, project_root=root, source_path=root / "project" / "INPUT.md", services=services)
    source_artifact = services.artifact_store.find(state["source_ref"])
    before = source_artifact.path.read_bytes()
    state["owner_authority_corrections"] = [{
        "id": "correction-1",
        "instruction": "The choice belongs to the community, not the institution.",
        "reason": "The actor was wrong.",
        "authority": "OWNER_GROUNDED",
    }]

    update = deps.representation(state)

    representation_prompt = [call for call in services.codex.calls if call.role == "representation"][-1].prompt
    assert "The choice belongs to the community, not the institution." in representation_prompt
    units = [json.loads(services.artifact_store.find(ref).path.read_text()) for ref in update["atom_refs"]]
    correction = [unit for unit in units if unit["id"] == "correction-1"][0]
    assert correction["authority"] == "OWNER_GROUNDED"
    assert correction["exact_lock"] is False
    assert correction["reason"] == "owner supervisor meaning correction"
    assert source_artifact.path.read_bytes() == before


class RaisingAdapter:
    def call(self, call, runner, store):
        raise RuntimeError("provider capacity unavailable")


def test_runtime_provider_exception_becomes_machine_failure_state_not_user_exception(tmp_path):
    root = Path(__file__).resolve().parents[2]
    cfg = RuntimeConfig.from_root(tmp_path)
    base = _fake_services(tmp_path)
    services = RuntimeServices.for_tests(
        claude=base.claude,
        codex=RaisingAdapter(),
        pangram=base.pangram,
        artifact_store=base.artifact_store,
    )
    deps = build_runtime_dependencies(cfg, project_root=root, services=services)
    state = seed_initial_state(cfg, project_root=root, source_path=root / "project" / "INPUT.md", services=services)

    update = deps.representation(state)

    assert update["status"] == "machine_failure"
    assert update["failure_class"] == "PROVIDER_PLUMBING"
    assert update["failure_origin_node"] == "representation"
    assert update["failure_record_ref"]


def test_runtime_repair_dependency_invokes_machine_cycle_without_owner(tmp_path):
    root = Path(__file__).resolve().parents[2]
    cfg = RuntimeConfig.from_root(tmp_path)
    base = _fake_services(tmp_path)
    calls = []

    def repair_cycle(state):
        calls.append(dict(state))
        return {"pass": True, "program_version": "repair-commit"}

    base.repair_cycle = repair_cycle
    deps = build_runtime_dependencies(cfg, project_root=root, services=base)
    update = deps.repair({"status": "machine_failure", "failure_class": "PROVIDER_PLUMBING", "repair_attempt": 0})
    assert calls
    assert update["status"] == "repair_promoted"
    assert update["repair_attempt"] == 1
    assert update["program_version"] == "repair-commit"


def test_runtime_repair_propagates_restart_required(tmp_path):
    root = Path(__file__).resolve().parents[2]
    cfg = RuntimeConfig.from_root(tmp_path)
    base = _fake_services(tmp_path)
    base.repair_cycle=lambda state: {'pass':True,'program_version':'new-code','restart_required':True}
    deps=build_runtime_dependencies(cfg,project_root=root,services=base)
    update=deps.repair({'status':'machine_failure','repair_attempt':0})
    assert update['status']=='repair_promoted_restart_required'
    assert update['restart_required'] is True


def test_runtime_semantic_sanity_failure_runs_developmental_reconstruction_before_writer(tmp_path):
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    services.codex.responses['representation']={
        'section_job':'inherited section job',
        'semantic_sanity':{
            'status':'FAIL','defect_types':['wrong_thought'],'research_trigger':False,
            'recommended_escalation':'P4','owner_question':'',
        },
        'units':[
            {'id':'u-owner','text':'Choices arise from conditions.','reason':'owner-grounded input'},
            {'id':'u-ai','text':'The inherited citation answers the question.','reason':'AI bridge'},
        ],
    }
    services.codex.responses['developmental']={
        'architecture_card':{
            'heading_promise':'free will question','real_pressure':'If choices are conditioned, what is choosing?',
            'reader_stake':'understand the actual problem','controlling_claim':'choices arise from conditions',
            'certainty':'owner-grounded','motive_obligation':'','intellectual_lived_route':[],
            'actor_action_object':[],'causality_chronology':[],'source_landscape':[],
            'strongest_complication':'choosing still happens','governing_movement':'inquiry',
            'paragraph_jobs':[],'stopping_point':'unresolved chooser question','exact_language_reasons':[],
        },
        'corrected_units':[
            {'id':'u-owner','text':'Choices arise from conditions.','disposition':'use','reason':'retain grounded premise','origin':'source'},
            {'id':'u-ai','text':'The inherited citation answers the question.','disposition':'omit','reason':'AI-provisional source role may be wrong','origin':'source'},
        ],
        'owner_position_diverges':False,
        'unresolved_authorial':[],
    }
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    state=seed_initial_state(cfg,project_root=root,source_path=root/'project'/'INPUT.md',services=services)
    state.update(deps.representation(state))
    assert state['status']=='represented'
    assert state['task_mode'] in {'P3','P4'}
    assert state['developmental_ref']
    units=[json.loads(services.artifact_store.find(ref).path.read_text()) for ref in state['atom_refs']]
    assert [u['id'] for u in units]==['u-owner']
    assert any(c.role=='developmental' for c in services.codex.calls)


def test_runtime_research_escalation_keeps_faithful_position_separate_from_better_reasoned_alternative(tmp_path):
    from authorial_flow.research.base import SearchHit, RetrievedSource
    from authorial_flow.research.evidence import AccessLevel
    class Provider:
        def search(self,query,limit):
            return [SearchHit(title='Primary',url='https://example.test/primary',primary_hint=True)]
    class Fetcher:
        def fetch(self,url):
            return RetrievedSource(url=url,final_url=url,mime_type='text/plain',body='Primary text.',body_sha256='abc',retrieved_at=1.0,access_level=AccessLevel.FULL_TEXT,headers={})
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    services.research_provider=Provider(); services.research_fetcher=Fetcher()
    services.codex.responses['representation']={
        'section_job':'free will inquiry',
        'semantic_sanity':{
            'status':'FAIL','defect_types':['source_role'],'research_trigger':True,
            'recommended_escalation':'RESEARCH','owner_question':'',
        },
        'units':[{'id':'u1','text':'The inherited citation bears on the question.','reason':'AI source role'}],
    }
    services.codex.responses['research_question']={
        'uncertainty':'Does the inherited citation directly answer the free-will question?',
        'material_consequence':'The thought route and source choice may change.',
        'query':'early Buddhist free will intention contact',
    }
    services.codex.responses['research_evidence']={
        'evidence':[{'source_ref':'abc','access_level':'full_text','primary_status':'primary','supports':['citation says X'],'resists':['direct answer relation'],'system_inference':['use a different route']}],
        'stable':True,'access_limits':[],
    }
    services.codex.responses['research_developmental']={
        'architecture_card':{
            'heading_promise':'free will','real_pressure':'what is choosing?','reader_stake':'understand it',
            'controlling_claim':'choices are conditioned','certainty':'provisional','motive_obligation':'',
            'intellectual_lived_route':[],'actor_action_object':[],'causality_chronology':[],
            'source_landscape':['primary evidence resists inherited source role'],'strongest_complication':'',
            'governing_movement':'inquiry','paragraph_jobs':[],'stopping_point':'open question','exact_language_reasons':[],
        },
        'corrected_units':[{'id':'u1','text':'The citation does not directly settle the question.','disposition':'use','reason':'research-informed candidate','origin':'research_candidate'}],
        'owner_position_diverges':True,'unresolved_authorial':[],
    }
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    state=seed_initial_state(cfg,project_root=root,source_path=root/'project'/'INPUT.md',services=services)
    state.update(deps.representation(state))
    assert state['better_reasoned_alternative_ref']
    assert state['faithful_position_ref']
    assert state['atom_refs']  # faithful route remains active until owner adopts alternative
    assert state['better_reasoned_alternative_ref'] != state['faithful_position_ref']


def test_runtime_detector_tries_bounded_meaning_preserving_variant_without_replacing_editorial_winner(tmp_path):
    from authorial_flow.models.pangram import PangramResult
    class SequencePangram:
        def __init__(self): self.calls=[]
        def evaluate(self,text,candidate_hash,pending=None):
            self.calls.append(text)
            if len(self.calls)==1:
                return PangramResult('STAGE_SUCCESS','4.0','AI',1.0,0.0,(),{'prediction_short':'AI'},False)
            return PangramResult('STAGE_SUCCESS','4.0','Human',0.0,0.0,(),{'prediction_short':'Human'},True)
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    services.pangram=SequencePangram()
    services.claude.responses['detector_variant']='If my choices arise from conditions too, what would a chooser outside those conditions even be doing?'
    services.codex.responses['detector_variant_fidelity']={
        'verdict':'PASS','confidence':0.95,'failure_type':'none','reason':'meaning preserved','covered_unit_ids':['u001','u002']
    }
    services.codex.responses['detector_variant_audit']={
        'defects':[],'semantic_sanity':True,'curious_reader_chain':True,'stopping_point_ok':True,'fidelity_ok':True
    }
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    text='If my choices arise from conditions too, what exactly would a chooser outside those conditions even be doing?'
    candidate={
        'id':'candidate-parent','text':text,'editorial_score':1.0,'hard_pass':True,'frozen':True,
        'accepted_moves':(text,),'text_artifact_ref':'','role':'DEVELOPMENTAL','material_route':'live-thought-flow',
    }
    candidate_ref=_put_candidate_for_test=services.artifact_store.put_text(json.dumps(candidate,default=list), 'json', {'kind':'candidate-record'}).sha256
    state={'candidate_ref':candidate_ref,'final_local_gates':{'hard_pass':True},'source_ref':services.artifact_store.put_text('source','md',{}).sha256,
           'atom_refs':[],'detector_variant_attempt':0}
    first=deps.detector(state)
    assert first['status']=='detector_retry'
    state.update(first)
    second=deps.detector(state)
    assert second['status']=='owner_review_ready'
    assert second['recommended_candidate_ref']==candidate_ref
    assert second['pangram_human_variant_ref']
    assert len(services.pangram.calls)==2



def test_runtime_services_lazy_research_provider_factory_is_called_only_when_requested(tmp_path):
    services=_fake_services(tmp_path)
    services.research_provider=None
    calls=[]
    provider=object()
    services.research_provider_factory=lambda: calls.append('research') or provider
    assert calls==[]
    assert services.ensure_research_provider() is provider
    assert calls==['research']
    assert services.ensure_research_provider() is provider
    assert calls==['research']


def test_runtime_services_lazy_pangram_factory_is_called_only_when_requested(tmp_path):
    calls=[]
    services=RuntimeServices.for_tests(
        claude=object(), codex=object(), pangram=None,
        artifact_store=ArtifactStore(tmp_path / '.state' / 'artifacts'),
    )
    services.pangram_factory=lambda: calls.append('pangram') or FakePangram()
    assert calls == []
    client=services.ensure_pangram()
    assert calls == ['pangram']
    assert client is services.pangram
    assert services.ensure_pangram() is client
    assert calls == ['pangram']


def test_runtime_services_default_codex_models_skip_unsupported_plain_gpt_5_6(tmp_path,monkeypatch):
    monkeypatch.delenv('AUTHORIAL_CODEX_MODELS',raising=False)
    services=RuntimeServices.from_config(RuntimeConfig.from_root(tmp_path))
    assert services.codex.models == ['gpt-5.6-sol', None]


def test_detector_invalidates_rejected_pangram_key_and_retries_with_key_provider(tmp_path,monkeypatch):
    import httpx
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)

    class RejectingPangram:
        def request_identity(self,candidate_hash): return 'identity-'+candidate_hash
        def ensure_access(self):
            request=httpx.Request('GET','https://text.external-api.pangram.com/task/00000000-0000-0000-0000-000000000000')
            response=httpx.Response(401,request=request)
            raise httpx.HTTPStatusError('unauthorized',request=request,response=response)
        def submit(self,*args,**kwargs): raise AssertionError('must not submit with rejected key')
        def poll(self,*args,**kwargs): raise AssertionError('must not poll with rejected key')

    replacement=FakePangram(); factory_calls=[]
    services.pangram=RejectingPangram()
    services.pangram_factory=lambda: factory_calls.append('refresh') or replacement
    monkeypatch.setenv('PANGRAM_API_KEY','rejected-key')
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    text='A coherent candidate.'
    candidate={
        'id':'pangram-auth-parent','text':text,'editorial_score':1.0,'hard_pass':True,'frozen':True,
        'accepted_moves':(text,),'text_artifact_ref':'','role':'P2','material_route':'live-thought-flow',
    }
    candidate_ref=services.artifact_store.put_text(json.dumps(candidate,default=list),'json',{'kind':'candidate-record'}).sha256
    state={'candidate_ref':candidate_ref,'recommended_candidate_ref':candidate_ref,'final_local_gates':{'hard_pass':True}}

    first=deps.detector(state)
    assert first['status'] == 'detector_retry'
    assert first['credential_refresh_required'] == 'PANGRAM_API_KEY'
    assert services.pangram is None
    assert 'PANGRAM_API_KEY' not in __import__('os').environ

    state.update(first)
    second=deps.detector(state)
    assert factory_calls == ['refresh']
    assert second['status'] == 'owner_review_ready'


def test_cold_audit_revises_only_when_defects_exist_then_reaudits(tmp_path):
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    audits=iter([
        {
            'defects':[{'code':'aftercare','detail':'The second sentence re-explains the landing.','severity':'important'}],
            'semantic_sanity':True,'curious_reader_chain':False,'stopping_point_ok':False,'fidelity_ok':True,
        },
        {
            'defects':[], 'semantic_sanity':True,'curious_reader_chain':True,
            'stopping_point_ok':True,'fidelity_ok':True,
        },
    ])
    services.codex.responses['cold_audit']=lambda call: next(audits)
    services.codex.responses['cold_revision_fidelity']={
        'verdict':'PASS','confidence':0.98,'failure_type':'none','reason':'', 'covered_unit_ids':[]
    }
    services.claude.responses['cold_revision']='First sentence. Better ending.'
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    state=seed_initial_state(cfg,project_root=root,source_path=root/'project'/'INPUT.md',services=services)
    state.update({
        'accepted_moves':['First sentence.','Bad aftercare.'],
        'accepted_move_coverage':[
            {'move_sha256':sha256(b'First sentence.').hexdigest(),'covered_unit_ids':['u001']},
            {'move_sha256':sha256(b'Bad aftercare.').hexdigest(),'covered_unit_ids':['u002']},
        ],
        'task_mode':'P3','source_provenance':'AI_FROM_OWNER_INPUTS',
        'final_local_gates':{'regressions_hard_pass':True},
    })
    update=deps.cold_audit(state)
    assert update['status']=='local_gates_passed'
    assert update['accepted_moves']==['First sentence.','Better ending.']
    assert update['accepted_move_coverage']==[]
    assert update['coverage_reconciliation_required'] is True
    assert len(update['final_local_gates']['cold_audit_refs'])==2
    assert any(call.role=='cold_revision' for call in services.claude.calls)
    assert any(call.role=='cold_revision_fidelity' for call in services.codex.calls)


def test_cold_audit_no_defects_does_not_paraphrase_for_novelty(tmp_path):
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    services.claude.responses['cold_revision']=lambda call: (_ for _ in ()).throw(AssertionError('no revision allowed'))
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    state=seed_initial_state(cfg,project_root=root,source_path=root/'project'/'INPUT.md',services=services)
    state.update({
        'accepted_moves':['Already good.'], 'task_mode':'P3',
        'final_local_gates':{'regressions_hard_pass':True},
    })
    update=deps.cold_audit(state)
    assert update['status']=='local_gates_passed'
    assert update['accepted_moves']==['Already good.']
    assert not any(call.role=='cold_revision' for call in services.claude.calls)


def test_cold_audited_candidate_preserves_exact_paragraph_boundaries_through_freeze(tmp_path):
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    audits=iter([
        {
            'defects':[{'code':'aftercare','detail':'repair','severity':'important'}],
            'semantic_sanity':True,'curious_reader_chain':False,'stopping_point_ok':False,'fidelity_ok':True,
        },
        {
            'defects':[], 'semantic_sanity':True,'curious_reader_chain':True,
            'stopping_point_ok':True,'fidelity_ok':True,
        },
    ])
    services.codex.responses['cold_audit']=lambda call: next(audits)
    services.codex.responses['cold_revision_fidelity']={
        'verdict':'PASS','confidence':0.99,'failure_type':'none','reason':'','covered_unit_ids':[]
    }
    exact='First paragraph.\n\nBetter ending.'
    services.claude.responses['cold_revision']=exact
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    state=seed_initial_state(cfg,project_root=root,source_path=root/'project'/'INPUT.md',services=services)
    state.update({
        'accepted_moves':['First paragraph.','Bad aftercare.'],
        'task_mode':'P3','source_provenance':'AI_FROM_OWNER_INPUTS',
        'final_local_gates':{'regressions_hard_pass':True},
    })
    cold=deps.cold_audit(state)
    assert cold['candidate_text_ref']
    candidate_text=services.artifact_store.find(cold['candidate_text_ref']).path.read_text()
    assert candidate_text==exact
    state.update(cold)
    frozen=deps.freeze(state)
    record=json.loads(services.artifact_store.find(frozen['candidate_ref']).path.read_text())
    assert record['text']==exact


def test_owner_final_p2s_semantic_failure_cannot_escalate_to_substantive_rewrite_without_owner(tmp_path):
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    services.codex.responses['representation']={
        'section_job':'owner-final thought',
        'semantic_sanity':{
            'status':'FAIL','defect_types':['wrong_thought'],'research_trigger':False,
            'recommended_escalation':'P4','owner_question':'Did you mean X or Y?',
        },
        'units':[{'id':'u1','text':'Owner-final sentence.','reason':'locked owner text'}],
    }
    services.codex.responses['developmental']=lambda call: (_ for _ in ()).throw(
        AssertionError('P2S must not invoke substantive developmental reconstruction without owner authority')
    )
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    state=seed_initial_state(cfg,project_root=root,source_path=root/'project'/'INPUT.md',services=services)
    state['source_metadata']={'provenance_override':'OWNER_FINAL'}
    update=deps.representation(state)

    assert update['status']=='owner_ambiguity_required'
    assert update['task_mode']=='P2S'
    assert update['interrupt_payload']['kind']=='AUTHORIAL_AMBIGUITY'
    assert not any(call.role=='developmental' for call in services.codex.calls)


def test_nonresearch_developmental_position_divergence_never_becomes_active_byline(tmp_path):
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    services.codex.responses['representation']={
        'section_job':'free will inquiry',
        'semantic_sanity':{
            'status':'FAIL','defect_types':['wrong_thought'],'research_trigger':False,
            'recommended_escalation':'P4','owner_question':'Which position is yours?',
        },
        'units':[{'id':'u1','text':'Faithful inherited position.','reason':'owner-input route'}],
    }
    services.codex.responses['developmental']={
        'architecture_card':{
            'heading_promise':'free will','real_pressure':'what is choosing?','reader_stake':'understand it',
            'controlling_claim':'alternative claim','certainty':'candidate','motive_obligation':'',
            'intellectual_lived_route':[],'actor_action_object':[],'causality_chronology':[],
            'source_landscape':[],'strongest_complication':'','governing_movement':'inquiry',
            'paragraph_jobs':[],'stopping_point':'open','exact_language_reasons':[],
        },
        'corrected_units':[{'id':'u1','text':'Different system-authored position.','disposition':'use','reason':'alternative reasoning','origin':'source'}],
        'owner_position_diverges':True,'unresolved_authorial':[],
    }
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    state=seed_initial_state(cfg,project_root=root,source_path=root/'project'/'INPUT.md',services=services)
    update=deps.representation(state)

    assert update['status']=='owner_ambiguity_required'
    assert update['better_reasoned_alternative_ref']
    assert update['faithful_position_ref']
    assert update['interrupt_payload']['kind']=='AUTHORIAL_AMBIGUITY'


def test_nondivergent_research_repair_returns_research_informed_units_to_thought_flow(tmp_path):
    from authorial_flow.research.base import SearchHit, RetrievedSource
    from authorial_flow.research.evidence import AccessLevel
    class Provider:
        def search(self,query,limit):
            return [SearchHit(title='Primary',url='https://example.test/primary',primary_hint=True)]
    class Fetcher:
        def fetch(self,url):
            return RetrievedSource(url=url,final_url=url,mime_type='text/plain',body='Primary text.',body_sha256='abc',retrieved_at=1.0,access_level=AccessLevel.FULL_TEXT,headers={})
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    services.research_provider=Provider(); services.research_fetcher=Fetcher()
    services.codex.responses['representation']={
        'section_job':'free will inquiry',
        'semantic_sanity':{
            'status':'FAIL','defect_types':['source_role'],'research_trigger':True,
            'recommended_escalation':'RESEARCH','owner_question':'',
        },
        'units':[{'id':'u1','text':'The inherited citation directly answers it.','reason':'AI source role'}],
    }
    services.codex.responses['research_question']={
        'uncertainty':'Does the citation directly answer it?','material_consequence':'source role changes','query':'bounded query'
    }
    services.codex.responses['research_evidence']={
        'evidence':[{'source_ref':'abc','access_level':'full_text','primary_status':'primary','supports':[],'resists':['direct answer'],'system_inference':['narrow the role']}],
        'stable':True,'access_limits':[],
    }
    services.codex.responses['research_developmental']={
        'architecture_card':{
            'heading_promise':'free will','real_pressure':'what is choosing?','reader_stake':'understand it',
            'controlling_claim':'citation bears indirectly','certainty':'supported','motive_obligation':'',
            'intellectual_lived_route':[],'actor_action_object':[],'causality_chronology':[],
            'source_landscape':['primary source'],'strongest_complication':'','governing_movement':'inquiry',
            'paragraph_jobs':[],'stopping_point':'open','exact_language_reasons':[],
        },
        'corrected_units':[{'id':'u1','text':'The citation bears on the question without directly settling it.','disposition':'use','reason':'research corrects source role','origin':'research_candidate'}],
        'owner_position_diverges':False,'unresolved_authorial':[],
    }
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    state=seed_initial_state(cfg,project_root=root,source_path=root/'project'/'INPUT.md',services=services)
    update=deps.representation(state)

    assert update['status']=='represented'
    units=[json.loads(services.artifact_store.find(ref).path.read_text()) for ref in update['atom_refs']]
    assert [u['text'] for u in units]==['The citation bears on the question without directly settling it.']


def test_divergent_research_route_requires_explicit_research_adoption_interrupt(tmp_path):
    from authorial_flow.research.base import SearchHit, RetrievedSource
    from authorial_flow.research.evidence import AccessLevel
    class Provider:
        def search(self,query,limit):
            return [SearchHit(title='Primary',url='https://example.test/primary',primary_hint=True)]
    class Fetcher:
        def fetch(self,url):
            return RetrievedSource(url=url,final_url=url,mime_type='text/plain',body='Primary text.',body_sha256='abc',retrieved_at=1.0,access_level=AccessLevel.FULL_TEXT,headers={})
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    services.research_provider=Provider(); services.research_fetcher=Fetcher()
    services.codex.responses['representation']={
        'section_job':'free will inquiry',
        'semantic_sanity':{'status':'FAIL','defect_types':['source_role'],'research_trigger':True,'recommended_escalation':'RESEARCH','owner_question':''},
        'units':[{'id':'u1','text':'Faithful position.','reason':'owner-input route'}],
    }
    services.codex.responses['research_question']={'uncertainty':'q','material_consequence':'changes position','query':'q'}
    services.codex.responses['research_evidence']={'evidence':[],'stable':True,'access_limits':[]}
    services.codex.responses['research_developmental']={
        'architecture_card':{'heading_promise':'h','real_pressure':'p','reader_stake':'s','controlling_claim':'alt','certainty':'candidate','motive_obligation':'','intellectual_lived_route':[],'actor_action_object':[],'causality_chronology':[],'source_landscape':[],'strongest_complication':'','governing_movement':'inquiry','paragraph_jobs':[],'stopping_point':'open','exact_language_reasons':[]},
        'corrected_units':[{'id':'u1','text':'Research-backed different position.','disposition':'use','reason':'alternative','origin':'research_candidate'}],
        'owner_position_diverges':True,'unresolved_authorial':[],
    }
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    state=seed_initial_state(cfg,project_root=root,source_path=root/'project'/'INPUT.md',services=services)
    update=deps.representation(state)

    assert update['status']=='research_adoption_required'
    assert update['interrupt_payload']['kind']=='RESEARCH_ADOPTION'
    assert update['faithful_position_ref']
    assert update['better_reasoned_alternative_ref']


def test_owner_authorial_answer_is_installed_as_grounded_unit_on_resumed_representation(tmp_path):
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    services.codex.responses['representation']={
        'section_job':'free will inquiry',
        'semantic_sanity':{'status':'FAIL','defect_types':['authorial_ambiguity'],'research_trigger':False,'recommended_escalation':'OWNER','owner_question':'Which meaning?'},
        'units':[{'id':'u7','text':'Ambiguous system reconstruction.','reason':'open meaning'}],
    }
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    state=seed_initial_state(cfg,project_root=root,source_path=root/'project'/'INPUT.md',services=services)
    state.update({
        'resolved_authorial_answer':'Choosing happens without a separate chooser.',
        'open_authorial_unit_id':'u7',
        'section_job':'free will inquiry',
    })
    update=deps.representation(state)

    assert update['status']=='represented'
    units=[json.loads(services.artifact_store.find(ref).path.read_text()) for ref in update['atom_refs']]
    assert units[0]['id']=='u7'
    assert units[0]['text']=='Choosing happens without a separate chooser.'
    assert units[0]['authority']=='OWNER_GROUNDED'


def test_owner_adopted_research_alternative_resumes_directly_from_adopted_units(tmp_path):
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    alternative={
        'architecture_card':{},
        'corrected_units':[{'id':'u1','text':'Owner adopted researched position.','disposition':'use','reason':'owner adopted','origin':'research_candidate'}],
        'owner_position_diverges':True,
        'unresolved_authorial':[],
    }
    alt_ref=services.artifact_store.put_text(json.dumps(alternative),'json',{'kind':'developmental-result'}).sha256
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    state=seed_initial_state(cfg,project_root=root,source_path=root/'project'/'INPUT.md',services=services)
    calls_before=len(services.codex.calls)
    state.update({
        'adopted_alternative_ref':alt_ref,
        'better_reasoned_alternative_ref':alt_ref,
        'faithful_position_ref':'faithful:old',
        'research_ref':'research:1',
        'section_job':'free will inquiry',
        'task_mode':'P3',
    })
    update=deps.representation(state)

    assert update['status']=='represented'
    units=[json.loads(services.artifact_store.find(ref).path.read_text()) for ref in update['atom_refs']]
    assert [u['text'] for u in units]==['Owner adopted researched position.']
    assert units[0]['authority']=='OWNER_GROUNDED'
    assert len(services.codex.calls)==calls_before


def test_owner_keep_position_resumes_from_exact_faithful_units_without_research_repeating(tmp_path):
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    faithful={'units':[{'id':'u1','text':'Faithful owner position.','authority':'OWNER_GROUNDED','exact_lock':False,'disposition':'unresolved','reason':'faithful'}]}
    faithful_ref=services.artifact_store.put_text(json.dumps(faithful),'json',{'kind':'faithful-position'}).sha256
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    state=seed_initial_state(cfg,project_root=root,source_path=root/'project'/'INPUT.md',services=services)
    calls_before=len(services.codex.calls)
    state.update({
        'kept_faithful_position_ref':faithful_ref,
        'faithful_position_ref':faithful_ref,
        'better_reasoned_alternative_ref':'alt:1',
        'research_ref':'research:1',
        'section_job':'free will inquiry',
        'task_mode':'P3',
    })
    update=deps.representation(state)

    assert update['status']=='represented'
    units=[json.loads(services.artifact_store.find(ref).path.read_text()) for ref in update['atom_refs']]
    assert [u['text'] for u in units]==['Faithful owner position.']
    assert len(services.codex.calls)==calls_before


def test_generation_stops_durably_at_configured_writer_attempt_budget_without_another_model_call(tmp_path):
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    state=seed_initial_state(cfg,project_root=root,source_path=root/'project'/'INPUT.md',services=services)
    state.update(deps.representation(state))
    state['retry_count']=cfg.writer_attempts
    claude_before=len(services.claude.calls)
    codex_before=len(services.codex.calls)

    update=deps.generation(state)

    assert update['status']=='machine_failure'
    assert update['failure_class']=='GENERATION_DEAD_END'
    assert update['budget']=='writer_attempts'
    assert len(services.claude.calls)==claude_before
    assert len(services.codex.calls)==codex_before


def test_runtime_pangram_checkpoints_async_task_before_poll_and_resumes_without_resubmit(tmp_path):
    from authorial_flow.models.pangram import PangramTask, PangramResult
    class AsyncPangram:
        def __init__(self):
            self.submits=[]; self.polls=[]; self.access_checks=0
        def ensure_access(self): self.access_checks += 1
        def request_identity(self, candidate_hash): return 'identity:'+candidate_hash
        def submit(self,text,candidate_hash):
            self.submits.append((text,candidate_hash))
            return PangramTask('task-1',self.request_identity(candidate_hash),candidate_hash,'pangram-4')
        def poll(self,task_id):
            self.polls.append(task_id)
            if len(self.polls)==1:
                return PangramResult('STAGE_RUNNING','4.0','',0.0,0.0,(),{'stage':'STAGE_RUNNING','version':'4.0'},False)
            return PangramResult('STAGE_SUCCESS','4.0','Human',0.0,0.0,(),{'stage':'STAGE_SUCCESS','version':'4.0','prediction_short':'Human','fraction_ai':0,'fraction_ai_assisted':0},True)
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    services.pangram=AsyncPangram()
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    text='A frozen editorial winner.'
    candidate={
        'id':'candidate-parent','text':text,'editorial_score':1.0,'hard_pass':True,'frozen':True,
        'accepted_moves':(text,),'text_artifact_ref':'','role':'DEVELOPMENTAL','material_route':'live-thought-flow',
    }
    candidate_ref=services.artifact_store.put_text(json.dumps(candidate,default=list),'json',{'kind':'candidate-record'}).sha256
    state={
        'candidate_ref':candidate_ref,'final_local_gates':{'hard_pass':True},
        'source_ref':services.artifact_store.put_text('source','md',{}).sha256,
        'atom_refs':[],'detector_variant_attempt':0,
    }

    first=deps.detector(state)
    assert first['status']=='detector_poll_pending'
    assert first['pangram_task_id']=='task-1'
    assert len(services.pangram.submits)==1
    assert services.pangram.polls==[]

    state.update(first)
    second=deps.detector(state)
    assert second['status']=='detector_poll_pending'
    assert len(services.pangram.submits)==1
    assert services.pangram.polls==['task-1']

    state.update(second)
    third=deps.detector(state)
    assert third['status']=='owner_review_ready'
    assert len(services.pangram.submits)==1
    assert services.pangram.polls==['task-1','task-1']
    assert third['pangram_task_id']==''



def test_detector_version_mismatch_is_not_sent_to_code_repair(tmp_path):
    from authorial_flow.models.pangram import PangramResult, PangramTask
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    class AsyncWrongVersion:
        def request_identity(self,h): return 'identity-'+h
        def ensure_access(self): return None
        def submit(self,text,h): return PangramTask('t1',self.request_identity(h),h,'pangram-4')
        def poll(self,task_id):
            return PangramResult('STAGE_SUCCESS','3.3','Human',0.0,0.0,(),{
                'stage':'STAGE_SUCCESS','version':'3.3','prediction_short':'Human',
                'fraction_ai':0,'fraction_ai_assisted':0,'windows':[]
            },False)
    services.pangram=AsyncWrongVersion()
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    text='A sufficiently long candidate sentence for the detector contract check. ' * 3
    candidate={
        'id':'candidate-parent','text':text,'editorial_score':1.0,'hard_pass':True,'frozen':True,
        'accepted_moves':(text,),'text_artifact_ref':'','role':'DEVELOPMENTAL','material_route':'live-thought-flow',
    }
    candidate_ref=services.artifact_store.put_text(json.dumps(candidate,default=list),'json',{'kind':'candidate-record'}).sha256
    state={'candidate_ref':candidate_ref,'recommended_candidate_ref':candidate_ref,'final_local_gates':{'hard_pass':True}}
    first=deps.detector(state)
    assert first['status']=='detector_poll_pending'
    second=deps.detector({**state,**first})
    assert second['status']=='bounded_detector_contract_stop'
    assert second['detector_required_version']=='4.0'
    assert second['detector_returned_version']=='3.3'


def test_detector_payment_required_stops_for_account_action_without_code_repair(tmp_path):
    import httpx
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    class NoCredits:
        def request_identity(self,h): return 'identity-'+h
        def ensure_access(self):
            request=httpx.Request('GET','https://text.external-api.pangram.com/task/00000000-0000-0000-0000-000000000000')
            response=httpx.Response(402,request=request)
            raise httpx.HTTPStatusError('payment required',request=request,response=response)
        def submit(self,text,h):
            raise AssertionError('402 must stop before Pangram submission')
        def poll(self,task_id):
            raise AssertionError('402 must stop before Pangram polling')
    services.pangram=NoCredits()
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    text='A sufficiently long candidate sentence for a Pangram account action check. ' * 3
    candidate={
        'id':'candidate-parent','text':text,'editorial_score':1.0,'hard_pass':True,'frozen':True,
        'accepted_moves':(text,),'text_artifact_ref':'','role':'DEVELOPMENTAL','material_route':'live-thought-flow',
    }
    candidate_ref=services.artifact_store.put_text(json.dumps(candidate,default=list),'json',{'kind':'candidate-record'}).sha256
    update=deps.detector({'candidate_ref':candidate_ref,'recommended_candidate_ref':candidate_ref,'final_local_gates':{'hard_pass':True}})
    assert update['status']=='bounded_detector_account_stop'
    assert update['detector_account_action']=='PANGRAM_CREDITS'
    assert 'failure_class' not in update


def test_detector_checkpoint_task_forbidden_resubmits_same_candidate_without_invalidating_key(tmp_path, monkeypatch):
    import httpx
    import os
    import time
    from hashlib import sha256
    root=Path(__file__).resolve().parents[2]
    cfg=RuntimeConfig.from_root(tmp_path)
    services=_fake_services(tmp_path)
    class TaskOwnedByOldKey:
        def request_identity(self,h): return 'identity-'+h
        def ensure_access(self): return None
        def submit(self,text,h):
            raise AssertionError('existing checkpoint task should be polled before resubmission')
        def poll(self,task_id):
            request=httpx.Request('GET',f'https://text.external-api.pangram.com/task/{task_id}')
            response=httpx.Response(403,request=request)
            raise httpx.HTTPStatusError('forbidden task',request=request,response=response)
    services.pangram=TaskOwnedByOldKey()
    monkeypatch.setenv('PANGRAM_API_KEY','still-valid-current-key')
    deps=build_runtime_dependencies(cfg,project_root=root,services=services)
    text='A sufficiently long candidate sentence for checkpoint task ownership recovery. ' * 3
    candidate={
        'id':'candidate-parent','text':text,'editorial_score':1.0,'hard_pass':True,'frozen':True,
        'accepted_moves':(text,),'text_artifact_ref':'','role':'DEVELOPMENTAL','material_route':'live-thought-flow',
    }
    candidate_ref=services.artifact_store.put_text(json.dumps(candidate,default=list),'json',{'kind':'candidate-record'}).sha256
    state={
        'candidate_ref':candidate_ref,'recommended_candidate_ref':candidate_ref,
        'final_local_gates':{'hard_pass':True},
        'pangram_task_id':'task-from-old-key',
        'pangram_request_identity':services.pangram.request_identity(sha256(text.encode()).hexdigest()),
        'pangram_candidate_ref':candidate_ref,'pangram_submitted_at':time.time(),
    }
    update=deps.detector(state)
    assert update['status']=='detector_retry'
    assert update['pangram_task_id']==''
    assert update['pangram_request_identity']==''
    assert update['pangram_candidate_ref']==''
    assert update['pangram_submitted_at']==0.0
    assert os.environ.get('PANGRAM_API_KEY')=='still-valid-current-key'
    assert services.pangram is not None
