# File: app_helpers/ui_helpers.py
from typing import Any, Dict, List, Set
import streamlit as st
import re
from app_helpers.schema import load_schema, SCHEMA_PATH
from app_helpers.labels import GROUP_LABELS

# Utility casts

def _cast(val: Any, typ: type):
    return None if val is None else typ(val)

def is_transport_field(name: str) -> bool:
    return "_tt" in name.lower() or "transport_time" in name.lower()

def prettify(code_name: str) -> str:
    return code_name.replace("_", " ").title()

# Load and cache schema
schema: Dict[str, Dict[str, Any]] = load_schema(SCHEMA_PATH)

general_core: Dict[str, Dict[str, Any]] = {}
general_transport: Dict[str, Dict[str, Any]] = {}
machine_core: Dict[str, Dict[str, Dict[str, Any]]] = {}
machine_transport: Dict[str, Dict[str, Dict[str, Any]]] = {}

_MACHINE_NUM_RE = re.compile(r"^([A-Za-z&]+)(\d+)_([A-Za-z0-9_&]+)$")

# Categorize schema entries
for key, meta in schema.items():
    m = _MACHINE_NUM_RE.match(key)
    if m:
        prefix, num, field = m.groups()
        if prefix in GROUP_LABELS:
            mc = f"{prefix}{num}"
            bucket = machine_transport if is_transport_field(field) else machine_core
            bucket.setdefault(mc, {})[field] = {"key": key, "meta": meta}
        else:
            bucket = general_transport if is_transport_field(key) else general_core
            bucket[key] = meta
    else:
        bucket = general_transport if is_transport_field(key) else general_core
        bucket[key] = meta

# Fallback for unnumbered groups
for prefix in GROUP_LABELS:
    if prefix not in machine_core:
        grp_fields = {k: v for k, v in general_core.items() if k.startswith(prefix + "_")}
        if grp_fields:
            machine_core[prefix] = {}
            for k, m in grp_fields.items():
                field = k.split("_", 1)[1]
                machine_core[prefix][field] = {"key": k, "meta": m}
                del general_core[k]

all_machines: Set[str] = set(machine_core) | set(machine_transport)

def _machine_sort_key(code: str) -> int:
    m = re.search(r"(\d+)$", code)
    return int(m.group(1)) if m else 0

def _belongs_to_group(prefix: str, code: str) -> bool:
    if not code.startswith(prefix):
        return False
    suffix = code[len(prefix):]
    return suffix == "" or suffix[0].isdigit()

prefix_to_machines: Dict[str, List[str]] = {}
for prefix in GROUP_LABELS:
    machines = [mc for mc in all_machines if _belongs_to_group(prefix, mc)]
    machines.sort(key=_machine_sort_key)
    prefix_to_machines[prefix] = machines

# Map display labels back to prefixes
def _group_label(prefix: str) -> str:
    return GROUP_LABELS.get(prefix, prefix)

prefix_by_label: Dict[str, str] = { _group_label(p): p for p in GROUP_LABELS }

# Widget helper
def render_number_input(code_key: str, meta: Dict[str, Any]):
    label = meta.get("label") or prettify(code_key)
    num_type = float if meta["type"] == "float" else int
    min_val = _cast(meta.get("min"), num_type)
    max_val = _cast(meta.get("max"), num_type)
    default = _cast(meta.get("default"), num_type)
    if meta["type"] == "int":
        step, fmt = 1, "%d"
    else:
        rng = (max_val - min_val) if min_val is not None and max_val is not None else None
        step = num_type(round(rng/100,4)) if rng else num_type(0.01)
        fmt = "%f"
    initial = st.session_state["overrides"].get(code_key, st.session_state.get(code_key, default))
    return st.number_input(label, min_val, max_val, initial, step, format=fmt, key=code_key)

