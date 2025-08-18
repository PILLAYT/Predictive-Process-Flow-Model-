#
# plant_sim/stage5.py
# -----------------------------------------------------------------------------
# Stage 5 – FO → UT → SR1 → DB → KN → PDB (once‐per‐shift destruction) → FC → SP1 → FG5
# -----------------------------------------------------------------------------
import simpy
from .helpers import log_move, log_wip, unit_record
import plant_sim.helpers as helpers
from . import config as cfg
from .stage4 import foot_mover   # used for UT→SR1 (single‐shell) only
from .helpers import batch_move   # ← NEW import

# -----------------------------------------------------------------------------
# 2) Feeder: finished_goods4 → WIPi_FO1…WIPi_FO4 in pallets of 42 shells
# -----------------------------------------------------------------------------
def stage5_feeder(env, cfg, queues, src='finished_goods4'):
    """
    … same docstring …
    """
    all_dests = cfg.network[src]['next']            # e.g. ['WIPi_FO1',…,'WIPi_FO8']
    tts       = cfg.network[src]['transport_times']
    t_trans   = tts[0] if isinstance(tts, (list,tuple)) else tts
    BATCH     = cfg.FO_MERGE_CAP                    # 42

    while True:
        # only consider “live” FO inputs
        valid_dests = []
        for d in all_dests:
            # find the FO machine fed by this WIP‐input
            fo = cfg.network[d]['next'][0]         # e.g. 'FO5'
            if cfg.network[fo]['OEE'] > 0 and helpers.machine_status.get(fo, True):
                valid_dests.append(d)

        if len(queues[src]) >= BATCH and valid_dests:
            pallet = [queues[src].pop(0) for _ in range(BATCH)]
            with helpers.forklifts.request() as req:
                yield req; yield env.timeout(t_trans)

            for uid in pallet:
                idx  = min(range(len(valid_dests)),
                           key=lambda i: len(queues[valid_dests[i]]))
                dest = valid_dests[idx]
                queues[dest].append(uid)
                log_move(env, uid, src, dest, 'batch5')
                log_wip(env, dest, queues)
        else:
            yield env.timeout(0.05)


# -----------------------------------------------------------------------------
# 3) FO processor: WIPi_FO# → process → WIPo_FO#
# -----------------------------------------------------------------------------
def fo_processor(env, name, cfg, queues):
    """
    Each FO1…FO4 does this:
      - Pop one shell from WIPi_FO#
      - Process it (ptime/OEE)
      - Append that single shell into WIPo_FO#
    A separate batch mover will wait for 42 shells in WIPo_FO# before forklift‐moving them onward.
    """
    normal_q = cfg.MACHINE_INPUT[name]  # 'WIPi_FO1' if name == 'FO1', etc.

    while True:
        if not queues.get(normal_q):
            yield env.timeout(0.05)
            continue

        uid = queues[normal_q].pop(0)
        log_move(env, uid, normal_q, name, 'start')
        log_wip(env, normal_q, queues)

        ptime = cfg.network[name]['process_time'] / cfg.network[name]['OEE']
        yield env.timeout(ptime)

        out = f"WIPo_{name}"  # e.g. 'WIPo_FO1'
        queues[out].append(uid)
        log_move(env, uid, name, out, 'finish')
        log_wip(env, out, queues)


# -----------------------------------------------------------------------------
# 3a) FO batch mover: WIPo_FO# → WIPi_UT (42 shells at once)
# -----------------------------------------------------------------------------
def fo_batch_mover(env, src_wipo, queues, t_trans, batch_size=42):
    """
    For each FO output queue `src_wipo` (e.g. 'WIPo_FO1'), wait until it has ≥ 42 shells.
    Then forklift‐move that entire 42‐shell pallet into 'WIPi_UT' in one single trip.
    """
    while True:
        if len(queues.get(src_wipo, [])) >= batch_size:
            pallet = [queues[src_wipo].pop(0) for _ in range(batch_size)]
            with helpers.forklifts.request() as req:
                yield req
                yield env.timeout(t_trans)

            for uid in pallet:
                queues['WIPi_UT'].append(uid)
                log_move(env, uid, src_wipo, 'WIPi_UT', 'batch5')
                log_wip(env, 'WIPi_UT', queues)
        else:
            yield env.timeout(0.05)


# -----------------------------------------------------------------------------
# 4) UT processor + foot‐move to SR1
# -----------------------------------------------------------------------------
# We use the generic machine_processor for UT → WIPo_UT, and foot_mover to send
# WIPo_UT → WIPi_SR1 (one shell at a time).
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# 4a) Generic machine coroutine: UT, SR1, DB1–DB6, KN1–KN2
# -----------------------------------------------------------------------------
def machine_processor(env, name, cfg, queues):
    """
    Single‐shell logic for UT, SR1, DB1–DB6, KN1–KN2, FC1–FC3, SP1:
      1. Pop one shell from `WIPi_<name>`
      2. Process for `process_time / OEE`
      3. Send that shell to `cfg.network[name]['next']` (or 'output' if no 'next')—
         if that is a list, pick the shortest queue among them.
    """
    normal_q = cfg.MACHINE_INPUT[name]

    while True:
        if not queues.get(normal_q):
            yield env.timeout(0.05)
            continue

        uid = queues[normal_q].pop(0)
        log_move(env, uid, normal_q, name, 'start')
        log_wip(env, normal_q, queues)

        ptime = cfg.network[name]['process_time'] / cfg.network[name]['OEE']
        yield env.timeout(ptime)

        out = cfg.network[name].get('next', cfg.network[name].get('output'))
        if isinstance(out, list):
            dest = min(out, key=lambda d: len(queues[d]))
        else:
            dest = out

        queues[dest].append(uid)
        log_move(env, uid, name, dest, 'finish')
        log_wip(env, dest, queues)


