# plant_sim/run_sim.py
import simpy, random, pandas as pd
from . import config as cfg
import plant_sim.helpers as helpers
from .helpers import (
    init_queues,
    movement_log,
    wip_history,
    unit_record,
    log_move,
    log_wip,
    machine_status,
    downtime,
    status_history              
)
# from .config import Forklift_Capacity, SIM_TIME
# Removed unused TT_FAIL_INTERVAL import
from . import stage1, stage2, stage3, stage4, stage5, stage6
from plant_sim.helpers import build_utilisation_df


def run_sim(config: dict = None, progress_callback=None):
    
    import copy
    import plant_sim.config as cfg
    
    if config is None:
        config = {}
    
    # 1a) Determine which source of parameters to use
    use_cfg = (config is None)
    # 1b) Copy the network dict so we don’t clobber the global
    local_network = copy.deepcopy(cfg.network)
    
    # Monkey-patch the module so stages see our overrides
    cfg.network = local_network

    
    # ─── setup ─────────────────────────────────────────
    helpers.global_item_counter = 0
    movement_log.clear()
    wip_history.clear()
    unit_record.clear()
    status_history.clear()
    queues = init_queues(cfg.network)
    
    random.seed(42)
    env = simpy.Environment()
    
    # ── override global settings if passed in ────────────────────
    sim_time = config.get("SIM_TIME", cfg.SIM_TIME)
    interarrival = config.get("INTERARRIVAL", cfg.INTERARRIVAL)
    forklift_cap = config.get("Forklift_Capacity", cfg.Forklift_Capacity)
    wc_reject = config.get("WC_REJECT_INTERVAL", cfg.WC_REJECT_INTERVAL)
    tt_fail   = config.get("TT_FAIL_INTERVAL", cfg.TT_FAIL_INTERVAL)
    
#     helpers.forklifts = simpy.Resource(env, capacity=Forklift_Capacity)
    helpers.forklifts = simpy.Resource(env, capacity=forklift_cap)
    
    busy_time = { m: 0.0 for m in cfg.MACHINE_LIST } #PART OF STAGE5 INVESTIGATION
    
    #OEE DIAGNOSTIC 
#     def sentinel(env, name="NIH2"):
#         last_state = None
#         while True:
#             # look at the last recorded event for this machine
#             events = helpers.status_history.get(name, [])
#             if events:
#                 last_state = events[-1][1]  # True = up, False = down
#             print(f"[SENTINEL {env.now:.1f}] {name} up? {last_state}")
#             yield env.timeout(50)       # print every 500 min

#     env.process(sentinel(env))

    # initialize queues

    queues = init_queues(cfg.network)
    queues['WIPi_CL'] = []
    queues['WIPo_CL'] = []
    queues['WIPi_SAW'] = []
    queues['WIPo_SAW'] = []
    queues['test_feed'] = []  # Stage 4 feeder

    # stage buffers
    storage_after_press = []
    finished_goods      = []
    finished_goods2     = []
    finished_goods3     = []
    finished_goods4     = []
    finished_goods5     = []
    finished_goods6     = []

    # link buffers
    queues['storage_after_press'] = storage_after_press
    queues['finished_goods']      = finished_goods
    queues['finished_goods2']     = finished_goods2
    queues['finished_goods3']     = finished_goods3
    queues['finished_goods4']     = finished_goods4
    queues['finished_goods5']     = finished_goods5 
    queues['finished_goods6']     = finished_goods6


#     for name, props in cfg.network.items():
#         if "process_time" in props and "OEE" in props:
#             machine_status[name] = True
#             env.process(downtime(env, name, props['OEE']))

    for name, props in cfg.network.items():
        if "process_time" in props and "OEE" in props:
            if props['OEE'] > 0:
                machine_status[name] = True
                env.process(downtime(env, name, props['OEE']))
            else:
                machine_status[name] = False
