from core.orchestrator import run_agent_pipeline

P = "android.permission."
PAYLOAD = {
    "app_name": "BrightTorch",
    "description": "A simple flashlight app. No location or contacts needed.",
    "permissions": [P + "CAMERA", P + "READ_CONTACTS", P + "ACCESS_FINE_LOCATION", P + "INTERNET"],
}
PURPOSE = {"assessments": [{"permission": P + "READ_CONTACTS", "verdict": "concerning", "reason": "A flashlight has no reason to read contacts."}]}
REVIEW = {"challenges": [{"title": "High Exposure Combination (Contacts + Location + Internet)",
                          "innocent_explanation": "Some apps use all three for social features."}]}


def summary(state):
    return sorted((f.title, f.severity) for f in state.final_findings)


def test_no_ai_means_ai_is_reported_as_off():
    state = run_agent_pipeline(dict(PAYLOAD), llm=None)
    assert state.ai_used is False and state.ai_notes == [] and len(state.final_findings) == 3


def test_with_a_model_ai_used_is_true_and_the_review_note_is_added(fake_llm):
    state = run_agent_pipeline(dict(PAYLOAD), llm=fake_llm([PURPOSE, REVIEW]))
    assert state.ai_used is True
    combo = next(f for f in state.final_findings if f.title.startswith("High Exposure"))
    assert combo.severity == "high" and any("innocent explanation (AI)" in l for l in combo.limitations)


def test_a_dead_model_never_stops_the_analysis(fake_llm):
    state = run_agent_pipeline(dict(PAYLOAD), llm=fake_llm(["x", "x", "x", "x"]))
    assert state.ai_used is False and len(state.ai_notes) == 2 and len(state.final_findings) == 3


def test_langgraph_and_the_plain_workflow_give_the_same_answer(fake_llm):
    graph = run_agent_pipeline(dict(PAYLOAD), llm=fake_llm([PURPOSE, REVIEW]), use_graph=True)
    plain = run_agent_pipeline(dict(PAYLOAD), llm=fake_llm([PURPOSE, REVIEW]), use_graph=False)
    assert summary(graph) == summary(plain)
    assert graph.ai_used == plain.ai_used and graph.ai_notes == plain.ai_notes


def test_the_workflow_graph_really_has_five_steps():
    from core.orchestrator import STEPS
    assert [name for name, _ in STEPS] == ["permission_mapper", "purpose_analyst", "combination_analyst",
                                           "merge_findings", "skeptical_reviewer"]