# ------------------------------------------------------------------------------
# 5) PDB destructive-plus-pallet mover (fixed fc_inputs wrap)
# ------------------------------------------------------------------------------
# def pdb_processor(env, name, cfg, queues):
#     """
#     Each PDB1/PDB2:
#       1. Pop one shell from WIPi_PDB#
#       2. Process it for process_time/OEE
#       3. Internally accumulate it into a 42-shell pallet buffer.
#       4. As soon as pallet hits 42:
#          a. If env.now >= next_fail_time: pop one from the pallet → scrap,
#             and increment next_fail_time += PDB_FAIL_INTERVAL.
#          b. Choose the FC input (WIPi_FC1/2/FC3) with the fewest shells.
#          c. Request one forklift, wait that transport time, and batch-send
#             **all remaining** shells in the pallet to that single FC input.
#          d. Reset pallet buffer to empty.
#     """
#     # 1) Which input queue Feds this PDB?  (e.g. "WIPi_PDB1")
#     in_q      = cfg.MACHINE_INPUT[name]
#     # 2) Next time to destroy one shell (once‐per‐shift)
#     next_fail = cfg.PDB_FAIL_INTERVAL
#     # 3) Internal pallet buffer (holds up to 42 UIDs)
#     pallet    = []

#     # 4) Grab the FC‐input list from cfg.network[name]['next']:
#     raw_next = cfg.network[name]['next']
#     if isinstance(raw_next, list):
#         fc_inputs = raw_next
#     else:
#         fc_inputs = [raw_next]

#     # 5) Grab the transport times from cfg.network[name]['transport_times']
#     raw_tts = cfg.network[name]['transport_times']
#     if isinstance(raw_tts, list):
#         fc_tts = raw_tts
#     else:
#         # broadcast a single value across all FC destinations
#         fc_tts = [raw_tts] * len(fc_inputs)

#     while True:
#         # ——— Wait for a shell in WIPi_PDB# —————————————————————
#         if not queues.get(in_q) or len(queues[in_q]) == 0:
#             yield env.timeout(0.05)
#             continue

#         # ——— Pop one shell for processing ——————————————————————
#         uid = queues[in_q].pop(0)
#         log_move(env, uid, in_q, name, 'start')
#         log_wip(env, in_q, queues)

#         # ——— Simulate the PDB process time ————————————————————
#         ptime = cfg.network[name]['process_time'] / cfg.network[name]['OEE']
#         yield env.timeout(ptime)

#         # ——— Accumulate into internal pallet ———————————————
#         pallet.append(uid)

#         # ——— Once we have exactly 42 shells, time to load the pallet ————
#         if len(pallet) == cfg.FO_MERGE_CAP:  # FO_MERGE_CAP == 42
#             # a) Destructive test if due
#             if env.now >= next_fail:
#                 victim = pallet.pop()  # scrap the last-arrived shell
#                 queues['scrap'].append(victim)
#                 log_move(env, victim, name, 'scrap', 'destroy')
#                 log_wip(env, 'scrap', queues)
#                 next_fail += cfg.PDB_FAIL_INTERVAL

#             # b) Choose which FC input has the fewest shells right now
#             dest = min(fc_inputs, key=lambda d: len(queues[d]))
#             idx  = fc_inputs.index(dest)
#             t_trans = fc_tts[idx]

#             # c) One forklift trip to THAT FC input
#             with helpers.forklifts.request() as req:
#                 yield req
#                 yield env.timeout(t_trans)

#             # d) Drop all remaining shells in pallet into the chosen FC queue
#             for u in pallet:
#                 queues[dest].append(u)
#                 log_move(env, u, name, dest, 'batch')
#             log_wip(env, dest, queues)

#             # e) Reset pallet for next 42
#             pallet = []

def pdb_processor(env, name, cfg, queues):
    in_q      = cfg.MACHINE_INPUT[name]      # e.g. 'WIPi_PDB1'
    next_fail = cfg.PDB_FAIL_INTERVAL        # once‐per‐shift
    pallet    = []                           # for destructive‐test timing

    normal_out = f"WIPo_{name}"              # e.g. 'WIPo_PDB1'
    while True:
        if not queues.get(in_q):
            yield env.timeout(0.05)
            continue

        uid = queues[in_q].pop(0)
        log_move(env, uid, in_q, name, 'start')
        log_wip(env, in_q, queues)

        ptime = cfg.network[name]['process_time'] / cfg.network[name]['OEE']
        yield env.timeout(ptime)

        # destructive test only removes 1 from each 42 processed
        pallet.append(uid)
        if env.now >= next_fail and len(pallet) > 0:
            victim = pallet.pop()               # scrap last shell
            queues['scrap'].append(victim)
            log_move(env, victim, name, 'scrap', 'destroy')
            log_wip(env, 'scrap', queues)
            next_fail += cfg.PDB_FAIL_INTERVAL

        # send *all* processed shells into WIPo_PDB#, to be batched later
        for u in pallet:
            queues[normal_out].append(u)
            log_move(env, u, name, normal_out, 'finish')
        log_wip(env, normal_out, queues)

        pallet = []

