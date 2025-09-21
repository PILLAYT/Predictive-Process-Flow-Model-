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
    
    # NEW: run-mode + progress settings
    run_mode    = str(config.get("RUN_MODE", getattr(cfg, "RUN_MODE", "time"))).lower()
    desired_units = config.get("DESIRED_UNITS", getattr(cfg, "DESIRED_UNITS", None))
    max_time      = config.get("MAX_TIME", getattr(cfg, "MAX_TIME", sim_time))
    warmup_est    = config.get("WARMUP_ESTIMATE", getattr(cfg, "WARMUP_ESTIMATE", 30))
    warmup_frac   = config.get("PROGRESS_WARMUP_FRACTION", getattr(cfg, "PROGRESS_WARMUP_FRACTION", 0.25))

    # Basic validation (fail fast, clear)
    if run_mode not in ("time", "units", "auto"):
        raise ValueError("RUN_MODE must be 'time', 'units', or 'auto'.")

    if run_mode == "time":
        if not sim_time or sim_time <= 0:
            raise ValueError("RUN_MODE='time' requires SIM_TIME > 0.")
    elif run_mode == "units":
        if not desired_units or desired_units <= 0:
            raise ValueError("RUN_MODE='units' requires DESIRED_UNITS > 0.")
        if not max_time or max_time <= 0:
            raise ValueError("RUN_MODE='units' requires MAX_TIME > 0 (safety cap).")
    else:  # "auto"
        if (not sim_time or sim_time <= 0) and (not desired_units or desired_units <= 0):
            raise ValueError("RUN_MODE='auto' needs at least SIM_TIME>0 or DESIRED_UNITS>0.")
    
#     helpers.forklifts = simpy.Resource(env, capacity=Forklift_Capacity)
    helpers.forklifts = simpy.Resource(env, capacity=forklift_cap)
    
    busy_time = { m: 0.0 for m in cfg.MACHINE_LIST } #PART OF STAGE5 INVESTIGATION
    

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


#     # ─── run the simulation (with optional progress reporting) ─────────
#     if progress_callback:
#         orig_step   = env.step       # keep a reference to the real step()

#         def step_and_report(*args, **kwargs):
#             """Wrap env.step so we can ping the UI every time the clock moves."""
#             result = orig_step(*args, **kwargs)          # advance sim
#             if sim_time:                                # guard against /0
#                 progress_callback(env.now / sim_time)   # 0 → 1
#             return result

#         env.step = step_and_report                      # monkey-patch only for this run

#     env.run(until=sim_time)                             # ← single official run call

    # ─── progress model (time vs two-phase units) ──────────────────────────────
    use_units_progress = (run_mode == "units") or (run_mode == "auto" and desired_units and desired_units > 0)

    if progress_callback:
        orig_step = env.step

        def step_and_report(*args, **kwargs):
            res = orig_step(*args, **kwargs)

            # compute progress per mode
            prog = 0.0
            if use_units_progress and desired_units and desired_units > 0:
                elapsed = env.now
                produced = len(finished_goods6)

                if produced <= 0:
                    # warm-up segment (0 → warmup_frac)
                    if warmup_est and warmup_est > 0:
                        prog = min(elapsed / float(warmup_est), 1.0) * float(warmup_frac)
                    else:
                        prog = 0.0
                else:
                    # main segment (warmup_frac → 1.0)
                    unit_frac = min(float(produced) / float(desired_units), 1.0)
                    prog = float(warmup_frac) + (1.0 - float(warmup_frac)) * unit_frac
            else:
                # time mode (or auto without units target)
                if sim_time and sim_time > 0:
                    prog = min(env.now / float(sim_time), 1.0)
                else:
                    prog = 0.0

            if prog < 0.0: prog = 0.0
            if prog > 1.0: prog = 1.0
            try:
                progress_callback(prog)
            except Exception:
                pass  # keep the sim running even if UI callback fails

            return res

        env.step = step_and_report

    # ─── stop policy (time, units, or auto) ───────────────────────────────────
    stop_reason = "unknown"

    if run_mode == "time":
        end_evt = env.timeout(sim_time)
        env.run(until=end_evt)
        stop_reason = "time_cap"

    elif run_mode == "units":
        # target watcher
        units_evt = env.event()
        def _goal_watcher(e):
            while len(finished_goods6) < desired_units:
                yield e.timeout(1)
            if not units_evt.triggered:
                units_evt.succeed()
        env.process(_goal_watcher(env))

        time_cap_evt = env.timeout(max_time)
        combined = simpy.events.AnyOf(env, [units_evt, time_cap_evt])
        env.run(until=combined)
        # which one fired?
        stop_reason = "units_target" if units_evt in combined.value else "safety_cap"

    else:  # run_mode == "auto"
        events = []
        units_evt = None
        time_cap_evt = None

        if desired_units and desired_units > 0:
            units_evt = env.event()
            def _goal_watcher(e):
                while len(finished_goods6) < desired_units:
                    yield e.timeout(1)
                if not units_evt.triggered:
                    units_evt.succeed()
            env.process(_goal_watcher(env))
            events.append(units_evt)

        if sim_time and sim_time > 0:
            time_cap_evt = env.timeout(sim_time)
            events.append(time_cap_evt)

        if len(events) == 1:
            env.run(until=events[0])
            stop_reason = "units_target" if units_evt and events[0] is units_evt else "time_cap"
        else:
            combined = simpy.events.AnyOf(env, events)
            env.run(until=combined)
            if units_evt and (units_evt in combined.value):
                stop_reason = "units_target"
            elif time_cap_evt and (time_cap_evt in combined.value):
                stop_reason = "time_cap"
            else:
                stop_reason = "unknown"
                
                
    # after the run completes
    actual_elapsed = env.now
    produced_units = len(finished_goods6)
    throughput_rph = (produced_units / (actual_elapsed / 60.0)) if actual_elapsed > 0 else None


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


    # ─── build machine‐utilisation table ─────────────────────────────
    df_move_std = pd.DataFrame(movement_log)
    if "Time" in df_move_std.columns:
        df_move_std = df_move_std.sort_values("Time").reset_index(drop=True)
    df_util = build_utilisation_df(df_move_std, actual_elapsed)
    
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
                        "available":   actual_elapsed,   # use actual elapsed
                        "utilisation": 0.0,
                    }
                ),
            ],
            ignore_index=True,
        )

    # ─── return all outputs ──────────────────────────────────────────
    
    run_meta = {
        "mode": run_mode,
        "targets": {
            "sim_time": sim_time,
            "desired_units": desired_units,
            "max_time": max_time,
            "warmup_estimate": warmup_est,
            "warmup_fraction": warmup_frac,
        },
        "progress_model": "two_phase_units" if use_units_progress else "time_fraction",
        "stop_reason": stop_reason,
        "elapsed_time": actual_elapsed,               # total elapsed
        "first_stage6_time": first_stage6_time,       # when the first unit hit Stage-6 (sim minutes)
        "elapsed_since_first": elapsed_since_first,   # window for the new throughput
        "produced_units": produced_units,
        "throughput_rph": throughput_rph,             # NEW: since the first Stage-6 unit
        "throughput_rph_since_start": throughput_rph_since_start,  # legacy/reference
    }
    
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
        finished_goods6,
        run_meta
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

    
    