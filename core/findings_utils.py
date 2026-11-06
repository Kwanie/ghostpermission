"""Removes repeated findings so the user sees each concern once."""

_RANK = {"justified": 0, "safe": 0, "info": 0}
_NAMES = {3: "high", 2: "review"}


def _rank(finding):
    sev = str(finding.severity).lower()
    if sev in _RANK:
        return _RANK[sev]
    if "high" in sev:
        return 3
    if "review" in sev or "caution" in sev or "warning" in sev:
        return 2
    return 1


def _same_concern(evidence_a, evidence_b):
    if not evidence_a or not evidence_b:
        return False
    if evidence_a == evidence_b:
        return True
    # two combination findings where one is part of the other: keep the bigger one
    return len(evidence_a) >= 2 and len(evidence_b) >= 2 and (evidence_a <= evidence_b or evidence_b <= evidence_a)


def dedupe_findings(findings):
    kept = []
    for finding in findings:
        evidence = set(finding.evidence)
        for index, existing in enumerate(kept):
            if _same_concern(evidence, set(existing.evidence)):
                bigger = finding if len(evidence) > len(existing.evidence) else existing
                strongest = max(_rank(finding), _rank(existing))
                merged = bigger.model_copy(deep=True)
                if strongest in _NAMES and _rank(merged) < strongest:
                    merged.severity = _NAMES[strongest]
                kept[index] = merged
                break
        else:
            kept.append(finding)
    return kept