# -----------------------------------------------------------------------------
# 6) FC processor (single‐shell) and per‐machine batch mover: WIPo_FC# → WIPi_SP1
# -----------------------------------------------------------------------------
def fc_processor(env, name, cfg, queues):
    """
    Each FC1…FC3 does:
      - Pop one shell from WIPi_FC#
      - Process it
      - Append that shell into WIPo_FC#
    A separate batch mover waits until WIPo_FC# accumulates 42 shells, then moves
    that 42‐shell pallet into WIPi_SP1 in one forklift trip.
    """
    normal_q = cfg.MACHINE_INPUT[name]

    while True:
        if not queues.get(normal_q):
            yield env.timeout(0.05)
            continue

        uid = queues[normal_q].pop(0)
        log_move(env, uid, normal_q, name, 'start')
        log_wip(env, normal_q, queues)

        ptime = cfg.network[name]['process_time'] / cfg.network[name]['OEE']
        yield env.timeout(ptime)

        out = f"WIPo_{name}"  # e.g. 'WIPo_FC1'
        queues[out].append(uid)
        log_move(env, uid, name, out, 'finish')
        log_wip(env, out, queues)


def fc_batch_mover(env, src_wipo, queues, t_trans, batch_size=42):
    """
    For each FC output queue `src_wipo` (e.g. 'WIPo_FC1'), wait until it has ≥ 42 shells.
    Then forklift‐move that 42‐shell pallet into 'WIPi_SP1'.
    """
    while True:
        if len(queues.get(src_wipo, [])) >= batch_size:
            pallet = [queues[src_wipo].pop(0) for _ in range(batch_size)]
            with helpers.forklifts.request() as req:
                yield req
                yield env.timeout(t_trans)

            for uid in pallet:
                queues['WIPi_SP1'].append(uid)
                log_move(env, uid, src_wipo, 'WIPi_SP1', 'batch5')
                log_wip(env, 'WIPi_SP1', queues)
        else:
            yield env.timeout(0.05)


# -----------------------------------------------------------------------------
# 7) SP1 processor (single‐shell) + SP1 → finished_goods5 batch mover
# -----------------------------------------------------------------------------
def sp1_processor(env, cfg, queues):
    """
    SP1 pops one shell from WIPi_SP1, processes it, then appends it into WIPo_SP1.
    A separate batch mover waits until WIPo_SP1 has 42 shells, then moves them
    into finished_goods5 as a single forklift trip.
    """
    normal_q = cfg.MACHINE_INPUT['SP1']

    while True:
        if not queues.get(normal_q):
            yield env.timeout(0.05)
            continue

        uid = queues[normal_q].pop(0)
        log_move(env, uid, normal_q, 'SP1', 'start')
        log_wip(env, normal_q, queues)

        ptime = cfg.network['SP1']['process_time'] / cfg.network['SP1']['OEE']
        yield env.timeout(ptime)

        queues['WIPo_SP1'].append(uid)
        log_move(env, uid, 'SP1', 'WIPo_SP1', 'finish')
        log_wip(env, 'WIPo_SP1', queues)


def sp1_to_fg5_batch(env, queues):
    """
    Wait until WIPo_SP1 has ≥ 42 shells, then forklift moves them into finished_goods5.
    """
    batch_size = cfg.FO_MERGE_CAP  # 42
    tts = cfg.network['WIPo_SP1']['transport_times']
    t_trans = tts[0] if isinstance(tts, (list, tuple)) else tts

    while True:
        if len(queues.get('WIPo_SP1', [])) >= batch_size:
            pallet = [queues['WIPo_SP1'].pop(0) for _ in range(batch_size)]
            with helpers.forklifts.request() as req:
                yield req
                yield env.timeout(t_trans)

            for uid in pallet:
                queues['finished_goods5'].append(uid)
                unit_record[uid]['Stage5Storage'] = env.now
                log_move(env, uid, 'WIPo_SP1', 'finished_goods5', 'batch5')
                log_wip(env, 'finished_goods5', queues)
        else:
            yield env.timeout(0.05)


