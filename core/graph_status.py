"""Which permissions did the findings flag? Pure logic, kept apart from the drawing code so it can be tested."""

# status -> (legend text, marker shape, colour). Shape AND colour AND legend all say the same thing,
# so the picture still works for people who cannot tell the colours apart.
STATUS_STYLE = {
    "high":      ("Needs attention (high)",       "diamond",     "#ef4444"),
    "review":    ("Worth a closer look (review)", "triangle-up", "#f59e0b"),
    "justified": ("Explained by the description", "square",      "#10b981"),
    "ok":        ("No finding mentions it",       "circle",      "#60a5fa"),
    "unchecked": ("Not checked yet",              "circle-open", "#9ca3af"),
}
_RANK = {"ok": 0, "justified": 1, "review": 2, "high": 3}


def _field(finding, name):
    return finding.get(name) if isinstance(finding, dict) else getattr(finding, name, None)


def permission_statuses(permissions, findings):
    """{permission: status}. With findings=None every permission is 'unchecked'.

    A permission is only 'ok' when NO finding mentions it. A finding with an unfamiliar severity word still
    counts as 'review', so the picture never says 'no concern' about something we flagged."""
    if findings is None:
        return {p: "unchecked" for p in permissions}
    status = {p: "ok" for p in permissions}
    for finding in findings:
        severity = str(_field(finding, "severity") or "").lower()
        if "high" in severity:
            level = "high"
        elif "justified" in severity:
            level = "justified"
        else:
            level = "review"
        for item in (_field(finding, "evidence") or []):
            if item in status and _RANK[level] > _RANK[status[item]]:
                status[item] = level
    return status
