# make_schema.py
import inspect, yaml
from config import SIM_TIME, INTERARRIVAL, network, Forklift_Capacity, WC_REJECT_INTERVAL, TT_FAIL_INTERVAL
# …import any other top-level constants you want…

schema = {}

# 1) Top-level single values
top_consts = {
    "SIM_TIME": SIM_TIME,
    "INTERARRIVAL": INTERARRIVAL,
    "Forklift_Capacity": Forklift_Capacity,
    "WC_REJECT_INTERVAL": WC_REJECT_INTERVAL,
    "TT_FAIL_INTERVAL": TT_FAIL_INTERVAL,
}
for name, val in top_consts.items():
    t = "int" if isinstance(val, int) else "float"
    default = val
    if t == "int":
        schema[name] = {"type": "int",   "default": default, "min": 0,    "max": default * 10}
    else:
        schema[name] = {"type": "float", "default": default, "min": 0.0,  "max": default * 10.0}

# 2) Per-machine in network
for node, params in network.items():
    if "process_time" in params:
        key = f"{node}_process_time"
        default = params["process_time"]
        schema[key] = {"type": "float", "default": default, "min": 0.0,       "max": default * 5.0}
    if "OEE" in params:
        key = f"{node}_OEE"
        default = params["OEE"]
        schema[key] = {"type": "float", "default": default, "min": 0.0,       "max": 1.0}
    if "transport_times" in params:
        tts = params["transport_times"]
        # normalize to list
        tlist = tts if isinstance(tts, list) else [tts]
        for i, t in enumerate(tlist, start=1):
            key = f"{node}_tt{i}"
            default = t
            schema[key] = {"type": "float", "default": default, "min": 0.0,   "max": default * 5.0}

# 3) Write out YAML
with open("config_schema.yml", "w") as f:
    yaml.safe_dump(schema, f, sort_keys=False)
print("Wrote config_schema.yml with", len(schema), "entries.")
