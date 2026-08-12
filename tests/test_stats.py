from pangram_lab.stats import factorial_effects

def test_factorial_effects_compute_main_and_pairwise_interaction():
    plan={"factors":[{"id":"A"},{"id":"B"}],"probes":[]}
    results={}
    # y = A + 2B + 3AB, encoded as fraction_ai score.
    vals={(0,0):0,(1,0):1,(0,1):2,(1,1):6}
    for i,((a,b),v) in enumerate(vals.items()):
        pid=f'P{i}'; plan['probes'].append({"id":pid,"assignments":[{"factor_id":"A","level":a},{"factor_id":"B","level":b}]})
        results[pid]={"fraction_ai":v,"fraction_ai_assisted":0}
    out=factorial_effects(plan,results)
    assert out['main_effects']['A'] == 2.5  # marginal mean effect
    assert out['main_effects']['B'] == 3.5
    assert out['pairwise_interactions']['A×B'] == 3.0
