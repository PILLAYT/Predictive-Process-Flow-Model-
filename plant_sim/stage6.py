# plant_sim/stage6.py
# -----------------------------------------------------------------------------
# Stage 6 – RG → SB → NT → BT → MP → FB → FI → D&P → FG6
# -----------------------------------------------------------------------------
# This mirrors Stage 5’s style: each segment has
#   • a feeder/batch-mover coroutine (42‑shell pallets, one forklift trip)
#   • one‑shell machine processors pulling from WIPi_, pushing to WIPo_
# Routing, pallet size, and forklift times are taken **directly** from cfg.network.
# -----------------------------------------------------------------------------

import simpy
from .helpers import log_move, log_wip, unit_record, batch_move
import plant_sim.helpers as helpers
from . import config as cfg

BATCH = getattr(cfg, 'FO_MERGE_CAP', 42)  # pallet size (42 everywhere)
DP_BATCH = 13 

# -----------------------------------------------------------------------------
# Helper: wait till `src` ≥ 42 → forklift pallet to the *shortest* dest queue(s)
# -----------------------------------------------------------------------------

def pallet_mover(env, src, queues, dests, tts):
    if not isinstance(dests, (list, tuple)):
        dests = [dests]
    if not isinstance(tts, (list, tuple)):
        tts = [tts] * len(dests)

    while True:
        if len(queues.get(src, [])) >= BATCH:
            pallet = [queues[src].pop(0) for _ in range(BATCH)]
            # choose dest with fewest shells
            idx = min(range(len(dests)), key=lambda i: len(queues[dests[i]]))
            dest = dests[idx]
            t_trans = tts[idx]

            with helpers.forklifts.request() as req:
                yield req
                yield env.timeout(t_trans)

            for uid in pallet:
                queues[dest].append(uid)
                # stamp Stage‑6 completion time when shell enters FG6
                if dest == 'finished_goods6':
                    unit_record[uid]['Stage6Storage'] = env.now
                log_move(env, uid, src, dest, 'batch6')
                log_wip(env, dest, queues)
        else:
            yield env.timeout(0.05)

# -----------------------------------------------------------------------------
# Helper: single‑shell machine processor
# -----------------------------------------------------------------------------

def machine_processor(env, name, queues):
    in_q  = cfg.MACHINE_INPUT[name]
    out_q = cfg.network[name]['next'][0] if isinstance(cfg.network[name]['next'], list) else cfg.network[name]['next']
    ptime = cfg.network[name]['process_time'] / cfg.network[name]['OEE']

    while True:
        if not queues.get(in_q):
            yield env.timeout(0.05)
            continue
        uid = queues[in_q].pop(0)
        log_move(env, uid, in_q, name, 'start')
        log_wip(env, in_q, queues)
        yield env.timeout(ptime)
        queues[out_q].append(uid)
        log_move(env, uid, name, out_q, 'finish')
        log_wip(env, out_q, queues)

# -----------------------------------------------------------------------------
# 1) Feeder: finished_goods5 → WIPi_RG
# -----------------------------------------------------------------------------

def feeder_fg5_to_rg(env, queues):
    net = cfg.network['finished_goods5']
    dest  = net['next'][0]
    t_tr  = net['transport_times']
    t_tr  = t_tr[0] if isinstance(t_tr, (list, tuple)) else t_tr
    while True:
        if len(queues['finished_goods5']) >= BATCH:
            pallet = [queues['finished_goods5'].pop(0) for _ in range(BATCH)]
            with helpers.forklifts.request() as req:
                yield req
                yield env.timeout(t_tr)
            for uid in pallet:
                queues[dest].append(uid)
                log_move(env, uid, 'finished_goods5', dest, 'batch6')
                log_wip(env, dest, queues)
        else:
            yield env.timeout(0.05)
            
            
