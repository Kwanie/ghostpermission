from typing import List, Dict, Any
from core.kb_loader import lookup_permission

def run_permission_mapper(permissions: List[str], llm=None) -> List[Dict[str, Any]]:
    """Maps raw permissions to plain-language descriptions using knowledge base and LLM."""
    mapped = []
    for perm in permissions:
        info = lookup_permission(perm)
        mapped.append({
            "permission": perm,
            "display_name": info.get("name"),
            "category": info.get("category"),
            "risk_level": info.get("risk_level"),
            "description": info.get("description"),
            "data_exposed": info.get("data_exposed", [])
        })
    return mapped