#                 print(f"[INIT] {name} status set to {machine_status[name]}")
                
    # ── override each node’s process_time, OEE, and transport_times ──
    for node, props in local_network.items():
        # process_time
        key_pt = f"{node}_process_time"
        if key_pt in config:
            props["process_time"] = config[key_pt]

        # OEE
        key_oee = f"{node}_OEE"
        if key_oee in config:
            props["OEE"] = config[key_oee]

        # transport times: rename to list
        if "transport_times" in props:
            tt_list = props["transport_times"]
            tt_list = tt_list if isinstance(tt_list, list) else [tt_list]
            for i in range(len(tt_list)):
                key_tt = f"{node}_tt{i+1}"
                if key_tt in config:
                    tt_list[i] = config[key_tt]
            # write back
            props["transport_times"] = tt_list if len(tt_list)>1 else tt_list[0]
            

    # register stages
    stage1.build(env, cfg, queues, storage_after_press, finished_goods)
    stage2.build(env, cfg, queues, finished_goods, finished_goods2)
    stage3.build(env, cfg, queues, finished_goods2, finished_goods3)
    
    # set up your HDT⇄SPHDT token
    queues['hdt_token'] = simpy.Container(env, init=1, capacity=1)
    stage4.build(env, cfg, queues,
             finished_goods3=queues['finished_goods3'],
             finished_goods4=queues['finished_goods4'])
    
    
    stage5.build(env, cfg, queues,
                 finished_goods4=queues['finished_goods4'],
                 finished_goods5=queues['finished_goods5'])
    
    stage6.build(env, cfg, queues,
             finished_goods5=queues['finished_goods5'],
             finished_goods6=queues['finished_goods6'])
    



    # defect loop
    def wc_defect_loop(env):
        while True:
            yield env.timeout(cfg.WC_REJECT_INTERVAL)
            while not queues['WIPo_WC']:
                yield env.timeout(1)
            uid = queues['WIPo_WC'].pop(0)
            log_move(env, uid, 'WIPo_WC', 'rework_CL', 'reject')
            yield env.timeout(cfg.network['CL1']['process_time'])
            log_move(env, uid, 'rework_CL', 'WIPo_CL', 'rework_cut')
            t = cfg.network['WIPo_CL']['transport_times']
            t = t[0] if isinstance(t, list) else t
            yield env.timeout(t)
            queues['WIPi_WC'].append(uid)
            log_wip(env, 'WIPi_WC', queues)
            log_move(env, uid, 'WIPo_CL', 'WIPi_WC', 'rework_move')

    env.process(wc_defect_loop(env))

    # ─── run the simulation ────────────────────────────
#     env.run(until=cfg.SIM_TIME)
    # right before env.run(...)
    def _step_callback():
        if progress_callback:
            progress_callback(env.now / sim_time)

    # ─── run the simulation with progress reporting ──────────
#     if progress_callback:
#         orig_step = env.step
#         def step_and_report(*args, **kwargs):
#             result = orig_step(*args, **kwargs)
#             progress_callback(env.now / sim_time)
#             return result
#         env.step = step_and_report

#     env.run(until=sim_time)

#     # right before env.run(...)
#     if progress_callback:
#         next_report = sim_time * 0.05  # every 5%
#         orig_step    = env.step

#         def step_and_report(*args, **kwargs):
#             res = orig_step(*args, **kwargs)
#             now = env.now
#             nonlocal next_report
#             if now >= next_report:
#                 progress_callback(now / sim_time)
#                 next_report += sim_time * 0.05
#             return res

#         env.step = step_and_report
        
#     env.run(until=sim_time)

    # ─── run the simulation (with optional progress reporting) ─────────
    if progress_callback:
        orig_step   = env.step       # keep a reference to the real step()

        def step_and_report(*args, **kwargs):
            """Wrap env.step so we can ping the UI every time the clock moves."""
            result = orig_step(*args, **kwargs)          # advance sim
            if sim_time:                                # guard against /0
                progress_callback(env.now / sim_time)   # 0 → 1
            return result

        env.step = step_and_report                      # monkey-patch only for this run

    env.run(until=sim_time)                             # ← single official run call

    # ─── collect ending WIP counts ─────────────────────
    final_wip = {}
    for node, q in queues.items():
        if node.startswith("WIPo_") or node.startswith("WIPi_") or node == "hold":
            if isinstance(q, simpy.Store):
                count = len(q.items)
            else:
                count = len(q)
            final_wip[node] = count

    # ─── build DataFrames ──────────────────────────────
    df_units = pd.DataFrame([
        {
            "UnitID":        uid,
            "SAW":           rec.get("SAW"),
            "ArrivalTime":   rec.get("EntryTime"),
            #"Stage1Storage": rec.get("ExitTime"),
            "Cooling":       rec.get("Cooling"),
            "Stage1Storage": rec.get("FinalGoodsTime", ""),
            "Stage2Storage": rec.get("FinalStorageTime", ""), 
            "Stage3Storage": rec.get("FinalStorage2Time", ""),
            "Stage4Storage": rec.get("Stage4Storage", ""),   # only once
            "Stage5Storage": rec.get("Stage5Storage", ""),
            "Stage6Storage": rec.get("Stage6Storage", "")
        }
        for uid, rec in unit_record.items()
    ])
    
