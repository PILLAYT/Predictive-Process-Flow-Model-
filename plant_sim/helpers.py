# plant_sim/helpers.py
import random
from collections import defaultdict
import pandas as pd
import numpy as np   
from typing import Optional 

PRINT_MOVES = False

# ---- globally shared collectors / utils ---------------------------
global_item_counter = 0
unit_record = defaultdict(lambda: {
    "SAW": None,
    "EntryTime": None,
    "ExitTime": None,
    "Cooling": None,
    "Stage1Storage": None,
    "Stage2Storage": None,
    "PressDiverts": 0,
    "Scrapped": False 
})
movement_log = []    # every movement record
wip_history = []     # list of {'Time','Node','WIP'}

# track machine on/off status and history
machine_status = {}
status_history = defaultdict(list)
# forklifts = None 

# --------------------------------------------------------------------
def init_queues(network):
    """Initialize an empty queue list for each node in the network."""
    return {name: [] for name in network.keys()}

# --------------------------------------------------------------------
def log_wip(env, node, queues):
    wip_history.append({
        "Time": env.now,
        "Node": node,
        "WIP": len(queues[node])
    })

# --------------------------------------------------------------------
def log_move(env, uid, src, dest, action):
    movement_log.append({
        "Time":   env.now,
        "UnitID": uid,
        "From":   src,
        "To":     dest,
        "Action": action
    })
    if PRINT_MOVES:
        print(f"[{env.now:6.1f}] {uid:>6}  {action:<8}  {src:>22} → {dest}")

# --------------------------------------------------------------------
# def downtime(env, machine, OEE, mttf=50.0):
#     """
#     Toggle machine_status on/off so long-run availability ≈ OEE.
#     Records timestamped up/down events in status_history.
#     """
#     mttr = mttf * (1 - OEE) / OEE
#     # start up
#     machine_status[machine] = True
#     status_history[machine].append((env.now, True))
#     while True:
#         # up-time
#         yield env.timeout(random.expovariate(1 / mttf))
#         machine_status[machine] = False
#         status_history[machine].append((env.now, False))
#         # down-time
#         yield env.timeout(random.expovariate(1 / mttr))
#         machine_status[machine] = True
#         status_history[machine].append((env.now, True))

downtime_log = {}

def downtime(env, machine_name, OEE):
    if OEE >= 1.0 or OEE <= 0:
        return

    uptime = 1000 * OEE
    downtime_duration = 1000 * (1 - OEE)

    if machine_name not in status_history:
        status_history[machine_name] = []

    # Machine starts as "up"
    status_history[machine_name].append((env.now, True))

    while True:
        yield env.timeout(uptime)
        status_history[machine_name].append((env.now, False))  # going down

        yield env.timeout(downtime_duration)
        status_history[machine_name].append((env.now, True))   # back up
        
def machine_processor(env, name, cfg, queues):
    """
    Repeatedly:
      1) wait until (`queues[cfg.MACHINE_INPUT[name]]` has a unit)
      2) pop one unit
      3) process for tc = cfg.MACHINE_TC[name]
      4) push the finished unit into (`WIPo_<name>`)
    """
    input_q = cfg.MACHINE_INPUT[name]
    output_q = cfg.MACHINE_OUTPUT[name]    # or however you name them
    tc = cfg.MACHINE_TC[name]

    while True:
        # 1) Wait until there is something to process
        if not queues[input_q] or not machine_status.get(name, True):
            yield env.timeout(0.1)
            continue

        uid = queues[input_q].pop(0)
        log_move(env, uid, input_q, name, 'start')
        
        # 2) Process for tc time
        yield env.timeout(tc)
        
        # 3) Record that unit is done
        log_move(env, uid, name, output_q, 'end')
        queues[output_q].append(uid)
        


# helpers.py  (or wherever batch_move is defined)
from .helpers import unit_record