# -----------------------------------------------------------------------------
# 8) BUILD – glue everything together
# -----------------------------------------------------------------------------
def build(env, cfg, queues, finished_goods4, finished_goods5):
    """
    Stage 5 build: connect finished_goods4 → FO1…FO4 (42‐batch) → WIPi_UT → UT → SR1 → 
    DB1–DB6 → KN1–KN2 → PDB1–PDB2 (once‐per‐shift) → FC1–FC3 (42‐batch) → SP1 (42‐batch) → finished_goods5.

    Assumes run_sim.py has already set:
      queues['finished_goods4'] = finished_goods4
      queues['finished_goods5'] = finished_goods5
      queues['WIPi_UT']         = []
    """
    net = cfg.network

    # 8.1) FO feeder: finished_goods4 → WIPi_FO1…WIPi_FO4 in pallets of 42 shells
    # … inside stage5.build( ) …
    # 8.1) FO feeder: only feed live FO machines
    raw_dests = cfg.network['finished_goods4']['next']
    tts       = cfg.network['finished_goods4']['transport_times']
    t_trans   = tts[0] if isinstance(tts, (list, tuple)) else tts

    feeder_dests = []
    for dest_q in raw_dests:
        # find which FO machine uses that input queue
        fo_machine = next((m for m, q in cfg.MACHINE_INPUT.items() if q == dest_q), None)
        if fo_machine \
           and cfg.network[fo_machine]['OEE'] > 0 \
           and helpers.machine_status.get(fo_machine, True):
            feeder_dests.append(dest_q)

    if feeder_dests:
        env.process(batch_move(
            env,
            'finished_goods4',
            queues,
            feeder_dests,
            t_trans
        ))

    # 8.2) FO1–FO4: single‐shell processors + per‐machine batch movers
    for fo in ('FO1','FO2','FO3','FO4','FO5','FO6','FO7','FO8'):
        queues.setdefault(f'WIPo_{fo}', [])
        # Ensure each FO output queue exists
        queues[f'WIPo_{fo}'] = []
        # Launch FO processor if machine is up
        if helpers.machine_status.get(fo, True):
            env.process(fo_processor(env, fo, cfg, queues))

        # Launch the batch mover on WIPo_FO# → WIPi_UT (42 shells)
        tts = net[f'WIPo_{fo}']['transport_times']
        t_trans = tts[0] if isinstance(tts, (list, tuple)) else tts
        env.process(fo_batch_mover(env, f'WIPo_{fo}', queues, t_trans, batch_size=cfg.FO_MERGE_CAP))
        
    # ─── initialize the shared UT output and each SR input queue ───
    queues.setdefault('WIPo_UT', [])
    for q in cfg.network['WIPo_UT']['next']:
        queues.setdefault(q, [])

    # 8.3) UT1 & UT2 in parallel → shared WIPo_UT
    for ut in ('UT1','UT2'):
        if helpers.machine_status.get(ut, True):
            env.process(machine_processor(env, ut, cfg, queues))

    # 8.3) UT1 & UT2 …
    for ut in ('UT1','UT2'):
        if helpers.machine_status.get(ut, True):
            env.process(machine_processor(env, ut, cfg, queues))

    # make sure the UT‐output buffer exists, and each SR input does too
    queues.setdefault('WIPo_UT', [])
    for q in cfg.network['WIPo_UT']['next']:
        queues.setdefault(q, [])

    # 8.3b) UT → SR via batch_move (1 shell at a time)
    raw_sr  = cfg.network['WIPo_UT']['next']
    t_trans = (cfg.network['WIPo_UT']['transport_times'][0]
               if isinstance(cfg.network['WIPo_UT']['transport_times'], (list,tuple))
               else cfg.network['WIPo_UT']['transport_times'])

    valid_sr = []
    for dest_q in raw_sr:
        sr_m = next((m for m,q in cfg.MACHINE_INPUT.items() if q==dest_q), None)
        if sr_m and cfg.network[sr_m]['OEE']>0 and helpers.machine_status.get(sr_m,True):
            valid_sr.append(dest_q)

    for dest_q in valid_sr:
        env.process(batch_move(env,
                               'WIPo_UT',
                               queues,
                               [dest_q],
                               t_trans,
                               batch_size=1))


    # 8.4) SR1 & SR2 in parallel from shared WIPi_SR → WIPo_SR
    for sr in ('SR1','SR2'):
        if helpers.machine_status.get(sr, True):
            env.process(machine_processor(env, sr, cfg, queues))

    # batch‐move from shared WIPo_SR → DB inputs
    all_db = net['WIPo_SR']['next']
    tts   = net['WIPo_SR']['transport_times']
    t_db  = tts[0] if isinstance(tts,(list,tuple)) else tts
    valid_db = []
    for d in all_db:
        db = cfg.network[d]['next'][0]  # e.g. 'DB5'
        if cfg.network[db]['OEE'] > 0 and helpers.machine_status.get(db, True):
            valid_db.append(d)

    if valid_db:
        env.process(batch_move(env,
                               'WIPo_SR',
                               queues,
                               valid_db,
                               t_db))

    # 8.5) DB1–DB6: each single‐shell + filtered_move to KN1–KN2
    for i in range(1, 7):
        db_name = f'DB{i}'
        if helpers.machine_status.get(db_name, True):
            env.process(machine_processor(env, db_name, cfg, queues))
        wipo = f'WIPo_{db_name}'
        for i in range(1, 7):
            wipo = f'WIPo_DB{i}'
            env.process(batch_move(env,
                                   wipo,
                                   queues,
                                   net[wipo]['next'],       # ['WIPi_KN1','WIPi_KN2']
                                   net[wipo]['transport_times']))

