# plant_sim/stage4.py
import simpy, random
from . import config as cfg
from .helpers import log_move, log_wip, unit_record
import plant_sim.helpers as helpers
from .stage1 import move                     # for the feeder’s “round-robin” move
from .helpers import batch_move, machine_status   # ← NEW import

CUT_MACHINES   = ['CUT1', 'CUT2', 'CUT3', 'CUT4']
next_fail_time = None        # set in build()

# ──────────────────────────────────────────────────────────────────────────
# 1.  Finished-goods_2  →  WIPi_PO*   (hysteresis throttle on WIPi_HT depth)
# --------------------------------------------------------------------------
# def regulated_stage4_feeder(env, queues, src, dests, tts,
#                             batch_size=42): 
# #                             high_limit=252,     # ←– NEW thresholds
# #                             low_limit=84):      # ←– NEW thresholds
#     """
#     Pull full pallets (42) from `src` (finished_goods_2) and send the shells
#     one-by-one to the least-loaded WIPi_PO*.  
#     Shipping is **blocked** whenever the HT→SPHDT input buffer
#     (`WIPi_SPHDT`) is above `high_limit`, and resumes only after it drains
#     below `low_limit`.
#     """
# #     starved = False
#     t_trans = tts[0] if isinstance(tts, (list, tuple)) else tts

#     while True:
#         depth = len(queues.get('WIPi_SPHDT', []))        # ← throttle buffer

#         if not starved and depth > high_limit:
#             starved = True               # enter “blocked” state
#         elif starved and depth < low_limit:
#             starved = False              # resume shipping

#         if (not starved) and len(queues[src]) >= batch_size:
#         if len(queues[src]) >= batch_size: #added to remove throttle 
#             pallet = [queues[src].pop(0) for _ in range(batch_size)]

#             # forklift travel
#             yield env.timeout(t_trans)

#             # drop each shell into the PO-input with the shortest queue
#             for uid in pallet:
#                 idx  = min(range(len(dests)),
#                            key=lambda i: len(queues[dests[i]]))
#                 dest = dests[idx]
#                 queues[dest].append(uid)
#                 log_move(env, uid, src, dest, 'batch4')
#                 log_wip(env, dest, queues)
#         else:
#             yield env.timeout(0.05)

# ──────────────────────────────────────────────────────────────────────────
# 2.  HDT pallet split : 36 → (2 shells×3 pieces → MTT) + hold 34 shells
# ──────────────────────────────────────────────────────────────────────────
# def hold_and_split(env, cfg, queues, batch_size=36):
#     """
#     Every time 36 shells accumulate at WIPo_HDT:
#       – take the first  2 shells → break each into 3 pieces → send 6 pieces into MTT
#       – hold the remaining 34 shells in 'hold', stamping HoldEntryTime
#     """
#     while True:
#         if len(queues['WIPo_HDT']) >= batch_size:
#             # pull one pallet of 36 shells
#             pallet = [queues['WIPo_HDT'].pop(0) for _ in range(batch_size)]

#             # split off two shells into 6 pieces
#             for shell_uid in pallet[:2]:
#                 for piece_idx in (1, 2, 3):
#                     piece_uid = f"{shell_uid}_p{piece_idx}"
#                     # copy over any existing record data
#                     unit_record[piece_uid] = {
#                         "UnitID": piece_uid,
#                         "ParentID": shell_uid,
#                         "SAW": unit_record[shell_uid].get("SAW"),
#                         "ArrivalTime": unit_record[shell_uid].get("ArrivalTime"),
#                         # Do **not** carry over any StageXStorage/Cell1Storage/FinalGoodsTime etc!
#                     }
#                     # send each piece into MTT
#                     queues['WIPi_MTT'].append(piece_uid)
#                     log_move(env, piece_uid, 'WIPo_HDT', 'WIPi_MTT', 'split4')
#                     log_wip(env, 'WIPi_MTT', queues)

#             # hold the remaining 34 shells
#             for shell_uid in pallet[2:]:
#                 queues['hold'].append(shell_uid)
#                 # stamp the moment it enters hold
#                 unit_record[shell_uid]['HoldEntryTime'] = env.now
#                 log_move(env, shell_uid, 'WIPo_HDT', 'hold', 'split4')
#                 log_wip(env, 'hold', queues)

