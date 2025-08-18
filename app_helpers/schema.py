# # File: app_helpers/schema.py
# from __future__ import annotations
# from pathlib import Path
# import yaml
# import streamlit as st
# from typing import Dict, Any

# SCHEMA_PATH = Path(__file__).parent.parent / "config_schema.yml"

# @st.cache_data
# def load_schema(path: Path) -> Dict[str, Dict[str, Any]]:
#     with open(path, "r", encoding="utf-8") as f:
#         return yaml.safe_load(f)

# File: app.py
from __future__ import annotations
from pathlib import Path
import yaml
import streamlit as st
from typing import Dict, Any

# Paths for original and user-specific schema
ORIGINAL_PATH = Path(__file__).parent.parent / "config_schema.yml"
USER_PATH     = Path(__file__).parent.parent / "config_schema_user.yml"
# Expose SCHEMA_PATH for compatibility
SCHEMA_PATH   = USER_PATH

def ensure_user_schema_exists() -> None:
    """
    Create the user-writable schema copy if it doesn't exist.
    """
    if not USER_PATH.exists():
        USER_PATH.write_text(
            ORIGINAL_PATH.read_text(encoding="utf-8"),
            encoding="utf-8"
        )

@st.cache_data
def load_schema(path: Path = SCHEMA_PATH) -> Dict[str, Dict[str, Any]]:
    """
    Load the original schema, overlay defaults from the user copy, and cache.
    """
    # 1) load the pristine original
    orig = yaml.safe_load(ORIGINAL_PATH.read_text(encoding="utf-8"))
    # 2) ensure the writable user copy exists
    ensure_user_schema_exists()
    # 3) load user copy (may contain updated defaults)
    user = yaml.safe_load(path.read_text(encoding="utf-8"))

    # 4) overlay defaults from user copy into the pristine schema
    for key, entry in user.items():
        if key in orig and isinstance(entry, dict) and "default" in entry:
            orig[key]["default"] = entry["default"]

    return orig
