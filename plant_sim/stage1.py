# # plant_sim/stage1.py

# import simpy, sys, pathlib, uuid
# from plant_sim import helpers as h
# from plant_sim import config as cfg

# # ensure helpers & config resolve (assumes notebook sits with them or one level up)
# if not pathlib.Path('helpers.py').exists():
#     sys.path.append('..')

# from .helpers import machine_status

# # clean previous runs
# h.movement_log.clear()
# h.wip_history.clear()
# h.unit_record.clear()


# # ------------------ parameters (unchanged) ------------------

# SIM_TIME        = 20_000
# CONVEYOR_CAP    = 100
# PAUSE_LEVEL     = 100
# RESUME_LEVEL    = 50
# THROTTLE        = True
# SB1_TIME        = cfg.network['SB1']['process_time']
# FORKLIFT_COUNT  = 2
# PALLET_SIZE     = 42
# POLL            = 0.01

# # map which IH feeds which Press
# IH_TO_PRESS     = {"IH1": "P1", "IH2": "P1", "IH3": "P2"}


# def move(env, wipo, queues, dests, tts):
#     """One-by-one transporter (round-robin to shortest queue)."""
#     if not isinstance(tts, list):
#         tts = [tts] * len(dests)

#     while True:
#         if queues[wipo]:
#             active_dest_pairs = [
#                 (d, t) for d, t in zip(dests, tts)
#                 if h.machine_status.get(d, True)
#             ]
#             if not active_dest_pairs:
#                 yield env.timeout(0.05)
#                 continue

#             dest, t_trans = min(active_dest_pairs,
#                                 key=lambda pair: len(queues[pair[0]]))
#             uid = queues[wipo].pop(0)
#             yield env.timeout(t_trans)
#             queues[dest].append(uid)
#             h.log_wip(env, dest, queues)
#             h.log_move(env, uid, wipo, dest, 'transport')
#         else:
#             yield env.timeout(0.05)


# def build(env, cfg, queues, storage_after_press, finished_goods):
#     """
#     Stage 1 build: SAW → IH → Press → CL → Conveyor.

#     • We remove all WIPi_SAW* queues. Each SAWn
#       will “create” a new shell as soon as it’s free.
#     • After processing, SAWn pushes to WIPo_SAWn; the
#       move(env,…) calls carry that to IH inputs.
#     • CL is still regulated (via regulated_cl) so that
#       Stage 4→Stage 1 loopback can feed CL properly.
#     """

#     # ─── 1) DOWNTIME / MACHINE‐STATUS SETUP ────────────────────────────────
#     h.machine_status.clear()
#     for m_name, data in cfg.network.items():
#         if "OEE" not in data:
#             continue
#         h.machine_status[m_name] = (data["OEE"] > 0)
#         if data["OEE"] > 0:
#             env.process(h.downtime(env, m_name, data["OEE"]))

#     # ─── 2) INITIALIZE QUEUES ──────────────────────────────────────────────
# #     queues.clear()
# #     queues.update(h.init_queues(cfg.network))

#     # Ensure these Stage 1–specific buffers exist as plain lists:
#     for q in [
#         # SAW output buffers (no WIPi_SAW anymore)
#         'WIPo_SAW1','WIPo_SAW2','WIPo_SAW3','WIPo_SAW4','WIPo_SAW5',
#         # IH
#         'WIPi_IH1','WIPo_IH1',
#         'WIPi_IH2','WIPo_IH2',
#         'WIPi_IH3','WIPo_IH3',
#         # Press
#         'WIPi_P1','WIPo_P1',
#         'WIPi_P2','WIPo_P2',
#         # storage_after_press holds (uid,release_time)
#         'storage_after_press',
#         # CL conveyor
#         'WIPo_CL','WIPi_CL',
#         # Press→hold and scrap
#         'hold_P1','hold_P2','scrap_press',
#         # SB1 buffers
#         'WIPi_SB1','WIPo_SB1',
#         # finished goods
#         'finished_goods'
#     ]:
#         queues[q] = []