#         yield env.timeout(0.05)

# def hold_and_split(env, cfg, queues, batch_size=36):
#     """
#     Every time 36 shells accumulate at WIPo_HDT:
#       – send the first 2 whole shells to WIPi_CUT for test cutting
#       – hold the remaining 34 shells in 'hold'
#     """
#     while True:
#         if len(queues['WIPo_HDT']) >= batch_size:
#             pallet = [queues['WIPo_HDT'].pop(0) for _ in range(batch_size)]

#             # --- 1) send sample shells to CUT ------------------------
#             for shell_uid in pallet[:cfg.CUT_SAMPLE_COUNT]:
#                 queues['test_feed'].append(shell_uid)         # whole shell
#                 log_move(env, shell_uid, 'WIPo_HDT', 'test_feed', 'to_cut')
#             log_wip(env, 'test_feed', queues)                 # one snapshot

#             # --- 2) park the rest in HOLD ---------------------------
#             for shell_uid in pallet[cfg.CUT_SAMPLE_COUNT:]:
#                 queues['hold'].append(shell_uid)
#                 unit_record[shell_uid]['HoldEntryTime'] = env.now
#                 log_move(env, shell_uid, 'WIPo_HDT', 'hold', 'split4')
#             log_wip(env, 'hold', queues)

#         yield env.timeout(0.05)

def hold_and_split(env, cfg, queues, batch_size=36):
    """
    Sampling rule (v2):
      • Accumulate THREE full pallets (3 × 36 = 108 shells) from WIPo_HDT
      • When the 3rd pallet arrives, pull **2 shells** off it →
        send them to CUT/TT (via test_feed)
      • Park ALL remaining shells (the whole 1st + 2nd pallets,
        plus 34 shells of the 3rd) in 'hold'  ➜ 106 shells total
    """
    pallet_counter = 0          # 1, 2, 3 …  reset after every trio

    while True:
        if len(queues['WIPo_HDT']) >= batch_size:
            pallet = [queues['WIPo_HDT'].pop(0) for _ in range(batch_size)]
            pallet_counter = (pallet_counter + 1) % 3   # 0 on every 3-rd pallet

            # --- 1) sample only on the 3-rd pallet -------------------
            start_idx = 0
            if pallet_counter == 0:                     # third pallet of the trio
                for shell_uid in pallet[:cfg.CUT_SAMPLE_COUNT]:
                    queues['test_feed'].append(shell_uid)
                    log_move(env, shell_uid, 'WIPo_HDT', 'test_feed', 'to_cut')
                log_wip(env, 'test_feed', queues)
                start_idx = cfg.CUT_SAMPLE_COUNT        # skip the sampled shells

            # --- 2) park the rest in HOLD ----------------------------
            for shell_uid in pallet[start_idx:]:
                queues['hold'].append(shell_uid)
#                 unit_record[shell_uid]['HoldEntryTime'] = env.now
                log_move(env, shell_uid, 'WIPo_HDT', 'hold', 'split4')
            log_wip(env, 'hold', queues)

        yield env.timeout(0.05)
        

# def hold_release(env, cfg, queues):
#     """
#     Release one 34-shell pallet for each full group of 6 test-pieces
#     that arrive in 'scrap'.
#     """
#     while True:
#         # wait for at least one test-set
#         while len(queues['scrap']) < cfg.CUT_SAMPLE_COUNT * 3:
#             yield env.timeout(0.1)

#         sets_ready    = len(queues['scrap']) // (cfg.CUT_SAMPLE_COUNT * 3)
#         pallets_ready = len(queues['hold'])  // cfg.HDT_PALLET_SIZE
#         n = min(sets_ready, pallets_ready)

#         # consume scrap pieces
#         for _ in range(n * cfg.CUT_SAMPLE_COUNT * 3):
#             queues['scrap'].pop(0)
#         log_wip(env, 'scrap', queues)

#         # release matching pallets
#         for _ in range(n * cfg.HDT_PALLET_SIZE):
#             uid = queues['hold'].pop(0)
#             unit_record[uid]['HoldExitTime'] = env.now
#             queues['WIPi_HS'].append(uid)
#             log_move(env, uid, 'hold', 'WIPi_HS', 'release4')
#             log_wip(env, 'WIPi_HS', queues)