#     # Replace these names with your real df_units column names that should be floats:
#     float_cols = [
#         'Cooling',
#         'Stage1Storage',
#         'Stage2Storage',
#         'Stage3Storage',
#         'Stage4Storage',
#         'Stage5Storage',
#         'Stage6Storage'
#     ]

#     for c in float_cols:
#         # 1) Cast the column to string (in case any stray non‐string data sneaked in),
#         # 2) remove any commas/spaces if present (e.g. "1,234.56" → "1234.56"),
#         # 3) use pd.to_numeric to coerce to float—invalid parsing becomes NaN if something can't convert.
#         df_units[c] = pd.to_numeric(
#             df_units[c]
#                 .astype(str)
#                 .str.replace(',', '')    # remove any thousands‐separator commas
#                 .str.replace(' ', ''),   # remove any stray spaces
#             errors='coerce'
#         )

    # ─── safely coerce numeric columns only if they exist ─────────
    desired = [
        'Cooling',
        'Stage1Storage',
        'Stage2Storage',
        'Stage3Storage',
        'Stage4Storage',
        'Stage5Storage',
        'Stage6Storage'
    ]
    existing = [col for col in desired if col in df_units.columns]

    for c in existing:
        df_units[c] = pd.to_numeric(
            df_units[c]
                .astype(str)
                .str.replace(',', '')
                .str.replace(' ', ''),
            errors='coerce'
        )
    
    df_wip  = pd.DataFrame(wip_history)
#     df_move = pd.DataFrame(movement_log).sort_values("Time").reset_index(drop=True)
# Build movement log DataFrame, sorting only if Time exists
    df_move = pd.DataFrame(movement_log)
    if "Time" in df_move.columns:
        df_move = df_move.sort_values("Time").reset_index(drop=True)
    df_final_wip = (
        pd.DataFrame([{"Node": k, "EndingWIP": v} for k, v in final_wip.items()])
        .sort_values("Node").reset_index(drop=True)
    )

    # ─── console diagnostics ────────────────────────────
    print("\n--- df_units head ---");     print(df_units.head())
    print("\n--- df_wip head ---");       print(df_wip.head())
    print("\n--- df_move head ---");      print(df_move.head())
    print("\n--- Ending WIP in each WIP buffer ---");  print(df_final_wip)
    print("\n--- Finished stage 1 count:", len(finished_goods))
    print("\n--- Finished stage 2 count:",      len(finished_goods2))
    print("\n--- Finished stage 3 count:",      len(finished_goods3))
    print("--- Hold WIP count:",              len(queues.get('hold', [])))
    print("--- Finished stage 4 count:",      len(finished_goods4))
    print("--- Finished stage 5 count:",      len(finished_goods5))   # <─ new line
    print("--- Finished stage 6 count:", len(finished_goods6))   # ← add this

#     # ─── Stage-4 machine uptimes ───────────────────────
#     print("\n--- Stage 4 machine uptimes ---")
#     for machine in (
#         "PO1","PO2","PO3",
#         "HT","SPHDT","HDT",
#         "CUT1","CUT2","CUT3","CUT4",
#         "MTT","TT","HS"
#     ):
#         events = status_history.get(machine, [])
#         if len(events) < 2:
#             print(f"{machine:>5}: no downtime data")
#             continue

#         uptime = sum(
#             (t2 - t1)
#             for (t1, was_up), (t2, now_up) in zip(events, events[1:])
#             if was_up
#         )
#         util = uptime / env.now
#         print(f"{machine:>5}: {util:.0%} uptime")
        
    # ─── build machine-utilisation table ─────────────────────────────
#     df_move_std = (
#         df_move
#             .rename(columns=str.lower)           # Time→time, From→from, …
#             .rename(columns={"action": "event"})  # Action→event
#     )
#     df_util = build_utilisation_df(df_move_std, cfg.SIM_TIME)