# --------------------------------------------------------------------------
# Helper: 13-at-a-time batch processor for D&P1 / D&P2
# --------------------------------------------------------------------------
def dp_batch_processor(env, name, queues):
    """
    Wait until WIPi_D&P# has 13 shells, pull them as one batch,
    process for (process_time / OEE), then drop the same 13 shells
    into WIPo_D&P#.
    """
    in_q  = cfg.MACHINE_INPUT[name]         # e.g. 'WIPi_D&P1'
    out_q = cfg.network[name]['next'][0]    # 'WIPo_D&P1' or D&P2
    ptime = cfg.network[name]['process_time'] / cfg.network[name]['OEE']

    while True:
        if len(queues.get(in_q, [])) < DP_BATCH:
            yield env.timeout(0.05)
            continue

        batch = [queues[in_q].pop(0) for _ in range(DP_BATCH)]
        for uid in batch:
            log_move(env, uid, in_q, name, 'start')
        log_wip(env, in_q, queues)

        yield env.timeout(ptime)

        for uid in batch:
            queues[out_q].append(uid)
            log_move(env, uid, name, out_q, 'finish')
            log_wip(env, out_q, queues)

def build(env, cfg, queues, finished_goods5, finished_goods6):
    """
    Stage 6 build: FG5 → RG(1–12) → SB(5–14) → NT(1–6) → BT(1–6) →
                   MP(1–4) → FB(1–4) → FI(1–4) → D&P(1–4) → FG6
    """
    net = cfg.network

    # ── hookup FG5 feeder → WIPi_RG ───────────────────────────────────────────────
    queues['finished_goods5'] = finished_goods5
    queues.setdefault('WIPi_RG', [])
    queues.setdefault('WIPo_RG', [])
    env.process(batch_move(
        env,
        'finished_goods5',
        queues,
        ['WIPi_RG'],
        net['finished_goods5']['transport_times'],
        batch_size=cfg.FO_MERGE_CAP
    ))

    # ── RG1–RG12: single‐shell → shared WIPo_RG ───────────────────────────────────
    for i in range(1, 13):
        rg = f'RG{i}'
        in_q = 'WIPi_RG'
        out_q = 'WIPo_RG'
        # make sure buffer exists
        queues.setdefault(in_q, [])
        queues.setdefault(out_q, [])
        # only start those machines that are live & OEE>0
        if helpers.machine_status.get(rg, True) and net[rg]['OEE'] > 0:
            env.process(machine_processor(env, rg, queues))

    # ── RG → SB5–SB14 pallet mover ────────────────────────────────────────────────
    env.process(batch_move(
        env,
        'WIPo_RG',
        queues,
        [q for q in net['WIPo_RG']['next']
           # only feed SB buffers whose SB machine is live & OEE>0
           if net[next(iter(net[q]['next']))]['OEE'] > 0
              and helpers.machine_status.get(next(iter(net[q]['next'])), True)
        ],
        net['WIPo_RG']['transport_times'],
        batch_size=cfg.FO_MERGE_CAP
    ))

    # ── SB5–SB14: single‐shell → WIPo_SB# + pallet → NT ──────────────────────────
    for sb_i in range(1, 11):
        sb   = f"SB{sb_i}"
        iq   = f"WIPi_{sb}"
        oq   = f"WIPo_{sb}"
        queues.setdefault(iq, [])
        queues.setdefault(oq, [])
        if helpers.machine_status.get(sb, True) and net[sb]['OEE'] > 0:
            env.process(machine_processor(env, sb, queues))
            # batch‐move 42 from WIPo_SB# into only the live NT-inputs
            env.process(batch_move(
               env,
               oq,
               queues,
               [q for q in net[oq]['next']
                  if net[next(iter(net[q]['next']))]['OEE'] > 0
                     and helpers.machine_status.get(next(iter(net[q]['next'])), True)
               ],
               net[oq]['transport_times'],
               batch_size=cfg.FO_MERGE_CAP
            ))

    # ── NT1–NT6 ───────────────────────────────────────────────────────────────────
    for i in range(1, 7):
        nt = f"NT{i}"
        oq = f"WIPo_{nt}"
        queues.setdefault(oq, [])
        if helpers.machine_status.get(nt, True) and net[nt]['OEE'] > 0:
            env.process(machine_processor(env, nt, queues))
            env.process(batch_move(
                env,
                oq,
                queues,
                [q for q in net[oq]['next']
                   if net[next(iter(net[q]['next']))]['OEE'] > 0
                      and helpers.machine_status.get(next(iter(net[q]['next'])), True)
                ],
                net[oq]['transport_times'],
                batch_size=cfg.FO_MERGE_CAP
            ))

    # ── BT1–BT6 ───────────────────────────────────────────────────────────────────
    for i in range(1, 7):
        bt = f"BT{i}"
        oq = f"WIPo_{bt}"
        queues.setdefault(oq, [])
        if helpers.machine_status.get(bt, True) and net[bt]['OEE'] > 0:
            env.process(machine_processor(env, bt, queues))
            env.process(batch_move(
                env,
                oq,
                queues,
                [q for q in net[oq]['next']
                   if net[next(iter(net[q]['next']))]['OEE'] > 0
                      and helpers.machine_status.get(next(iter(net[q]['next'])), True)
                ],
                net[oq]['transport_times'],
                batch_size=cfg.FO_MERGE_CAP
            ))

    # ── MP1–MP4 (shared WIPi_MP# feeds each MP) ──────────────────────────────────
    for mp in ('MP1','MP2','MP3','MP4'):
        in_q = cfg.MACHINE_INPUT[mp]
        out_q = f"WIPo_{mp}"
        queues.setdefault(in_q, [])
        queues.setdefault(out_q, [])
        if helpers.machine_status.get(mp, True) and net[mp]['OEE'] > 0:
            env.process(machine_processor(env, mp, queues))
            env.process(batch_move(
                env,
                out_q,
                queues,
                [q for q in net[out_q]['next']
                   if net[next(iter(net[q]['next']))]['OEE'] > 0
                      and helpers.machine_status.get(next(iter(net[q]['next'])), True)
                ],
                net[out_q]['transport_times'],
                batch_size=cfg.FO_MERGE_CAP
            ))

    # ── FB1–FB4 ──────────────────────────────────────────────────────────────────
    for fb in ('FB1','FB2','FB3','FB4'):
        in_q = cfg.MACHINE_INPUT[fb]
        out_q = f"WIPo_{fb}"
        queues.setdefault(in_q, [])
        queues.setdefault(out_q, [])
        if helpers.machine_status.get(fb, True) and net[fb]['OEE'] > 0:
            env.process(machine_processor(env, fb, queues))
            env.process(batch_move(
                env,
                out_q,
                queues,
                [q for q in net[out_q]['next']
                   if net[next(iter(net[q]['next']))]['OEE'] > 0
                      and helpers.machine_status.get(next(iter(net[q]['next'])), True)
                ],
                net[out_q]['transport_times'],
                batch_size=cfg.FO_MERGE_CAP
            ))

    # ── FI1–FI4 ──────────────────────────────────────────────────────────────────
    for fi in ('FI1','FI2','FI3','FI4'):
        in_q = cfg.MACHINE_INPUT[fi]
        out_q = f"WIPo_{fi}"
        queues.setdefault(in_q, [])
        queues.setdefault(out_q, [])
        if helpers.machine_status.get(fi, True) and net[fi]['OEE'] > 0:
            env.process(machine_processor(env, fi, queues))
            env.process(batch_move(
                env,
                out_q,
                queues,
                [q for q in net[out_q]['next']
                   if net[next(iter(net[q]['next']))]['OEE'] > 0
                      and helpers.machine_status.get(next(iter(net[q]['next'])), True)
                ],
                net[out_q]['transport_times'],
                batch_size=cfg.FO_MERGE_CAP
            ))


    for dp in ('D&P1', 'D&P2'):
        in_q  = cfg.MACHINE_INPUT[dp]               # e.g. WIPi_D&P1
        out_q = f'WIPo_{dp}'                        # WIPo_D&P1
        queues.setdefault(in_q,  [])                # make sure buffers exist
        queues.setdefault(out_q, [])

        # 1️⃣  Batch-processor: pull 13 shells from WIPi_D&P# → WIPo_D&P#
        if helpers.machine_status.get(dp, True) and cfg.network[dp]['OEE'] > 0:
            env.process(dp_batch_processor(env, dp, queues))

        # 2️⃣  Fork-lift: full pallet from WIPo_D&P# → finished_goods6
        t_dp = cfg.network[out_q]['transport_times']
        t_dp = t_dp[0] if isinstance(t_dp, (list, tuple)) else t_dp

        env.process(batch_move(
            env,
            out_q,                                    # source queue
            queues,
            ['finished_goods6'],                      # destination
            t_dp,                                     # travel time
            batch_size=13,                      # 13 shells
            stamp_field="Stage6Storage"               # ★ stamp Stage-6 time
        ))
