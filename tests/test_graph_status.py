from core.graph_status import STATUS_STYLE, permission_statuses

CAM = "android.permission.CAMERA"
LOC = "android.permission.ACCESS_FINE_LOCATION"
NET = "android.permission.INTERNET"


class Obj:                      # findings can be objects as well as dictionaries
    def __init__(self, severity, evidence):
        self.severity, self.evidence = severity, evidence


def test_without_findings_nothing_is_called_checked():
    assert permission_statuses([CAM, LOC], None) == {CAM: "unchecked", LOC: "unchecked"}

def test_unmentioned_permissions_are_ok():
    assert permission_statuses([CAM, NET], []) == {CAM: "ok", NET: "ok"}

def test_the_worst_finding_wins():
    findings = [{"severity": "review", "evidence": [LOC]}, {"severity": "high", "evidence": [LOC, CAM]},
                {"severity": "justified", "evidence": [CAM]}]
    assert permission_statuses([CAM, LOC, NET], findings) == {CAM: "high", LOC: "high", NET: "ok"}

def test_justified_findings_show_as_explained():
    assert permission_statuses([CAM], [{"severity": "justified", "evidence": [CAM]}]) == {CAM: "justified"}

def test_an_unfamiliar_severity_never_paints_a_permission_as_fine():
    assert permission_statuses([CAM], [{"severity": "low", "evidence": [CAM]}]) == {CAM: "review"}

def test_evidence_that_is_not_a_requested_permission_is_ignored():
    findings = [{"severity": "high", "evidence": ["android.permission.SOMETHING_ELSE", "a quoted sentence"]}]
    assert permission_statuses([CAM], findings) == {CAM: "ok"}

def test_finding_objects_work_too():
    assert permission_statuses([LOC], [Obj("HIGH", [LOC])]) == {LOC: "high"}

def test_every_status_has_a_distinct_shape_and_colour():
    shapes = [style[1] for style in STATUS_STYLE.values()]
    colours = [style[2] for style in STATUS_STYLE.values()]
    assert len(set(shapes)) == len(shapes) and len(set(colours)) == len(colours)
