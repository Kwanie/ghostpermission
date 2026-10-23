from core.integration import adapt_langchain_agent, call_parser


class FakeRunnable:
    def __init__(self, response):
        self.payload = None
        self.response = response

    def invoke(self, payload):
        self.payload = payload
        return self.response


def test_parser_adapter_supports_xml_bytes_signature(tmp_path):
    xml_path = tmp_path / "AndroidManifest.xml"
    xml_path.write_bytes(b"<manifest />")
    seen = {}

    def parser(xml_bytes):
        seen["value"] = xml_bytes
        return ["android.permission.CAMERA"]

    result = call_parser(parser, manifest_path=xml_path)
    assert result == ["android.permission.CAMERA"]
    assert seen["value"] == b"<manifest />"


def test_permission_mapper_adapter_uses_original_prompt_input():
    runnable = FakeRunnable({"title": "Mapping", "severity": "info"})
    adapter = adapt_langchain_agent(runnable, "permission_mapper")
    result = adapter(permissions=["android.permission.CAMERA"], app_description="Flashlight")
    assert runnable.payload == {"permissions": ["android.permission.CAMERA"]}
    assert result["title"] == "Mapping"


def test_purpose_adapter_maps_app_description_to_app_purpose():
    runnable = FakeRunnable({"title": "Purpose"})
    adapter = adapt_langchain_agent(runnable, "purpose_analyst")
    adapter(permissions=["android.permission.CAMERA"], app_description="Flashlight app")
    assert runnable.payload == {
        "app_purpose": "Flashlight app",
        "permissions": ["android.permission.CAMERA"],
    }


def test_reviewer_adapter_sends_json_draft_findings():
    import json

    runnable = FakeRunnable({"title": "Reviewed"})
    adapter = adapt_langchain_agent(runnable, "skeptical_reviewer")
    adapter(app_description="Demo", rule_findings=[{"title": "Check camera"}])
    assert runnable.payload["app_purpose"] == "Demo"
    draft = json.loads(runnable.payload["findings"])
    assert draft["deterministic_rule_findings"][0]["title"] == "Check camera"