#         yield env.timeout(0.05)

def hold_release(env, cfg, queues):
    """
    Release logic for the v2 sampler:
      • Each set of 6 scrap pieces (2 shells × 3) unlocks
        THREE pallets (3 × 34 = 102 shells) from 'hold'.
    """
    pieces_per_set = cfg.CUT_SAMPLE_COUNT * 3   # still = 6
    pallets_per_set = 3

    while True:
        # wait until at least one complete test-piece set exists
        while len(queues['scrap']) < pieces_per_set:
            yield env.timeout(0.1)

        sets_ready    = len(queues['scrap']) // pieces_per_set
        pallets_ready = len(queues['hold'])    // cfg.HDT_PALLET_SIZE
        full_triplets = pallets_ready // pallets_per_set   # groups of 3 pallets
        n_sets = min(sets_ready, full_triplets)            # how many to release

        if n_sets == 0:
            yield env.timeout(0.05)
            continue

        # --- consume scrap pieces -----------------------------------
        for _ in range(n_sets * pieces_per_set):
            queues['scrap'].pop(0)
        log_wip(env, 'scrap', queues)

        # --- release 3 pallets per set ------------------------------
        for _ in range(n_sets * pallets_per_set * cfg.HDT_PALLET_SIZE):
            uid = queues['hold'].pop(0)
#             unit_record[uid]['HoldExitTime'] = env.now
            queues['WIPi_HS'].append(uid)
            log_move(env, uid, 'hold', 'WIPi_HS', 'release4')
        log_wip(env, 'WIPi_HS', queues)

        yield env.timeout(0.05)
        
def hs_to_fg4(env, cfg, queues, finished_goods4, batch_size=34):
    """Forklift moves 34-shell pallets WIPo_HS → finished_goods_4."""
    t_trans = cfg.network['WIPo_HS']['transport_times']
    t_trans = t_trans[0] if isinstance(t_trans, (list, tuple)) else t_trans
    while True:
        if len(queues['WIPo_HS']) >= batch_size:
            pallet = [queues['WIPo_HS'].pop(0) for _ in range(batch_size)]
            with helpers.forklifts.request() as req:
                yield req;  yield env.timeout(t_trans)
            for uid in pallet:
                unit_record[uid]["Stage4Storage"] = env.now      # stamp once
                queues['finished_goods3'].append(uid)
                log_move(env, uid, 'WIPo_HS', 'finished_goods4', 'batch4')
                log_wip (env, 'finished_goods4', queues)
        else:
            yield env.timeout(0.05)

# ──────────────────────────────────────────────────────────────────────────
# 4.  Generic machine coroutine  (HT supports capacity 8; SPHDT/HDT handshake)
# --------------------------------------------------------------------------
# ──────────────────────────────────────────────────────────────────────────
# 4.  Generic machine coroutine  (HT supports capacity 8; SPHDT/HDT handshake;
#     CUT machines split into 3 pieces)
# --------------------------------------------------------------------------

def machine_processor(env, name, cfg, queues):
    """
    PO, CUT, HT(8-up), SPHDT (token), HDT (token-return), …
    Ensures test pieces (_p in UnitID) at CUT go ONLY to WIPi_MTT.
    """
    normal_q = cfg.MACHINE_INPUT[name]
    is_test  = name in CUT_MACHINES
    is_HT    = (name == 'HT')
    is_sphdt = name.startswith('SPHDT')
    is_hdt   = name.startswith('HDT')
    BATCH_HT = 8

    while True:
        # ─── HT: real 8-up batch ─────────────────────────────────────
        if is_HT:
            if len(queues[normal_q]) < BATCH_HT:
                yield env.timeout(0.05)
                continue
            pallet = [queues[normal_q].pop(0) for _ in range(BATCH_HT)]
            for uid in pallet:
                log_move(env, uid, normal_q, name, 'start')
            log_wip(env, normal_q, queues)
            yield env.timeout(cfg.network[name]['process_time'])
            for uid in pallet:
                queues['WIPo_HT'].append(uid)
                log_move(env, uid, name, 'WIPo_HT', 'finish')
                log_wip(env, 'WIPo_HT', queues)
            continue

        # ─── SPHDT handshake ─────────────────────────────────────────