#     # 8.6) KN1 & KN2: single‐shell + filtered_move to PDB1/PDB2
#     for kn in ('KN1', 'KN2'):
#         if helpers.machine_status.get(kn, True):
#             env.process(machine_processor(env, kn, cfg, queues))
#         env.process(batch_move(env,
#                                'WIPo_KN',
#                                queues,
#                                net['WIPo_KN']['next'],      # ['WIPi_PDB1','WIPi_PDB2']
#                                net['WIPo_KN']['transport_times']))

    # ── 8.6) KN1–KN4: make sure their input/output buffers exist and spawn them ──
    # initialize the shared KN output buffer
    queues.setdefault('WIPo_KN', [])
    # and the shared KN input buffer (in case we cleared it earlier)
    queues.setdefault('WIPi_KN', [])

    # spin up all four KN machines that are live & have OEE>0
    for kn in ('KN1','KN2','KN3','KN4'):
        if helpers.machine_status.get(kn, True) and cfg.network[kn]['OEE'] > 0:
            env.process(machine_processor(env, kn, cfg, queues))

    # now batch‐move from that shared WIPo_KN into the live PDB inputs
    raw_pdbs    = net['WIPo_KN']['next']                            # ['WIPi_PDB1',…,'WIPi_PDB4']
    ttts        = net['WIPo_KN']['transport_times']
    t_trans_pdb = ttts[0] if isinstance(ttts,(list,tuple)) else ttts

    valid_pdb_inputs = []
    for dest_q in raw_pdbs:
        pdb_machine = next((m for m,q in cfg.MACHINE_INPUT.items() if q==dest_q), None)
        if pdb_machine and \
           cfg.network[pdb_machine]['OEE'] > 0 and \
           helpers.machine_status.get(pdb_machine, True):
            queues.setdefault(dest_q, [])
            valid_pdb_inputs.append(dest_q)

    if valid_pdb_inputs:
        env.process(batch_move(
            env,
            'WIPo_KN',
            queues,
            valid_pdb_inputs,
            t_trans_pdb
        ))

#     # 8.7) PDB1 & PDB2: single‐shell with once‐per‐shift destructive test
#     queues['scrap'] = []
#     for pdb in ('PDB1','PDB2','PDB3','PDB4'):
#         if helpers.machine_status.get(pdb, True):
#             queues.setdefault(cfg.MACHINE_INPUT[pdb], [])
#             env.process(pdb_processor(env, pdb, cfg, queues))

#     # 8.7) PDB1–PDB4: single‐shell with once‐per‐shift destructive test
#     queues.setdefault('scrap', [])
#     for pdb in ('PDB1','PDB2','PDB3','PDB4'):
#         if helpers.machine_status.get(pdb, True) and cfg.network[pdb]['OEE'] > 0:
#             # make sure its input queue exists
#             queues.setdefault(cfg.MACHINE_INPUT[pdb], [])
#             env.process(pdb_processor(env, pdb, cfg, queues))
    # 8.7) PDB1–PDB2 (etc): single‐shell + batch mover → FC inputs
    queues['scrap'] = []
    for pdb in ('PDB1','PDB2','PDB3','PDB4'):
        if helpers.machine_status.get(pdb, True) and cfg.network[pdb]['OEE'] > 0:
            # ensure its WIPo exists
            wipo = f'WIPo_{pdb}'
            queues.setdefault(wipo, [])

            # start the single‐shell PDB processor
            env.process(pdb_processor(env, pdb, cfg, queues))

            # then launch a pallet mover: when WIPo_PDB# has 42, forklift to FC inputs
            next_fc_inputs = cfg.network[wipo]['next']              # e.g. ['WIPi_FC1','WIPi_FC2',...]
            tts            = cfg.network[wipo]['transport_times']
            t_trans        = tts[0] if isinstance(tts,(list,tuple)) else tts

            env.process(batch_move(
                env,
                wipo,
                queues,
                [q for q in next_fc_inputs
                     if cfg.network[next(iter(cfg.network[q]['next']))]['OEE'] > 0
                        and helpers.machine_status.get(next(iter(cfg.network[q]['next'])), True)
                ],  # only live FC inputs
                t_trans,
                batch_size=cfg.FO_MERGE_CAP  # 42
            ))

    # 8.8) FC1–FC6: single‐shell processors + per‐machine batch movers → SP inputs
    for fc in ('FC1','FC2','FC3','FC4','FC5','FC6'):
        in_q  = cfg.MACHINE_INPUT[fc]      # e.g. 'WIPi_FC1'
        out_q = f'WIPo_{fc}'               # 'WIPo_FC1'
        tts   = cfg.network[out_q]['transport_times']
        t_trans = tts[0] if isinstance(tts,(list,tuple)) else tts

        # ensure our queues exist
        queues.setdefault(in_q, [])
        queues.setdefault(out_q, [])

        # only hook in live, non-zero machines
        if helpers.machine_status.get(fc, True) and cfg.network[fc]['OEE'] > 0:
            # single-shell processor
            env.process(machine_processor(env, fc, cfg, queues))

            # now batch-move 42-shell pallets to whichever SP inputs are alive
            raw_sp_inputs = cfg.network[out_q]['next']  # e.g. ['WIPi_SP1','WIPi_SP2']
            live_sp_inputs = []
            for dest in raw_sp_inputs:
                # find the SP machine behind that input queue
                sp_machine = next((m for m,q in cfg.MACHINE_INPUT.items() if q==dest), None)
                if sp_machine \
                   and cfg.network[sp_machine]['OEE'] > 0 \
                   and helpers.machine_status.get(sp_machine, True):
                    live_sp_inputs.append(dest)

            if live_sp_inputs:
                env.process(batch_move(
                    env,
                    out_q,
                    queues,
                    live_sp_inputs,
                    t_trans,
                    batch_size=cfg.FO_MERGE_CAP   # 42
                ))

    # 8.9) SP1 & SP2: single‐shell processors + batch movers → finished_goods5
    for sp in ('SP1','SP2'):
        oee = cfg.network[sp]['OEE']
        in_q = cfg.MACHINE_INPUT[sp]         # 'WIPi_SP1' or 'WIPi_SP2'
        out_q = f'WIPo_{sp}'                 # 'WIPo_SP1' or 'WIPo_SP2'
        tts = cfg.network[out_q]['transport_times']
        t_trans = tts[0] if isinstance(tts, (list,tuple)) else tts

        # ensure queues exist
        queues.setdefault(in_q, [])
        queues.setdefault(out_q, [])

        # only hook in live machines
        if helpers.machine_status.get(sp, True) and oee > 0:
            # spawn the single‐shell processor
            env.process(machine_processor(env, sp, cfg, queues))
            
            env.process(batch_move(
                env,
                out_q,                              # ‘WIPo_SP1’ or ‘WIPo_SP2’
                queues,
                ['finished_goods5'],
                t_trans,
                batch_size=cfg.FO_MERGE_CAP,
                stamp_field="Stage5Storage"         # ★ add this
            ))

            # only if the machine can actually process anything do we batch‐move its output