#     # ─── build machine‐utilisation table safely ───────────────────
#     df_move_std = df_move.copy()
#     # only lowercase & rename if 'action' exists
#     if "action" in df_move_std.columns:
#         df_move_std = (
#             df_move_std
#               .rename(columns=str.lower)          # Time→time, From→from, …
#               .rename(columns={"action": "event"})# Action→event
#         )
#     else:
#         # ensure we have the right columns to avoid KeyErrors
# #         df_move_std["machine"] = []
# #         df_move_std["event"]   = []
# #         df_move_std["time"]    = []

#         df_move_std["machine"] = pd.NA
#         df_move_std["event"]   = pd.NA
#         df_move_std["time"]    = pd.NA

#     # only build utilisation if we have events logged
#     if "event" in df_move_std.columns and not df_move_std.empty:
#         # use sim_time (overrides) rather than raw cfg.SIM_TIME
#         df_util = build_utilisation_df(df_move_std, sim_time)
#     else:
#         # return an empty utilisation DataFrame with expected schema
#         df_util = pd.DataFrame(
#             columns=["machine", "busy_time", "available", "utilisation"]
#         )

#     # quick peek (comment out if you don’t want the noise)
#     print("\n--- Machine Utilisation (head) ---")
#     print(df_util.head())

    # ─── build machine‐utilisation table ─────────────────────────────
    df_move_std = pd.DataFrame(movement_log).sort_values("Time").reset_index(drop=True)
    df_util      = build_utilisation_df(df_move_std, sim_time)
    # ── Ensure every enabled machine (OEE>0) appears, even if idle ─────────────
    enabled = [m for m, props in cfg.network.items() if props.get("OEE", 0) > 0]

    present  = set(df_util["machine"])
    missing  = [m for m in enabled if m not in present]

    if missing:
        df_util = pd.concat(
            [
                df_util,
                pd.DataFrame(
                    {
                        "machine":     missing,
                        "busy_time":   0.0,
                        "available":   sim_time,   # whole window was available
                        "utilisation": 0.0,
                    }
                ),
            ],
            ignore_index=True,
        )

    # ─── return all outputs ──────────────────────────────────────────
    return (
        df_units,
        df_wip,
        df_move,
        df_final_wip,
        df_util,               # ← utilisation DF now part of the return
        finished_goods,
        finished_goods2,
        finished_goods3,
        finished_goods4,
        finished_goods5,
        finished_goods6
    )


# ─────────────────────────── script entry point ─────────────────────────
if __name__ == "__main__":
    (
        df_units,
        df_wip,
        df_move,
        df_final_wip,
        df_util,
        finished_goods,
        finished_goods2,
        finished_goods3,
        finished_goods4,
        finished_goods5,
        finished_goods6      # finished_goods lists
    ) = run_sim()
    
    # run one replication
    df_units, df_wip, df_move, df_final_wip, df_util, *rest = run_sim()

    print("\n=== Machine Utilisation ===")
    print(df_util.to_string(index=False))
    df_util.to_csv("machine_utilisation.csv", index=False)

    # ─── quick sanity check for one machine ────────────────────────────
    import plant_sim.helpers as helpers      # ✔ correct import
    sim_time = helpers.cfg.SIM_TIME
    m = "PDB1"                               # machine to inspect

    # first start time = sim_time - 'available' column
    first_start = sim_time - df_util.set_index("machine").loc[m, "available"]
    busy        = df_util.set_index("machine").loc[m, "busy_time"]

    events   = helpers.status_history.get(m, [])
    n_breaks = sum(not up for _, up in events)

    print(f"\n--- Diagnostic for {m} ---")
    print(f"breakdowns in this run : {n_breaks}")
    print(f"first start at         : {first_start:.1f} min")
    print(f"busy_time              : {busy:.1f} min")
    print(f"available_window       : {sim_time - first_start:.1f} min")
    print(f"measured utilisation   : {busy / (sim_time - first_start):.3f}")
    print(f"configured OEE         : {helpers.cfg.network[m]['OEE']}")

    
    
#     run_sim()
    
#     df_util = build_utilisation_df(df_move, SIM_TIME)
#     print("\n=== Machine Utilisation ===")
#     print(df_util.to_string(index=False))
#     df_util.to_csv("machine_utilisation.csv", index=False)
    