#         if is_sphdt:
#             if not queues[normal_q]:
#                 yield env.timeout(0.05); continue
#             yield queues['hdt_token'].get(1)
#             if not queues[normal_q]:
#                 yield queues['hdt_token'].put(1); yield env.timeout(0); continue
#             uid, srcQ = queues[normal_q].pop(0), normal_q
#             log_wip(env, normal_q, queues)
        # ─── SPHDT handshake & routing to its matching HDT ───────────
        if is_sphdt:
            if not queues[normal_q]:
                yield env.timeout(0.05)
                continue
            # grab the HDT‐token
            yield queues['hdt_token'].get(1)
            # pop a shell
            if not queues[normal_q]:
                # no shell to process → return token
                yield queues['hdt_token'].put(1)
                yield env.timeout(0)
                continue
            uid, srcQ = queues[normal_q].pop(0), normal_q
            log_wip(env, normal_q, queues)

#         # ─── CUT machines pluck from test_feed 1st ───────────────────
#         elif is_test and queues['test_feed']:
#             uid, srcQ = queues['test_feed'].pop(0), 'test_feed'
    # ─── CUT machines pluck raw shells from test_feed ───
        elif is_test and queues['test_feed']:
            uid, srcQ = queues['test_feed'].pop(0), 'test_feed'

        # ─── everyone else pulls normally ────────────────────────────
        elif queues.get(normal_q):
            uid, srcQ = queues[normal_q].pop(0), normal_q
            log_wip(env, normal_q, queues)

        # ─── nothing to do ───────────────────────────────────────────
        else:
            yield env.timeout(0.05)
            continue

        # ─── run the machine cycle ───────────────────────────────────
        log_move(env, uid, srcQ, name, 'start')
        ptime = cfg.network[name]['process_time'] / cfg.network[name]['OEE']
        yield env.timeout(ptime)

        # ─── HDT returns the token ───────────────────────────────────
        if is_hdt:
            yield queues['hdt_token'].put(1)

        # ─── SPHDT pushes to WIPi_HDT and continues ─────────────────
#         if is_sphdt:
#             queues['WIPi_HDT'].append(uid)
#             log_move(env, uid, name, 'WIPi_HDT', 'finish')
#             log_wip(env, 'WIPi_HDT', queues)
#             continue
        if is_sphdt:
            # name is "SPHDT1" or "SPHDT2", so map to "WIPi_HDT1"/"WIPi_HDT2"
            dst = f"WIPi_HDT{name[-1]}"
            queues[dst].append(uid)
            log_move(env, uid, name, dst, 'finish')
            log_wip(env, dst, queues)
            continue

#         # ─── **CUT test‐piece intercept** ───────────────────────────
#         if is_test and '_p' in uid:
#             queues['WIPi_MTT'].append(uid)
#             log_move(env, uid, name, 'WIPi_MTT', 'finish')
#             log_wip(env, 'WIPi_MTT', queues)
#             continue
        # ─── after processing time, split at CUT: handle all CUT outputs here