#             env.process(batch_move(
#                 env,
#                 out_q,
#                 queues,
#                 ['finished_goods5'],
#                 t_trans,
#                 batch_size=cfg.FO_MERGE_CAP
#             ))

# # plant_sim/stage5.py
# # -----------------------------------------------------------------------------
# # Stage 5 – FO → UT → SR → DB → KN → PDB (once-per-shift destruction) → FC → SP1 → FG5
# # -----------------------------------------------------------------------------
# import simpy
# from .helpers import log_move, log_wip, unit_record
# import plant_sim.helpers as helpers
# from . import config as cfg
# from .stage4 import foot_mover     # for UT→SR (single-shell foot move)
# from .helpers import batch_move     # forklift batch mover

# # -----------------------------------------------------------------------------
# # 2) Feeder: finished_goods4 → WIPi_FO1…WIPi_FO8 in 42-shell pallets
# # -----------------------------------------------------------------------------
# def stage5_feeder(env, cfg, queues, src='finished_goods4'):
#     dests   = cfg.network[src]['next']
#     tts     = cfg.network[src]['transport_times']
#     t_trans = tts[0] if isinstance(tts, (list, tuple)) else tts
#     BATCH   = cfg.FO_MERGE_CAP

#     while True:
#         if len(queues[src]) >= BATCH:
#             pallet = [queues[src].pop(0) for _ in range(BATCH)]
#             with helpers.forklifts.request() as req:
#                 yield req; yield env.timeout(t_trans)
#             for uid in pallet:
#                 idx  = min(range(len(dests)), key=lambda i: len(queues[dests[i]]))
#                 dest = dests[idx]
#                 queues[dest].append(uid)
#                 log_move(env, uid, src, dest, 'batch5')
#                 log_wip(env, dest, queues)
#         else:
#             yield env.timeout(0.05)

# # -----------------------------------------------------------------------------
# # 3) FO processor & batch mover
# # -----------------------------------------------------------------------------
# def fo_processor(env, name, cfg, queues):
#     in_q = cfg.MACHINE_INPUT[name]      # e.g. 'WIPi_FO1'
#     out_q = f'WIPo_{name}'
#     while True:
#         if queues[in_q]:
#             uid = queues[in_q].pop(0)
#             log_move(env, uid, in_q, name, 'start')
#             log_wip(env, in_q, queues)
#             ptime = cfg.network[name]['process_time']/cfg.network[name]['OEE']
#             yield env.timeout(ptime)
#             queues[out_q].append(uid)
#             log_move(env, uid, name, out_q, 'finish')
#             log_wip(env, out_q, queues)
#         else:
#             yield env.timeout(0.05)

# def fo_batch_mover(env, src_wipo, queues, t_trans, batch_size=42):
#     while True:
#         if len(queues[src_wipo]) >= batch_size:
#             pallet = [queues[src_wipo].pop(0) for _ in range(batch_size)]
#             with helpers.forklifts.request() as req:
#                 yield req; yield env.timeout(t_trans)
#             for uid in pallet:
#                 queues['WIPi_UT'].append(uid)
#                 log_move(env, uid, src_wipo, 'WIPi_UT', 'batch5')
#                 log_wip(env, 'WIPi_UT', queues)
#         else:
#             yield env.timeout(0.05)

