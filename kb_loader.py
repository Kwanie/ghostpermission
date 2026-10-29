import json
import os
from typing import Dict, Any

DEFAULT_KB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "permissions.json"
)

def load_permission_db(kb_path: str = DEFAULT_KB_PATH) -> Dict[str, Any]:
    """Loads the permission knowledge base JSON into memory."""
    if not os.path.exists(kb_path):
        return {}
    with open(kb_path, "r", encoding="utf-8") as f:
        return json.load(f)

def lookup_permission(permission_name: str, db: Dict[str, Any] = None) -> Dict[str, Any]:
    """Retrieves metadata for a given permission string, with safe defaults for unknown permissions."""
    if db is None:
        db = load_permission_db()
    
    if permission_name in db:
        return db[permission_name]
    
    # Fallback for undocumented/custom permissions
    clean_name = permission_name.split(".")[-1].replace("_", " ").title()
    return {
        "name": clean_name,
        "description": f"Custom or unlisted permission ({permission_name}).",
        "category": "Custom/Other",
        "risk_level": "Unknown",
        "data_exposed": ["Unspecified system resources"]
    }