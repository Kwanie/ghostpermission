"""Compatibility adapters for Person A's parser and Person B's LangChain agents.

This module is the only place where differences in the teammates' interfaces
should be handled. The original agents and parser are not rewritten here.
"""
from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import Any, Callable, Mapping


def load_callable(module_name: str, function_name: str) -> Callable[..., Any]:
    """Import a callable by its module and attribute names."""
    module = importlib.import_module(module_name)
    function = getattr(module, function_name, None)
    if not callable(function):
        raise ImportError(
            f"{module_name}.{function_name} does not exist or is not callable. "
            "Check the actual module and symbol name."
        )
    return function


def load_object(module_name: str, object_name: str) -> Any:
    """Load an agent runnable, which may not itself be a Python function."""
    module = importlib.import_module(module_name)
    value = getattr(module, object_name, None)
    if value is None or not callable(getattr(value, "invoke", None)):
        raise ImportError(
            f"{module_name}.{object_name} was not found or does not expose invoke()."
        )
    return value


def _parameter_names(function: Callable[..., Any]) -> tuple[set[str], bool]:
    try:
        parameters = inspect.signature(function).parameters
    except (TypeError, ValueError):
        return set(), False
    names = set(parameters)
    accepts_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in parameters.values())
    return names, accepts_kwargs


def call_parser(
    parser_fn: Callable[..., Any],
    *,
    manifest_path: str | Path | None = None,
    manifest_xml: str | bytes | None = None,
) -> Any:
    """Call Person A's parser using its supported input style.

    Person A's app currently calls ``extract_permissions(xml_bytes)``. This
    adapter supports that form as well as common path- and text-based parsers.
    The manifest is read locally; this function does not send it to an API.
    """
    names, accepts_kwargs = _parameter_names(parser_fn)
    if manifest_xml is not None:
        text_or_bytes: str | bytes = manifest_xml
        if isinstance(text_or_bytes, str):
            encoded = text_or_bytes.encode("utf-8")
        else:
            encoded = text_or_bytes
        for key in ("xml_bytes", "content", "xml_content", "xml_text", "manifest_xml"):
            if key in names:
                value = encoded if key in {"xml_bytes", "content", "xml_content"} else text_or_bytes
                return parser_fn(**{key: value})
        if accepts_kwargs:
            return parser_fn(manifest_xml=text_or_bytes)
        return parser_fn(encoded)

    if manifest_path is not None:
        path = Path(manifest_path)
        for key in ("manifest_path", "file_path", "path", "xml_path"):
            if key in names:
                return parser_fn(**{key: str(path)})
        raw = path.read_bytes()
        for key in ("xml_bytes", "content", "xml_content"):
            if key in names:
                return parser_fn(**{key: raw})
        for key in ("xml_text", "manifest_xml"):
            if key in names:
                return parser_fn(**{key: raw.decode("utf-8", errors="strict")})
        if accepts_kwargs:
            return parser_fn(manifest_xml=raw.decode("utf-8", errors="strict"))
        return parser_fn(raw)

    raise ValueError("Supply manifest_path or manifest_xml.")


def json_safe(value: Any) -> Any:
    """Convert common structured-agent results into JSON-safe values."""
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return json_safe(value.model_dump())
    if hasattr(value, "dict") and callable(value.dict):
        return json_safe(value.dict())
    if isinstance(value, Mapping):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def adapt_langchain_agent(runnable: Any, agent_name: str) -> Callable[..., dict[str, Any]]:
    """Wrap Person B's existing ``prompt | agent_brain`` runnable.

    The prompt variables are taken from the original Person B files. This
    adapter intentionally passes only the minimum fields each prompt needs.
    """
    if not callable(getattr(runnable, "invoke", None)):
        raise TypeError(f"{agent_name} must expose an invoke() method.")

    def run_agent(**kwargs: Any) -> dict[str, Any]:
        permissions = list(kwargs.get("permissions") or [])
        app_purpose = str(kwargs.get("app_description") or "Not provided by the user.")
        if agent_name == "permission_mapper":
            payload = {"permissions": permissions}
        elif agent_name in {"purpose_analyst", "combination_analyst"}:
            payload = {"app_purpose": app_purpose, "permissions": permissions}
        elif agent_name == "skeptical_reviewer":
            drafts = {
                "deterministic_rule_findings": kwargs.get("rule_findings", []),
                "permission_analysis": json_safe(kwargs.get("permission_analysis")),
                "purpose_analysis": json_safe(kwargs.get("purpose_analysis")),
                "combination_analysis": json_safe(kwargs.get("combination_analysis")),
            }
            import json
            payload = {
                "app_purpose": app_purpose,
                "findings": json.dumps(drafts, ensure_ascii=False, default=str),
            }
        else:
            raise ValueError(f"Unknown GhostPermission agent adapter: {agent_name}")
        return json_safe(runnable.invoke(payload))

    return run_agent