#     # expose for debugging if needed
#     env.queues = queues
#     env.storage_after_press = storage_after_press

#     # forklift resource
#     h.forklifts = simpy.Resource(env, capacity=FORKLIFT_COUNT)

#     # ─── 3) SAW PROCESSORS (no WIPi_SAW queue) ───────────────────────────
#     def saw_processor(env, name, pt):
#         """
#         Each SAWn “pulls” a brand-new shell as soon as it finishes its prior one.
#         After processing, push into WIPo_SAWn.
#         """
#         out_q = f'WIPo_{name}'
#         while True:
#             if h.machine_status.get(name, True):
#                 # Create a new unit immediately
#                 h.global_item_counter += 1
#                 uid = f"U{h.global_item_counter}"
#                 h.unit_record[uid]['SAW'] = env.now
#                 h.log_move(env, uid, '', name, 'create')

#                 # Process on SAWn
#                 h.log_move(env, uid, name, name, 'start')
#                 yield env.timeout(pt)
#                 h.unit_record[uid] = {}                    # make sure the dict exists
#                 h.unit_record[uid]["EntryTime"] = env.now  # <--- record arrival time
#                 h.unit_record[uid]['SAW'] = env.now

#                 # Push into WIPo_SAWn
#                 queues[out_q].append(uid)
#                 h.log_wip(env, out_q, queues)
#                 h.log_move(env, uid, name, out_q, 'finish')
#             else:
#                 yield env.timeout(POLL)

#     for s in ('SAW1','SAW2','SAW3','SAW4','SAW5'):
#         env.process(
#             saw_processor(env, s, cfg.network[s]['process_time'])
#         )

#     # ─── 4) MOVE from WIPo_SAW* → WIPi_IH* ─────────────────────────────────
#     for w in ('WIPo_SAW1','WIPo_SAW2','WIPo_SAW3','WIPo_SAW4','WIPo_SAW5'):
#         env.process(
#             move(
#                 env,
#                 w,
#                 queues,
#                 cfg.network[w]['next'],           # IH destinations
#                 cfg.network[w]['transport_times']
#             )
#         )

#     # ─── 5) IH MACHINES ────────────────────────────────────────────────────
#     def ih(name, pt, out_q):
#         in_q = f'WIPi_{name}'
#         while True:
#             # must check both IH and its downstream Press are up
#             press_name = IH_TO_PRESS[name]
#             if not (h.machine_status.get(name, True) and
#                     h.machine_status.get(press_name, True)):
#                 yield env.timeout(POLL)
#                 continue

#             if queues[in_q]:
#                 uid = queues[in_q].pop(0)
#                 h.log_move(env, uid, in_q, name, 'start')
#                 yield env.timeout(pt)
#                 queues[out_q].append(uid)
#                 h.log_wip(env, out_q, queues)
#                 h.log_move(env, uid, name, out_q, 'finish')
#             else:
#                 yield env.timeout(POLL)

#     for ihm, out_q in (('IH1','WIPi_P1'),
#                       ('IH2','WIPi_P1'),
#                       ('IH3','WIPi_P2')):
#         env.process(
#             ih(ihm, cfg.network[ihm]['process_time'], out_q)
#         )

#     # ─── 6) PRESS MACHINES ──────────────────────────────────────────────────
#     def press(name, pt):
#         COOL = 1440
#         in_q = f'WIPi_{name}'
#         while True:
#             if h.machine_status.get(name, True) and queues[in_q]:
#                 uid = queues[in_q].pop(0)
#                 h.log_move(env, uid, f'{name}_Q', name, 'start')
#                 yield env.timeout(pt)
#                 storage_after_press.append((uid, env.now + COOL))
#                 h.unit_record[uid]['ExitTime'] = env.now
#                 h.unit_record[uid]['Cooling'] = env.now
#                 h.log_move(env, uid, name, 'storage_after_press', 'finish')
#             else:
#                 yield env.timeout(POLL)