#         if is_test:
#             # split this shell into 3 pieces
#             for piece_idx in (1, 2, 3):
#                 piece_uid = f"{uid}_p{piece_idx}"
#                 unit_record[piece_uid] = {
#                     "UnitID": piece_uid,
#                     "ParentID": uid,
#                     "SAW": unit_record[uid].get("SAW"),
#                     "ArrivalTime": unit_record[uid].get("ArrivalTime")
#                 }
#             # only send pieces to MTTs whose OEE > 0
#             mtt_inputs = ['WIPi_MTT1','WIPi_MTT2']
#             # filter to only the UP machines
#             active = [
#                 q for q in mtt_inputs
#                 if machine_status.get(q.replace('WIPi_',''), False)
#             ]
#             if active:
#                 dest = min(active, key=lambda q: len(queues[q]))
#                 queues[dest].append(piece_uid)
#                 log_move(env, piece_uid, name, dest, 'finish_cut')
#                 log_wip(env, dest, queues)
#             else:
#                 # no MTT up: requeue the piece and wait a bit
#                 queues['test_feed'].insert(0, piece_uid)
#             continue

        # split this shell into 3 pieces *and* send each one
        # ─── CUT machines: split each test‐shell into 3 pieces ─────────
        if is_test:
            # only ever split the raw shell you just processed
            mtt_inputs = ['WIPi_MTT1','WIPi_MTT2']
            active_mtts = [
                q for q in mtt_inputs
                if machine_status.get(q.replace('WIPi_',''), False)
            ]
            for piece_idx in (1, 2, 3):
                piece_uid = f"{uid}_p{piece_idx}"
                unit_record[piece_uid] = {
                    "UnitID":     piece_uid,
                    "ParentID":   uid,
                    "SAW":        unit_record[uid].get("SAW"),
                    "ArrivalTime":unit_record[uid].get("ArrivalTime")
                }
                if active_mtts:
                    dest = min(active_mtts, key=lambda q: len(queues[q]))
                    queues[dest].append(piece_uid)
                    log_move(env, piece_uid, name, dest, 'finish_cut')
                    log_wip(env, dest, queues)
                else:
                    # requeue if no MTT is available
                    queues['test_feed'].insert(0, piece_uid)
            continue
        # ─── normal routing for everything else ─────────────────────
        out = cfg.network[name]['output']
        if isinstance(out, list):
            for o in out:
                queues[o].append(uid)
                log_move(env, uid, name, o, 'finish')
                log_wip(env, o, queues)
        else:
            queues[out].append(uid)
            log_move(env, uid, name, out, 'finish')
            log_wip(env, out, queues)


# ──────────────────────────────────────────────────────────────────────────
# 5.  Batch mover (forklift) & foot mover helpers
# --------------------------------------------------------------------------
def batch_mover(env, src, dest, queues, t_trans, batch_size):
    while True:
        if len(queues[src]) >= batch_size:
            pallet = [queues[src].pop(0) for _ in range(batch_size)]
            with helpers.forklifts.request() as req:
                yield req;  yield env.timeout(t_trans)
            for uid in pallet:
                queues[dest].append(uid)
                log_move(env, uid, src, dest, 'batch4')
                log_wip (env, dest, queues)
        else:
            yield env.timeout(0.05)

def batch_feeder(env, wipo, queues, dests, tts, batch_size=42):
    """
    Pull full pallets from `wipo` (a string) and send to the
    shortest active buffer in `dests`, skipping any machine with
    OEE=0 via machine_status.
    """
    t_trans = tts[0] if isinstance(tts, (list, tuple)) else tts

    while True:
        if len(queues[wipo]) < batch_size:
            yield env.timeout(0.05)
            continue

        pallet = [queues[wipo].pop(0) for _ in range(batch_size)]
        for uid in pallet:
            # filter only UP machines
            active = [
                d for d in dests
                if machine_status.get(d.replace('WIPi_',''), False)
            ]
            if not active:
                # no buffer up → requeue rest and wait
                queues[wipo][0:0] = [uid] + pallet[pallet.index(uid)+1:]
                yield env.timeout(0.05)
                break

            dest = min(active, key=lambda d: len(queues[d]))
            yield env.timeout(t_trans)
            queues[dest].append(uid)
            log_move(env, uid, wipo, dest, 'batch4')
            log_wip(env, dest, queues)
        else:
            # completed without break
            continue

        yield env.timeout(0.05)
def foot_mover(env, src, dest, queues, t_trans):
    while True:
        if queues[src]:
            uid = queues[src].pop(0)
            yield env.timeout(t_trans)
            queues[dest].append(uid)
            log_move(env, uid, src, dest, 'move4')
            log_wip (env, dest, queues)
        else:
            yield env.timeout(0.05)
            
# def foot_batch_mover(env, src, queues, dests, tts, batch_size):
#     """
#     Wait until `batch_size` units accumulate in `src`, then pick them all
#     up at once (no forklift) and carry to the shortest active dest.
#     """
#     # normalize transport times
#     t_list = tts if isinstance(tts, (list, tuple)) else [tts]
#     while True:
#         if len(queues[src]) < batch_size:
#             yield env.timeout(0.05)
#             continue