# # -----------------------------------------------------------------------------
# # 4) Generic single-shell machine (UT, SR, DB1–DB6, KN1–KN2, FC1–FC4, SP1)
# # -----------------------------------------------------------------------------
# def machine_processor(env, name, cfg, queues):
#     in_q = cfg.MACHINE_INPUT[name]
#     while True:
#         if queues[in_q]:
#             uid = queues[in_q].pop(0)
#             log_move(env, uid, in_q, name, 'start')
#             log_wip(env, in_q, queues)
#             ptime = cfg.network[name]['process_time']/cfg.network[name]['OEE']
#             yield env.timeout(ptime)
#             out = cfg.network[name].get('next', cfg.network[name].get('output'))
#             if isinstance(out, list):
#                 dest = min(out, key=lambda d: len(queues[d]))
#             else:
#                 dest = out
#             queues[dest].append(uid)
#             log_move(env, uid, name, dest, 'finish')
#             log_wip(env, dest, queues)
#         else:
#             yield env.timeout(0.05)

# # -----------------------------------------------------------------------------
# # 5) PDB destructive-plus-pallet mover
# # -----------------------------------------------------------------------------
# def pdb_processor(env, name, cfg, queues):
#     in_q      = cfg.MACHINE_INPUT[name]
#     next_fail = cfg.PDB_FAIL_INTERVAL
#     pallet    = []
#     raw_next  = cfg.network[name]['next']
#     fc_inputs = raw_next if isinstance(raw_next, list) else [raw_next]
#     raw_tts   = cfg.network[name]['transport_times']
#     fc_tts    = raw_tts if isinstance(raw_tts, list) else [raw_tts]*len(fc_inputs)

#     while True:
#         if queues[in_q]:
#             uid = queues[in_q].pop(0)
#             log_move(env, uid, in_q, name, 'start')
#             log_wip(env, in_q, queues)
#             ptime = cfg.network[name]['process_time']/cfg.network[name]['OEE']
#             yield env.timeout(ptime)
#             pallet.append(uid)
#             if len(pallet)==cfg.FO_MERGE_CAP:
#                 if env.now>=next_fail:
#                     victim = pallet.pop()
#                     queues['scrap'].append(victim)
#                     log_move(env, victim, name, 'scrap','destroy')
#                     log_wip(env,'scrap',queues)
#                     next_fail += cfg.PDB_FAIL_INTERVAL
#                 dest = min(fc_inputs, key=lambda d: len(queues[d]))
#                 idx  = fc_inputs.index(dest)
#                 t_trans = fc_tts[idx]
#                 with helpers.forklifts.request() as req:
#                     yield req; yield env.timeout(t_trans)
#                 for u in pallet:
#                     queues[dest].append(u)
#                     log_move(env,u,name,dest,'batch')
#                 log_wip(env,dest,queues)
#                 pallet=[]
#         else:
#             yield env.timeout(0.05)

# # -----------------------------------------------------------------------------
# # 6) FC processor + batch mover → WIPi_SP1
# # -----------------------------------------------------------------------------
# def fc_processor(env, name, cfg, queues):
#     in_q = cfg.MACHINE_INPUT[name]
#     out_q = f'WIPo_{name}'
#     while True:
#         if queues[in_q]:
#             uid = queues[in_q].pop(0)
#             log_move(env, uid, in_q, name, 'start')
#             log_wip(env, in_q, queues)
#             ptime = cfg.network[name]['process_time']/cfg.network[name]['OEE']
#             yield env.timeout(ptime)
#             queues[out_q].append(uid)
#             log_move(env, uid, name, out_q, 'finish')
#             log_wip(env, out_q, queues)
#         else:
#             yield env.timeout(0.05)

# def fc_batch_mover(env, src_wipo, queues, t_trans, batch_size=42):
#     while True:
#         if len(queues[src_wipo])>=batch_size:
#             pallet=[queues[src_wipo].pop(0) for _ in range(batch_size)]
#             with helpers.forklifts.request() as req:
#                 yield req; yield env.timeout(t_trans)
#             for uid in pallet:
#                 queues['WIPi_SP1'].append(uid)
#                 log_move(env,uid,src_wipo,'WIPi_SP1','batch5')
#                 log_wip(env,'WIPi_SP1',queues)
#         else:
#             yield env.timeout(0.05)

# # -----------------------------------------------------------------------------
# # 7) SP1 + batch → finished_goods5
# # -----------------------------------------------------------------------------
# def sp1_processor(env, cfg, queues):
#     in_q = cfg.MACHINE_INPUT['SP1']
#     while True:
#         if queues[in_q]:
#             uid=queues[in_q].pop(0)
#             log_move(env,uid,in_q,'SP1','start')
#             log_wip(env,in_q,queues)
#             ptime=cfg.network['SP1']['process_time']/cfg.network['SP1']['OEE']
#             yield env.timeout(ptime)
#             queues['WIPo_SP1'].append(uid)
#             log_move(env,uid,'SP1','WIPo_SP1','finish')
#             log_wip(env,'WIPo_SP1',queues)
#         else:
#             yield env.timeout(0.05)