def batch_move(env,
               wipo: str,
               queues: dict,
               dests: list,
               tts,
               batch_size: int = 42,
               poll: float = 0.05,
               stamp_field: Optional[str] = None):
    """
    Move one full pallet from `wipo` to the least-loaded dest.
    If `stamp_field` is given, write env.now into
        unit_record[uid][stamp_field]
    for every shell in that pallet.
    """
    if not isinstance(tts, list):
        tts = [tts] * len(dests)

    while True:
        if len(queues[wipo]) >= batch_size:
            idx  = min(range(len(dests)), key=lambda i: len(queues[dests[i]]))
            dest = dests[idx]
            pallet = [queues[wipo].pop(0) for _ in range(batch_size)]

            with forklifts.request() as req:
                yield req
                yield env.timeout(tts[idx])

            queues[dest].extend(pallet)
            log_wip(env, dest, queues)

            for uid in pallet:
                if stamp_field is not None:
                    unit_record[uid][stamp_field] = env.now    # ★ new line
                log_move(env, uid, wipo, dest, "batch")
        else:
            yield env.timeout(poll)


def build_utilisation_df(
        df_move: pd.DataFrame,
        sim_time: float,
        finish_labels=("finish", "end", "done", "complete", "destroy"),
    ) -> pd.DataFrame:
    """
    Utilisation = busy_time / (sim_time − first_start_time)

    * busy_time is accumulated even when multiple `start` events overlap on the
      same machine (depth counter).
    * If a `start` and a `finish` share the same timestamp, the `finish`
      is processed first so elapsed time is never lost.
    """

    # ── 1  normalise column names & labels ─────────────────────────────
    df = (df_move
            .rename(columns=str.lower)            # Time→time, …
            .rename(columns={"action": "event"})
            .copy())
    df["event"] = [str(x).lower() for x in df["event"]]

    # ── 1a  stable sort: finish before start at identical Time ─────────
    _order = {lbl: 0 for lbl in finish_labels}
    _order.update({"start": 1})
    df["order"] = df["event"].map(_order).fillna(2)
    df.sort_values(["time", "order"], inplace=True)
    df.drop(columns="order", inplace=True)

    # ── 2  discover real machines (at least one start & one finish) ────
    starts   = set(df.loc[df["event"] == "start",  "to"])
    finishes = set(df.loc[df["event"].isin(finish_labels), "from"])
    machines = (starts & finishes) - {np.nan}

    # ── 3  keep only rows for those machines & wanted events ───────────
    df["machine"] = np.where(df["event"] == "start", df["to"], df["from"])
    df = df[
        df["machine"].isin(machines)
        & df["event"].isin(("start",) + finish_labels)
    ]

    # ── 4  first-start time & busy accumulation (depth counter) ────────
    first_start = dict.fromkeys(machines, None)
    busy_time   = defaultdict(float)
    depth       = defaultdict(int)
    entered     = {}                         # timestamp when depth→1

    for _, r in df.iterrows():
        m, evt, t = r["machine"], r["event"], r["time"]

        if evt == "start":
            if first_start[m] is None:
                first_start[m] = t
            if depth[m] == 0:
                entered[m] = t
            depth[m] += 1

        else:  # finish / end / done / complete
            if depth[m] > 0:
                depth[m] -= 1
                if depth[m] == 0:           # machine just became idle
                    busy_time[m] += t - entered.pop(m, t)

    # ── 5  build result table incl. zero-busy machines ─────────────────
    records = []
    for m in sorted(machines):
        t0     = first_start[m]
        avail  = max(sim_time - t0, 0) if t0 is not None else 0
        bt     = busy_time.get(m, 0.0)
        util   = (bt / avail) if avail > 0 else 0.0
        records.append({
            "machine":     m,
            "busy_time":   bt,
            "available":   avail,
            "utilisation": util,
            "util_%":      round(util * 100, 1)
        })

    return pd.DataFrame(records)