#         # grab the whole batch
#         batch = [queues[src].pop(0) for _ in range(batch_size)]

#         # pick the shortest queue among dests
#         dest = min(dests, key=lambda d: len(queues[d]))
#         travel = t_list[dests.index(dest)] if len(t_list) > 1 else t_list[0]

#         # single foot‐carry
#         yield env.timeout(travel)
#         for uid in batch:
#             queues[dest].append(uid)
#             log_move(env, uid, src, dest, 'foot')
#             log_wip(env, dest, queues)

def foot_batch_mover(env, src, queues, dests, tts, batch_size):
    """
    Wait until `batch_size` units accumulate in `src`, then carry
    them all at once to the shortest active dest (no forklift).
    """
    # normalize transport times
    t_list = tts if isinstance(tts, (list, tuple)) else [tts]

    while True:
        if len(queues[src]) < batch_size:
            yield env.timeout(0.05)
            continue

        # grab the whole batch
        batch = [queues[src].pop(0) for _ in range(batch_size)]

        # filter only the UP TT inputs
        active = [
            d for d in dests
            if machine_status.get(d.replace('WIPi_',''), False)
        ]
        if not active:
            # no TT up → put batch back and wait
            queues[src][0:0] = batch
            yield env.timeout(0.05)
            continue

        # pick the shortest of the active queues
        dest = min(active, key=lambda q: len(queues[q]))
        travel = t_list[dests.index(dest)] if len(t_list) > 1 else t_list[0]

        # foot carry
        yield env.timeout(travel)
        for uid in batch:
            queues[dest].append(uid)
            log_move(env, uid, src, dest, 'foot')
            log_wip(env, dest, queues)
            
def hdt_to_hold_batch(env, queues, t_trans=1.6504, pallet_size=42):
    """Fork-lift batches 42 units from WIPo_HDT → hold in one trip."""
    while True:
        if len(queues['WIPo_HDT']) >= pallet_size:
            pallet = [queues['WIPo_HDT'].pop(0) for _ in range(pallet_size)]
            start = env.now
            yield env.timeout(t_trans)               # travel time
            queues['hold'].extend(pallet)
            for uid in pallet:
                log_move(env, uid, 'WIPo_HDT', 'hold', 'start', start)
                log_move(env, uid, 'WIPo_HDT', 'hold', 'end',   env.now)
        else:
            yield env.timeout(0.05)                  # poll

# ──────────────────────────────────────────────────────────────────────────
# 6.  Final pallet out of HS → finished_goods4
# --------------------------------------------------------------------------
def final_batch_hs(env, cfg, queues, finished_goods4, batch_size=42):
    t_trans = cfg.network['WIPo_HS']['transport_times']
    t_trans = t_trans[0] if isinstance(t_trans,(list,tuple)) else t_trans
    while True:
        if len(queues['WIPo_HS']) >= batch_size:
            pallet = [queues['WIPo_HS'].pop(0) for _ in range(batch_size)]
            with helpers.forklifts.request() as req:
                yield req;  yield env.timeout(t_trans)
            for uid in pallet:
                unit_record[uid]["Stage4Storage"] = env.now  
                finished_goods4.append(uid)
                log_move(env, uid, 'WIPo_HS', 'finished_goods4', 'batch4')
                log_wip (env, 'finished_goods4', queues)
        else:
            yield env.timeout(0.05)

def build(env, cfg, queues, finished_goods3, finished_goods4):
    global next_fail_time
    next_fail_time = cfg.TT_FAIL_INTERVAL
    net = cfg.network


    # make sure these queues are plain Python lists
    for q in [
        'WIPo_HDT','test_feed','hold','scrap','WIPi_HS',
        'WIPi_PO1','WIPi_PO2','WIPi_PO3','WIPi_PO4','WIPi_PO5','WIPi_PO6',
        'WIPo_PO1','WIPo_PO2','WIPo_PO3','WIPo_PO4','WIPo_PO5','WIPo_PO6',
        'WIPi_HT','WIPo_HT','WIPi_SPHDT', 'WIPi_HDT1', 'WIPi_HDT2',
        'WIPi_CUT','WIPo_CUT','WIPi_MTT1','WIPi_MTT2','WIPo_MTT1','WIPo_MTT2','WIPi_TT1','WIPi_TT2',
        'WIPo_HS'
    ]:
        queues[q] = []
    queues['finished_goods3'] = finished_goods3
    queues['finished_goods4'] = finished_goods4
    
    