#     for p in ('P1','P2'):
#         env.process(
#             press(p, cfg.network[p]['process_time'])
#         )

#     # ─── 7) CL MACHINES (regulated_cl for loopback) ─────────────────────────
#     def regulated_cl(env, name, pt, out_q, limit, monitor_q):
#         """
#         Pull one shell at a time from 'storage_after_press' (once cooled),
#         process at CLn, then send onto the CL conveyor (WIPo_CL).
#         """
#         while True:
#             if not h.machine_status.get(name, True):
#                 yield env.timeout(POLL)
#                 continue

#             # only pull from storage_after_press when its timestamp ≤ now
#             if storage_after_press and env.now >= storage_after_press[0][1]:
#                 uid, _ = storage_after_press.pop(0)
#             else:
#                 yield env.timeout(POLL)
#                 continue

#             h.log_move(env, uid, 'storage_after_press', name, 'start')
#             yield env.timeout(pt)
#             # stamp CL finish
#             h.unit_record[uid]['CL'] = env.now

#             # push onto the conveyor (WIPo_CL) if space
#             if len(queues['WIPo_CL']) < CONVEYOR_CAP:
#                 queues['WIPo_CL'].append(uid)
#                 h.log_move(env, uid, name, 'WIPo_CL', 'finish')
#                 h.log_wip(env, 'WIPo_CL', queues)
#             else:
#                 # if conveyor full, reinsert into storage_after_press front
#                 storage_after_press.insert(0, (uid, env.now))
#                 yield env.timeout(POLL)

#     for clm in ('CL1','CL2','CL3','CL4'):
#         env.process(
#             regulated_cl(
#                 env,
#                 clm,
#                 cfg.network[clm]['process_time'],
#                 cfg.network[clm]['output'],  # usually “WIPo_CL”
#                 PAUSE_LEVEL,
#                 'storage_after_press'
#             )
#         )

#     # ─── 8) CL → SB1 MOVER ──────────────────────────────────────────────
#     def cl_to_sb1_mover():
#         while True:
#             if queues['WIPo_CL']:
#                 uid = queues['WIPo_CL'].pop(0)
#                 t_field = cfg.network['WIPo_CL']['transport_times']
#                 t_move  = t_field[0] if isinstance(t_field, (list, tuple)) else t_field
#                 yield env.timeout(t_move)
#                 queues['WIPi_SB1'].append(uid)
#                 h.log_wip(env, 'WIPi_SB1', queues)
#                 h.log_move(env, uid, 'WIPo_CL', 'WIPi_SB1', 'transport')
#             else:
#                 yield env.timeout(POLL)

#     env.process(cl_to_sb1_mover())

#     # ─── 9) SB1 + PALLET TRANSFER ───────────────────────────────────────────
#     def sb1():
#         while True:
#             if h.machine_status.get('SB1', True) and queues['WIPi_SB1']:
#                 uid = queues['WIPi_SB1'].pop(0)
#                 h.log_move(env, uid, 'WIPi_SB1', 'SB1', 'start')
#                 yield env.timeout(SB1_TIME)
#                 queues['WIPo_SB1'].append(uid)
#                 h.log_move(env, uid, 'SB1', 'WIPo_SB1', 'finish')
#                 h.log_wip(env, 'WIPo_SB1', queues)
#             else:
#                 yield env.timeout(POLL)

#     env.process(sb1())

#     def sb1_pallet_transfer():
#         while True:
#             if len(queues['WIPo_SB1']) >= PALLET_SIZE:
#                 t_field = cfg.network['WIPo_SB1']['transport_times']
#                 travel  = t_field[0] if isinstance(t_field, (list, tuple)) else t_field
#                 with h.forklifts.request() as req:
#                     yield req
#                     yield env.timeout(travel)
#                 for _ in range(PALLET_SIZE):
#                     uid = queues['WIPo_SB1'].pop(0)
#                     queues['finished_goods'].append(uid)
#                     h.log_wip(env, 'finished_goods', queues)
#                     h.log_move(env, uid, 'WIPo_SB1', 'finished_goods', 'pallet_move')
#                     h.unit_record[uid]['FinalGoodsTime'] = env.now
#             else:
#                 yield env.timeout(POLL)