# # plant_sim/run_sim.py

# import simpy, random, pandas as pd
# from . import config as cfg
# import plant_sim.helpers as helpers
# from .helpers import (
#     init_queues,
#     movement_log,
#     wip_history,
#     unit_record,
#     log_move,
#     log_wip,
#     machine_status,
#     downtime,
#     status_history               
# )
# from .config import Forklift_Capacity
# from . import stage1, stage2, stage3, stage4, stage5


# def run_sim():
#     # ─── setup ─────────────────────────────────────────
#     helpers.global_item_counter = 0
#     movement_log.clear()
#     wip_history.clear()
#     unit_record.clear()
#     status_history.clear()
    
#     random.seed(42)
#     env = simpy.Environment()
#     helpers.forklifts = simpy.Resource(env, capacity=Forklift_Capacity)
    
#     # initialize queues
#     queues = init_queues(cfg.network)
#     queues['test_feed'] = []  # Stage 4 feeder

#     # stage buffers
#     storage_after_press = []
#     finished_goods      = []
#     finished_goods2     = []
#     finished_goods3     = []
#     finished_goods4     = []
#     finished_goods5     = []

#     # link buffers
#     queues['storage_after_press'] = storage_after_press
#     queues['finished_goods']      = finished_goods
#     queues['finished_goods2']     = finished_goods2
#     queues['finished_goods3']     = finished_goods3
#     queues['finished_goods4']     = finished_goods4
#     queues['finished_goods5']     = finished_goods5 

#     # OEE / downtime setup
#     for name, props in cfg.network.items():
#         if "process_time" in props and "OEE" in props:
#             if props['OEE'] > 0:
#                 machine_status[name] = True
#                 env.process(downtime(env, name, props['OEE']))
#             else:
#                 machine_status[name] = False
#                 print(f"[INIT] {name} status set to {machine_status[name]}")

#     # register stages
#     stage1.build(env, cfg, queues, storage_after_press, finished_goods)
#     stage2.build(env, cfg, queues, finished_goods, finished_goods2)
#     stage3.build(env, cfg, queues, finished_goods2, finished_goods3)
    
#     # set up HDT⇄SPHDT token for Stage 4
#     queues['hdt_token'] = simpy.Container(env, init=1, capacity=1)
#     stage4.build(env, cfg, queues,
#                  finished_goods3=queues['finished_goods3'],
#                  finished_goods4=queues['finished_goods4'])
    
#     stage5.build(env, cfg, queues,
#                  finished_goods4=queues['finished_goods4'],
#                  wipi_ut=queues.get('WIPi_UT', []),
#                  machine_status=machine_status)

#     # defect loop (unchanged)
#     def wc_defect_loop(env):
#         while True:
#             yield env.timeout(cfg.WC_REJECT_INTERVAL)
#             while not queues['WIPo_WC']:
#                 yield env.timeout(1)
#             uid = queues['WIPo_WC'].pop(0)
#             log_move(env, uid, 'WIPo_WC', 'rework_CL', 'reject')
#             yield env.timeout(cfg.network['CL1']['process_time'])
#             log_move(env, uid, 'rework_CL', 'WIPo_CL', 'rework_cut')
#             t = cfg.network['WIPo_CL']['transport_times']
#             t = t[0] if isinstance(t, list) else t
#             yield env.timeout(t)
#             queues['WIPi_WC'].append(uid)
#             log_wip(env, 'WIPi_WC', queues)
#             log_move(env, uid, 'WIPo_CL', 'WIPi_WC', 'rework_move')

#     env.process(wc_defect_loop(env))

#     # ─── run the simulation ────────────────────────────
#     env.run(until=cfg.SIM_TIME)

#     # ─── collect ending WIP counts ─────────────────────
#     final_wip = {}
#     for node, q in queues.items():
#         if node.startswith("WIPo_") or node.startswith("WIPi_") or node == "hold":
#             if isinstance(q, simpy.Store):
#                 count = len(q.items)
#             else:
#                 count = len(q)
#             final_wip[node] = count