#     queues['WIPo_HS']       = finished_
#     queues['finished_goods4'] = finished_goods4   
    

    # ---------- PROCESSES --------------------------------------------------
    # feeder
    env.process(batch_feeder(env,
                      'finished_goods3',
                      queues,
                      ['WIPi_PO1','WIPi_PO2','WIPi_PO3',
                       'WIPi_PO4','WIPi_PO5','WIPi_PO6'],
                      cfg.network['finished_goods3']['transport_times'], batch_size=42))

    # split & hold logic
    env.process(hold_and_split(
        env, cfg, queues,
        batch_size=cfg.HDT_PALLET_SIZE
    ))
    env.process(hold_release(env, cfg, queues))

    # token for SPHDT↔HDT
    queues['hdt_token'] = simpy.Container(env, init=2, capacity=2)

    # machines (POs, HT, SPHDT, HDT, CUTs, MTT, TT, HS)
    for m in ['PO1','PO2','PO3','PO4','PO5','PO6','HT','SPHDT1','SPHDT2','HDT1','HDT2',
              *CUT_MACHINES,'MTT1','MTT2','TT1','TT2','HS1','HS2']:
        if helpers.machine_status.get(m, True):  # Only start if machine is enabled
            env.process(machine_processor(env, m, cfg, queues))

    # batch-move 42 from each PO output into HT input
    t_PO = cfg.network['finished_goods3']['transport_times']
    t_PO = t_PO[0] if isinstance(t_PO, (list,tuple)) else t_PO
    for po in ('PO1','PO2','PO3','PO4','PO5','PO6'):
        env.process(batch_mover(
            env,
            f'WIPo_{po}',
            'WIPi_HT',
            queues,
            t_PO, batch_size=42
        ))

    # *** NEW *** 42-unit forklift move  WIPo_HT → WIPi_SPHDT
    t_HT = cfg.network['WIPo_HT']['transport_times']
    t_HT = t_HT[0] if isinstance (t_HT, (list, tuple)) else t_HT
    env.process(batch_mover(
        env,
        'WIPo_HT',
        'WIPi_SPHDT',
        queues,
        t_HT, batch_size=36
    ))

    # foot movers CUT→MTT and MTT→TT
#     t_cut = cfg.network['WIPo_CUT']['transport_times']
#     t_cut = t_cut[0] if isinstance(t_cut, (list, tuple)) else t_cut
#     env.process(foot_mover(env,'WIPo_CUT','WIPi_MTT',queues,t_cut))

    # use our stage1.move helper for round‐robin to shortest queue
    env.process(move(env,
                     'WIPo_CUT',
                     queues,
                     cfg.network['WIPo_CUT']['next'],        # ['WIPi_MTT1','WIPi_MTT2']
                     cfg.network['WIPo_CUT']['transport_times']))

#     t_mtt = cfg.network['WIPo_MTT']['transport_times']
#     t_mtt = t_mtt[0] if isinstance(t_mtt, (list, tuple)) else t_mtt
#     env.process(foot_mover(env,'WIPo_MTT','WIPi_TT',queues,t_mtt))

    # final pallet out of HS
    env.process(final_batch_hs(
        env, cfg, queues, finished_goods4,
        batch_size=cfg.HDT_PALLET_SIZE    # 34, from config.py
    ))
    
    # ─── MTT1 & MTT2 → TT1/TT2 (hand‐carry full 6‐piece pallet) ────────
    piece_batch = cfg.CUT_SAMPLE_COUNT * 3  # =6 pieces per test
    for mtt in ('WIPo_MTT1','WIPo_MTT2'):
        net_entry = cfg.network[mtt]
        env.process(foot_batch_mover(
            env,
            mtt,
            queues,
            net_entry['next'],             # ['WIPi_TT1','WIPi_TT2']
            net_entry['transport_times'],
            batch_size=piece_batch
        ))
    