#     env.process(sb1_pallet_transfer())

#     # ─── 10) PRESS MONITOR (cycle IH↔Press loopback) ────────────────────────
#     def press_monitor(press, in_queues, hold_q):
#         prev = h.machine_status.get(press, True)
#         while True:
#             now_up = h.machine_status.get(press, True)

#             # press just went DOWN: divert up to 10 to hold
#             if prev and not now_up:
#                 diverted = 0
#                 for q in in_queues:
#                     while queues[q] and diverted < 10:
#                         uid = queues[q].pop(0)
#                         h.unit_record[uid]["PressDiverts"] += 1
#                         if (h.unit_record[uid]["PressDiverts"] >= 3):
#                             queues['scrap_press'].append(uid)
#                             h.unit_record[uid]["Scrapped"] = True
#                             h.log_move(env, uid, q, 'scrap_press', 'scrap')
#                         else:
#                             queues[hold_q].append(uid)
#                             h.log_move(env, uid, q, hold_q, 'divert')
#                         diverted += 1
#                         h.log_wip(env, hold_q, queues)

#             # press just came UP: flush hold → IH input
#             if (not prev) and now_up and queues[hold_q]:
#                 ih_dest_candidates = {
#                     'P1': ['WIPi_IH1','WIPi_IH2'],
#                     'P2': ['WIPi_IH3']
#                 }
#                 while queues[hold_q]:
#                     uid = queues[hold_q].pop(0)
#                     dests = ih_dest_candidates[press]
#                     dest  = min(dests, key=lambda d: len(queues[d]))
#                     queues[dest].append(uid)
#                     h.log_move(env, uid, hold_q, dest, 'reheat')
#                     h.log_wip(env, dest, queues)

#             prev = now_up
#             yield env.timeout(POLL)

#     env.process(press_monitor('P1', ['WIPi_IH1','WIPi_IH2'], 'hold_P1'))
#     env.process(press_monitor('P2', ['WIPi_IH3'], 'hold_P2'))

#     return queues, None   # (Stage 1 does not return a conveyor; it's used downstream)



# plant_sim/stage1.py

import simpy, sys, pathlib, uuid
from plant_sim import helpers as h
from plant_sim import config as cfg
import re

# ensure helpers & config resolve (assumes notebook sits with them or one level up)
if not pathlib.Path('helpers.py').exists():
    sys.path.append('..')

from .helpers import machine_status

# clean previous runs
h.movement_log.clear()
h.wip_history.clear()
h.unit_record.clear()


# ------------------ parameters (unchanged) ------------------

SIM_TIME        = 20_000
CONVEYOR_CAP    = 100
PAUSE_LEVEL     = 100
RESUME_LEVEL    = 50
THROTTLE        = True
# SB1_TIME        = cfg.network['SB1']['process_time']
FORKLIFT_COUNT  = 2
PALLET_SIZE     = 42
POLL            = 0.01

# map which IH feeds which Press
IH_TO_PRESS     = {"IH1": "P1", "IH2": "P1", "IH3": "P2"}


def move(env, wipo, queues, dests, tts):
    """One-by-one transporter (round-robin to shortest queue)."""
    if not isinstance(tts, list):
        tts = [tts] * len(dests)

    while True:
        if queues[wipo]:
            active_dest_pairs = [
                (d, t) for d, t in zip(dests, tts)
                if h.machine_status.get(d, True)
            ]
            if not active_dest_pairs:
                yield env.timeout(0.05)
                continue

            dest, t_trans = min(active_dest_pairs,
                                key=lambda pair: len(queues[pair[0]]))
            uid = queues[wipo].pop(0)
            yield env.timeout(t_trans)
            queues[dest].append(uid)
            h.log_wip(env, dest, queues)
            h.log_move(env, uid, wipo, dest, 'transport')
        else:
            yield env.timeout(0.05)


