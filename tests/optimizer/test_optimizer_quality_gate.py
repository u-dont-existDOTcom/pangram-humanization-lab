from authorial_flow.learning import LearningStore
from authorial_flow.optimizer.program import ProgramBundle
from authorial_flow.optimizer.evaluate import EvaluationScore
from authorial_flow.optimizer.search import OptimizerSearch


def test_detector_only_improvement_cannot_promote_owner_regression(tmp_path):
    store=LearningStore(tmp_path)
    store.append_owner_judgment(kind='LOCAL_EDGE',project_id='p',payload={'abstract_rule':'respect live edge'},partition='dev')
    base=ProgramBundle.build({'edge':'base'},{},graph_compatibility='1')
    candidate=ProgramBundle.build({'edge':'candidate'},{},graph_compatibility='1',parent_id=base.id)
    def proposer(payload,program): return candidate
    def evaluator(program,partition):
        if program.id==candidate.id:
            return EvaluationScore(hard_pass=False,target_metrics={'pangram':1.0},fidelity_regressions=(),owner_regressions=('edge-case',))
        return EvaluationScore(hard_pass=True,target_metrics={'pangram':0.0},fidelity_regressions=(),owner_regressions=())
    search=OptimizerSearch(proposer=proposer,evaluator=evaluator,max_rounds=1)
    assert search.run(base,store) is None