# def sp1_to_fg5_batch(env, queues):
#     batch_size=cfg.FO_MERGE_CAP
#     tts=cfg.network['WIPo_SP1']['transport_times']
#     t_trans=tts[0] if isinstance(tts,(list,tuple)) else tts
#     while True:
#         if len(queues['WIPo_SP1'])>=batch_size:
#             pallet=[queues['WIPo_SP1'].pop(0) for _ in range(batch_size)]
#             with helpers.forklifts.request() as req:
#                 yield req; yield env.timeout(t_trans)
#             for uid in pallet:
#                 queues['finished_goods5'].append(uid)
#                 unit_record[uid]['Stage5Storage']=env.now
#                 log_move(env,uid,'WIPo_SP1','finished_goods5','batch5')
#                 log_wip(env,'finished_goods5',queues)
#         else:
#             yield env.timeout(0.05)

# # -----------------------------------------------------------------------------
# # 8) BUILD – glue everything together
# # -----------------------------------------------------------------------------
# def build(env, cfg, queues, finished_goods4, finished_goods5):
#     net = cfg.network

#     queues['finished_goods4'] = finished_goods4
#     queues['finished_goods5'] = finished_goods5
#     queues.setdefault('WIPi_UT', [])
#     queues['scrap'] = []

#     # 8.1 FO feeder
#     env.process(stage5_feeder(env, cfg, queues))

#     # 8.2 FO1–FO8
#     for fo in ('FO1','FO2','FO3','FO4','FO5','FO6','FO7','FO8'):
#         queues.setdefault(f'WIPo_{fo}', [])
#         if helpers.machine_status.get(fo, True):
#             env.process(fo_processor(env, fo, cfg, queues))
#         tts = net[f'WIPo_{fo}']['transport_times']
#         t_trans = tts[0] if isinstance(tts,(list,tuple)) else tts
#         env.process(fo_batch_mover(env, f'WIPo_{fo}', queues, t_trans, batch_size=cfg.FO_MERGE_CAP))

#     # ─── 8.3) UT1 & UT2: two single‐shell processors → WIPo_UT ────────
#     t_ut = cfg.network['WIPo_UT']['transport_times']
#     t_ut = t_ut[0] if isinstance(t_ut, (list, tuple)) else t_ut

#     for ut in ('UT1','UT2'):
#         if helpers.machine_status.get(ut, True):
#             env.process(machine_processor(env, ut, cfg, queues))

#     # every shell leaving UT1 or UT2 lands in WIPo_UT, now foot‐move each one
#     # into the single‐buffer WIPi_SR (shared for SR1+SR2)
#     queues.setdefault('WIPi_SR', [])
#     env.process(foot_mover(env,
#                            'WIPo_UT',       # shared output
#                            'WIPi_SR',       # single SR input
#                            queues,
#                            t_ut))

#     # ─── 8.4) SR1 & SR2: two single‐shell processors from WIPi_SR → WIPo_SR ────────
#     for sr in ('SR1','SR2'):
#         if helpers.machine_status.get(sr, True):
#             env.process(machine_processor(env, sr, cfg, queues))

#     # batch‐move from the shared WIPo_SR into all your DB inputs
#     env.process(batch_move(env,
#                            'WIPo_SR',
#                            queues,
#                            cfg.network['WIPo_SR']['next'],          # e.g. ['WIPi_DB1', …]
#                            cfg.network['WIPo_SR']['transport_times']))

#     # 8.5 DB1–DB6 → KN1–KN2
#     for i in range(1,7):
#         db=f'DB{i}'
#         if helpers.machine_status.get(db,True):
#             env.process(machine_processor(env, db, cfg, queues))
#         env.process(batch_move(env,
#                                f'WIPo_DB{i}',
#                                queues,
#                                net[f'WIPo_DB{i}']['next'],
#                                net[f'WIPo_DB{i}']['transport_times']))

#     # 8.6 KN1–KN2 → PDB1–PDB4
#     for kn in ('KN1','KN2','KN3','KN4'):
#         if helpers.machine_status.get(kn,True):
#             env.process(machine_processor(env, kn, cfg, queues))
#     env.process(batch_move(env,
#                            'WIPo_KN',
#                            queues,
#                            net['WIPo_KN']['next'],
#                            net['WIPo_KN']['transport_times']))

#     # 8.7 PDB1–PDB4
#     for pdb in ('PDB1','PDB2','PDB3','PDB4'):
#         if helpers.machine_status.get(pdb,True):
#             env.process(pdb_processor(env, pdb, cfg, queues))

#     # 8.8 FC1–FC4
#     for fc in ('FC1','FC2','FC3','FC4'):
#         queues.setdefault(f'WIPo_{fc}', [])
#         if helpers.machine_status.get(fc,True):
#             env.process(fc_processor(env, fc, cfg, queues))
#         tts=net[f'WIPo_{fc}']['transport_times']
#         t_trans=tts[0] if isinstance(tts,(list,tuple)) else tts
#         env.process(fc_batch_mover(env, f'WIPo_{fc}', queues, t_trans, batch_size=cfg.FO_MERGE_CAP))

#     # 8.9 SP1 → FG5
#     queues.setdefault('WIPo_SP1', [])
#     if helpers.machine_status.get('SP1',True):
#         env.process(sp1_processor(env, cfg, queues))
#     env.process(sp1_to_fg5_batch(env, queues))