def build(env, cfg, queues, storage_after_press, finished_goods):
    """
    Stage 1 build: SAW → IH → Press → CL → Conveyor.

    • We remove all WIPi_SAW* queues. Each SAWn
      will “create” a new shell as soon as it’s free.
    • After processing, SAWn pushes to WIPo_SAWn; the
      move(env,…) calls carry that to IH inputs.
    • CL is still regulated (via regulated_cl) so that
      Stage 4→Stage 1 loopback can feed CL properly.
    """

    # ─── 1) DOWNTIME / MACHINE‐STATUS SETUP ────────────────────────────────
    h.machine_status.clear()
    for m_name, data in cfg.network.items():
        if "OEE" not in data:
            continue
        h.machine_status[m_name] = (data["OEE"] > 0)
        if data["OEE"] > 0:
            env.process(h.downtime(env, m_name, data["OEE"]))

    # ─── 2) INITIALIZE QUEUES ──────────────────────────────────────────────
#     queues.clear()
#     queues.update(h.init_queues(cfg.network))

    # ─── MERGE ONLY Stage 1 queues ─────────────────────────────────────────
    needed = [
        # SAW outputs
        *[f"WIPo_{name}" for name in cfg.network if name.startswith("SAW")],
        # IH inputs/outputs
        *[f"WIPi_{name}" for name in cfg.network if name.startswith("IH")],
        *[f"WIPo_{name}" for name in cfg.network if name.startswith("IH")],
        # Press, loopback, CL conveyor
        "storage_after_press", "WIPo_CL", "WIPi_SB1", "WIPo_SB1",
        "finished_goods"
    ]
    for q in needed:
        queues.setdefault(q, [])

    # expose for debugging if needed
    env.queues = queues
    env.storage_after_press = storage_after_press

    # forklift resource
    h.forklifts = simpy.Resource(env, capacity=FORKLIFT_COUNT)

    # ─── 3) SAW PROCESSORS (no WIPi_SAW queue) ───────────────────────────
    def saw_processor(env, name, pt):
        """
        Each SAWn “pulls” a brand-new shell as soon as it finishes its prior one.
        After processing, push into WIPo_SAWn.
        """
        out_q = f'WIPo_{name}'
        while True:
            if h.machine_status.get(name, True):
                # Create a new unit immediately
                h.global_item_counter += 1
                uid = f"U{h.global_item_counter}"
                h.unit_record[uid]['SAW'] = env.now
                h.log_move(env, uid, '', name, 'create')

                # Process on SAWn
                h.log_move(env, uid, name, name, 'start')
                yield env.timeout(pt)
                h.unit_record[uid] = {}                    # make sure the dict exists
                h.unit_record[uid]["EntryTime"] = env.now  # <--- record arrival time
                h.unit_record[uid]['SAW'] = env.now

                # Push into WIPo_SAWn
                queues[out_q].append(uid)
                h.log_wip(env, out_q, queues)
                h.log_move(env, uid, name, out_q, 'finish')
            else:
                yield env.timeout(POLL)

    # ─── 3) SAW PROCESSORS (no WIPi_SAW queue) ───────────────────────────
    saw_names = [name
                 for name, data in cfg.network.items()
                 if name.startswith('SAW') and 'process_time' in data]
    for s in saw_names:
        env.process(
            saw_processor(env,
                          s,
                          cfg.network[s]['process_time'])
        )

    # ─── 4) MOVE from WIPo_SAW* → WIPi_IH* ─────────────────────────────────
    for s in saw_names:
        w = f'WIPo_{s}'
        env.process(
            move(env,
                 w,
                 queues,
                 cfg.network[w]['next'],
                 cfg.network[w]['transport_times'])
        )

    # ─── 5) IH MACHINES ────────────────────────────────────────────────────
    def ih(name, pt, out_q):
        in_q = f'WIPi_{name}'
        while True:
            # must check both IH and its downstream Press are up
            press_name = IH_TO_PRESS[name]
            if not (h.machine_status.get(name, True) and
                    h.machine_status.get(press_name, True)):
                yield env.timeout(POLL)
                continue

            if queues[in_q]:
                uid = queues[in_q].pop(0)
                h.log_move(env, uid, in_q, name, 'start')
                yield env.timeout(pt)
                queues[out_q].append(uid)
                h.log_wip(env, out_q, queues)
                h.log_move(env, uid, name, out_q, 'finish')
            else:
                yield env.timeout(POLL)

    for ihm, out_q in (('IH1','P1'),
                      ('IH2','P1'),
                      ('IH3','P2')):
        env.process(
            ih(ihm, cfg.network[ihm]['process_time'], out_q)
        )

    # ─── 6) PRESS MACHINES ──────────────────────────────────────────────────
    def press(name, pt):
        COOL = 1440
        in_q = name
        while True:
            if h.machine_status.get(name, True) and queues[in_q]:
                uid = queues[in_q].pop(0)
                h.log_move(env, uid, f'{name}_Q', name, 'start')
                yield env.timeout(pt)
                storage_after_press.append((uid, env.now + COOL))
                h.unit_record[uid]['ExitTime'] = env.now
                h.unit_record[uid]['Cooling'] = env.now
                h.log_move(env, uid, name, 'storage_after_press', 'finish')
            else:
                yield env.timeout(POLL)

    for p in ('P1','P2'):
        env.process(
            press(p, cfg.network[p]['process_time'])
        )

    # ─── 7) CL MACHINES (regulated_cl for loopback) ─────────────────────────
    def regulated_cl(env, name, pt, out_q, limit, monitor_q):
        """
        Pull one shell at a time from 'storage_after_press' (once cooled),
        process at CLn, then send onto the CL conveyor (WIPo_CL).
        """
        while True:
            if not h.machine_status.get(name, True):
                yield env.timeout(POLL)
                continue

            # only pull from storage_after_press when its timestamp ≤ now
            if storage_after_press and env.now >= storage_after_press[0][1]:
                uid, _ = storage_after_press.pop(0)
            else:
                yield env.timeout(POLL)
                continue

            h.log_move(env, uid, 'storage_after_press', name, 'start')
            yield env.timeout(pt)
            # stamp CL finish
            h.unit_record[uid]['CL'] = env.now

            # push onto the conveyor (WIPo_CL) if space
            if len(queues['WIPo_CL']) < CONVEYOR_CAP:
                queues['WIPo_CL'].append(uid)
                h.log_move(env, uid, name, 'WIPo_CL', 'finish')
                h.log_wip(env, 'WIPo_CL', queues)
            else:
                # if conveyor full, reinsert into storage_after_press front
                storage_after_press.insert(0, (uid, env.now))
                yield env.timeout(POLL)

    cl_names = [n for n in cfg.network
                if n.startswith('CL') and 'process_time' in cfg.network[n]]
    for clm in cl_names:
        env.process(
            regulated_cl(env,
                         clm,
                         cfg.network[clm]['process_time'],
                         cfg.network[clm]['output'],
                         PAUSE_LEVEL,
                         'storage_after_press')
        )

    # ─── 8) CL → SB1 MOVER ──────────────────────────────────────────────
    def cl_to_sb_mover(env):
        dests = cfg.network['WIPo_CL']['next']            # four WIPi_SBx
        tts   = cfg.network['WIPo_CL']['transport_times'] # matching times

        while True:
            if queues['WIPo_CL']:
                uid = queues['WIPo_CL'].pop(0)

                # choose the active SB buffer with the shortest queue
                active = [(d, t) for d, t in zip(dests, tts)
                          if h.machine_status.get(d.replace('WIPi_', ''), True)]
