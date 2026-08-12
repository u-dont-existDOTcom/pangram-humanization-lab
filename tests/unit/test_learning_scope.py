from authorial_flow.learning import LearningScope, LearningStore


def test_new_owner_label_is_project_authority_not_global(tmp_path):
    store=LearningStore(tmp_path)
    rec=store.append_owner_judgment(kind='LOCAL_EDGE',project_id='p',payload={'verdict':'FAIL'})
    assert rec.scope is LearningScope.PROJECT_AUTHORITY


def test_personal_fact_cannot_promote_to_style_rule(tmp_path):
    store=LearningStore(tmp_path)
    rec=store.append_owner_judgment(kind='MEANING_CORRECTION',project_id='p',payload={'personal_fact':True})
    result=store.promote(rec.id,evidence_refs=['case-2'])
    assert result.promoted is False


def test_general_rule_requires_validation_or_explicit_owner_confirmation(tmp_path):
    store=LearningStore(tmp_path)
    rec=store.append_owner_judgment(kind='GLOBAL_PRECOMPUTED_SHAPE',project_id='p',payload={'abstract_rule':'Do not continue after live curiosity ends.'})
    assert store.promote(rec.id,evidence_refs=['dev:2']).promoted is False
    result=store.promote(rec.id,evidence_refs=['dev:2','validation:3'],explicit_owner_confirmation=False)
    assert result.promoted is True
    assert result.scope is LearningScope.GENERAL_RULE


def test_owner_direction_hypothesis_stays_unpromoted_until_existing_gate_passes(tmp_path):
    store = LearningStore(tmp_path)
    rec = store.append_hypothesis(
        kind="OWNER_DIRECTION",
        project_id="p",
        payload={"abstract_rule": "Follow the concrete contradiction."},
    )

    assert rec.scope is LearningScope.REUSABLE_HYPOTHESIS
    assert store.promoted_rules() == []
    result = store.promote(rec.id, evidence_refs=["dev:2", "validation:3"])
    assert result.promoted is True
    assert store.promoted_rules() == [{
        "id": rec.id,
        "rule": "Follow the concrete contradiction.",
    }]
