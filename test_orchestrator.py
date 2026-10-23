from core.orchestrator import build_ghost_graph


def fake_parser(*, manifest_path=None, manifest_xml=None):
    return ["android.permission.CAMERA", "android.permission.RECORD_AUDIO"]


def fake_mapper(**kwargs):
    return {"summary": "Permissions mapped", "count": len(kwargs["permissions"])}


def fake_purpose(**kwargs):
    return {"status": "ok", "note": "purpose checked"}


def fake_combination(**kwargs):
    return {"status": "ok", "note": "combinations checked"}


def fake_reviewer(**kwargs):
    return {"status": "ok", "note": "review completed"}


def test_graph_runs_end_to_end_with_fake_components():
    graph = build_ghost_graph(
        parser_fn=fake_parser,
        knowledge_base={},
        permission_mapper_fn=fake_mapper,
        purpose_analyst_fn=fake_purpose,
        combination_analyst_fn=fake_combination,
        skeptical_reviewer_fn=fake_reviewer,
    )
    result = graph.invoke({
        "manifest_path": "fake.xml",
        "app_name": "Demo",
        "app_description": "Demo app",
        "knowledge_base": {},
        "errors": [],
    })
    assert result["permissions"]
    assert result["report"]["permissions_count"] == 2
    assert result["report"]["rule_findings"]
    assert result["report"]["skeptical_review"]["status"] == "ok"