#                 print(h.machine_status['SB3'], h.machine_status['SB4'])
                dest, t_move = min(active, key=lambda pair: len(queues[pair[0]]))

                yield env.timeout(t_move)
                queues[dest].append(uid)
                h.log_wip(env, dest, queues)
                h.log_move(env, uid, 'WIPo_CL', dest, 'transport')
            else:
                yield env.timeout(POLL)

    env.process(cl_to_sb_mover(env))


    # ─── SB1–SB4 processing & pallet moves ─────────────────────────────
    SB_RANGE = range(1, 5)  # 1‥4

    # guarantee queues exist
    for i in SB_RANGE:
        queues.setdefault(f"WIPi_CC{i}", [])
        queues.setdefault(f"WIPo_CC{i}", [])

    # --- SB processors ---
    def sb_processor(env, i):
        name   = f"CC{i}"
        in_q   = f"WIPi_{name}"
        out_q  = f"WIPo_{name}"
        pt     = cfg.network[name]['process_time']
        while True:
            if h.machine_status.get(name, True) and queues[in_q]:
                uid = queues[in_q].pop(0)
                h.log_move(env, uid, in_q, name, 'start')
                yield env.timeout(pt)
                queues[out_q].append(uid)
                h.log_move(env, uid, name, out_q, 'finish')
                h.log_wip(env, out_q, queues)
            else:
                yield env.timeout(POLL)

    for i in SB_RANGE:
        env.process(sb_processor(env, i))

    # --- pallet transfers ---
    def sb_pallet_transfer(env, i):
        wip_o  = f"WIPo_CC{i}"
        tt_raw = cfg.network[wip_o]['transport_times']
        travel = tt_raw[0] if isinstance(tt_raw, (list, tuple)) else tt_raw
        while True:
            if len(queues[wip_o]) >= PALLET_SIZE:
                with h.forklifts.request() as req:
                    yield req
                    yield env.timeout(travel)
                for _ in range(PALLET_SIZE):
                    uid = queues[wip_o].pop(0)
                    queues['finished_goods'].append(uid)
                    h.log_wip(env, 'finished_goods', queues)
                    h.log_move(env, uid, wip_o, 'finished_goods', 'pallet_move')
                    h.unit_record[uid]['FinalGoodsTime'] = env.now
            else:
                yield env.timeout(POLL)

    for i in SB_RANGE:
        env.process(sb_pallet_transfer(env, i))
        
    # ─── 10) PRESS MONITOR (cycle IH↔Press loopback) ────────────────────────
    def press_monitor(press, in_queues, hold_q):
        prev = h.machine_status.get(press, True)
        while True:
            now_up = h.machine_status.get(press, True)

            # press just went DOWN: divert up to 10 to hold
            if prev and not now_up:
                diverted = 0
                for q in in_queues:
                    while queues[q] and diverted < 10:
                        uid = queues[q].pop(0)
                        h.unit_record[uid]["PressDiverts"] += 1
                        if (h.unit_record[uid]["PressDiverts"] >= 3):
                            queues['scrap_press'].append(uid)
                            h.unit_record[uid]["Scrapped"] = True
                            h.log_move(env, uid, q, 'scrap_press', 'scrap')
                        else:
                            queues[hold_q].append(uid)
                            h.log_move(env, uid, q, hold_q, 'divert')
                        diverted += 1
                        h.log_wip(env, hold_q, queues)

            # press just came UP: flush hold → IH input
            if (not prev) and now_up and queues[hold_q]:
                ih_dest_candidates = {
                    'P1': ['WIPi_IH1','WIPi_IH2'],
                    'P2': ['WIPi_IH3']
                }
                while queues[hold_q]:
                    uid = queues[hold_q].pop(0)
                    dests = ih_dest_candidates[press]
                    dest  = min(dests, key=lambda d: len(queues[d]))
                    queues[dest].append(uid)
                    h.log_move(env, uid, hold_q, dest, 'reheat')
                    h.log_wip(env, dest, queues)

            prev = now_up
            yield env.timeout(POLL)

    env.process(press_monitor('P1', ['WIPi_IH1','WIPi_IH2'], 'hold_P1'))
    env.process(press_monitor('P2', ['WIPi_IH3'], 'hold_P2'))

    return queues, None   # (Stage 1 does not return a conveyor; it's used downstream)