#     # ─── build DataFrames ──────────────────────────────
#     df_units = pd.DataFrame([
#         {
#             "UnitID":        uid,
#             "SAW":           rec.get("SAW"),
#             "ArrivalTime":   rec.get("EntryTime"),
#             "Cooling":       rec.get("Cooling"),
#             "Stage1Storage": rec.get("FinalGoodsTime", ""),
#             "Stage2Storage": rec.get("FinalStorageTime", ""), 
#             "Stage3Storage": rec.get("FinalStorage2Time", ""),
#             "Stage4Storage": rec.get("Stage4Storage", ""),
#             "Stage5Storage": rec.get("Stage5Storage", "")
#         }
#         for uid, rec in unit_record.items()
#     ])
    
#     # Convert these columns to float so decimal="," works in to_csv:
#     float_cols = [
#         'ArrivalTime',
#         'Cooling',
#         'Stage1Storage',
#         'Stage2Storage',
#         'Stage3Storage',
#         'Stage4Storage',
#         'Stage5Storage',
#     ]

#     for c in float_cols:
#         df_units[c] = pd.to_numeric(
#             df_units[c]
#                 .astype(str)
#                 .str.replace(',', '')    # remove any thousands‐separator commas
#                 .str.replace(' ', ''),   # remove any stray spaces
#             errors='coerce'
#         )
    
#     df_wip  = pd.DataFrame(wip_history)
#     df_move = pd.DataFrame(movement_log).sort_values("Time").reset_index(drop=True)
#     df_final_wip = (
#         pd.DataFrame([{"Node": k, "EndingWIP": v} for k, v in final_wip.items()])
#         .sort_values("Node").reset_index(drop=True)
#     )

#     # ─── console diagnostics ────────────────────────────
#     print("\n--- df_units head ---")
#     print(df_units.head())
#     print("\n--- df_wip head ---")
#     print(df_wip.head())
#     print("\n--- df_move head ---")
#     print(df_move.head())
#     print("\n--- Ending WIP in each WIP buffer ---")
#     print(df_final_wip)
#     print("\n--- Finished stage 1 count:", len(finished_goods))
#     print("\n--- Finished stage 2 count:",      len(finished_goods2))
#     print("\n--- Finished stage 3 count:",      len(finished_goods3))
#     print("--- Hold WIP count:",              len(queues.get('hold', [])))
#     print("--- Finished stage 4 count:",      len(finished_goods4))
#     print("--- Finished stage 5 count:",      len(finished_goods5))

#     # ─── Stage 4 machine uptimes ───────────────────────
#     print("\n--- Stage 4 machine uptimes ---")
#     for machine in (
#         "PO1","PO2","PO3",
#         "HT","SPHDT","HDT",
#         "CUT1","CUT2","CUT3","CUT4",
#         "MTT","TT","HS"
#     ):
#         events = status_history.get(machine, [])
#         if len(events) < 2:
#             print(f"{machine:>5}: no downtime data")
#             continue

#         uptime = sum(
#             (t2 - t1)
#             for (t1, was_up), (t2, now_up) in zip(events, events[1:])
#             if was_up
#         )
#         util = uptime / env.now
#         print(f"{machine:>5}: {util:.0%} uptime")

#     # ─── Stage 5 machine uptimes ───────────────────────
#     print("\n--- Stage 5 machine uptimes ---")
#     for machine in (
#         # FO machines
#         "FO1","FO2","FO3","FO4",
#         # UT & SR1
#         "UT","SR1",
#         # DB machines
#         "DB1","DB2","DB3","DB4","DB5","DB6",
#         # KN machines
#         "KN1","KN2",
#         # PDB machines
#         "PDB1","PDB2",
#         # FC machines
#         "FC1","FC2","FC3",
#         # SP1
#         "SP1"
#     ):
#         events = status_history.get(machine, [])
#         if len(events) < 2:
#             print(f"{machine:>5}: no downtime data")
#             continue

#         uptime = sum(
#             (t2 - t1)
#             for (t1, was_up), (t2, now_up) in zip(events, events[1:])
#             if was_up
#         )
#         util = uptime / env.now
#         print(f"{machine:>5}: {util:.0%} uptime")

#     # ─── return all outputs ─────────────────────────────
#     return (
#         df_units,
#         df_wip,
#         df_move,
#         df_final_wip,
#         finished_goods,
#         finished_goods2,
#         finished_goods3,
#         finished_goods4,
#         finished_goods5
#     )


# if __name__ == "__main__":
#     run_sim()
