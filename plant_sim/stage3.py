# plant_sim/stage3.py
# ------------------------------------------
# Stage 3 flow with batch transports and individual moves, with hysteresis throttle:
# 1) finished_goods → WIPi_WC (batch 42, throttle by WIPi_RNB levels)
# 2) WC processes individually → WIPo_WC
# 3) WIPo_WC → WIPi_GR (batch 42)
# 4) GR processes individually → WIPo_GR
# 5) WIPo_GR → NIH1/NIH2 (individual transport)
# 6) NIH1/NIH2 → NP1/NP2 (individual)
# 7) WIPo_NP → WIPi_RNB (regulated pallet move, throttle by RNB input)
# 8) RNB processes individually → WIPo_RNB
# 9) WIPo_RNB → finished_goods_2 (batch 42, stamp exit time)
# ------------------------------------------
import simpy
from . import config as cfg
from .helpers import log_move, unit_record, downtime, machine_status, log_wip
import plant_sim.helpers as h
from .stage1 import move
from .stage2 import batch_move, machine

# ---------- one-by-one crane move: WIPo_WC → WIPi_GR -----------------
# def wc_to_gr_one(env, queues, t_trans, pallet_size=42):
#     while True:
#         if queues['WIPo_WC'] and len(queues['WIPi_GR']) < pallet_size:
#             uid = queues['WIPo_WC'].pop(0)
#             yield env.timeout(t_trans)
#             queues['WIPi_GR'].append(uid)
#             log_move(env, uid, 'WIPo_WC', 'WIPi_GR', 'wc_to_gr')
#             log_wip(env, 'WIPi_GR', queues)
#         else:
#             yield env.timeout(0.05)

def regulated_batch_from_finished(env, queues, src, dests, tts,
                                  batch_size=42, high_limit=490, low_limit=245):
    tts_list = tts if isinstance(tts, (list, tuple)) else [tts]
    starved = False
    while True:
        rnb_depth = len(queues.get('WIPi_RNB', []))
        if not starved and rnb_depth > high_limit:
            starved = True
        elif starved and rnb_depth < low_limit:
            starved = False

        if (not starved) and len(queues.get(src, [])) >= batch_size:
            pallet = [queues[src].pop(0) for _ in range(batch_size)]
            yield env.timeout(tts_list[0])
            dest = dests[0] if not isinstance(dests, str) else dests
            queues[dest].extend(pallet)
            for uid in pallet:
                log_move(env, uid, src, dest, 'batch3')
                log_wip(env, dest, queues)
        else:
            yield env.timeout(0.05)

# def regulated_np_to_rnb(env, queues, src, dest, tts, batch_size=42, limit=450):
#     tts_list = tts if isinstance(tts, (list, tuple)) else [tts]
#     while True:
#         if len(queues.get(dest, [])) <= limit and len(queues.get(src, [])) >= batch_size:
#             pallet = [queues[src].pop(0) for _ in range(batch_size)]
#             yield env.timeout(tts_list[0])
#             queues[dest].extend(pallet)
#             for uid in pallet:
#                 unit_record[uid]['FinalStorage2Time'] = env.now
#                 log_move(env, uid, src, dest, 'batch3')
#                 log_wip(env, dest, queues)
#         else:
#             yield env.timeout(0.05)

def regulated_np_to_rnb(env, queues, src, dests, tts, batch_size=42, limit=450):
    """
    Pull full pallets from `src` and send them (when below `limit`) to the
    shortest queue among `dests`. Throttled by `limit` on each dest's length.
    """
    # normalize transport times and dests
    tts_list = tts if isinstance(tts, (list, tuple)) else [tts]
    dests_list = dests if isinstance(dests, (list, tuple)) else [dests]

    while True:
        # check overall source depth
        if len(queues.get(src, [])) >= batch_size:
            # filter dests whose queue length <= limit
            eligible = [d for d in dests_list if len(queues.get(d, [])) <= limit]
            if eligible:
                # pick the dest with the shortest queue
                dest = min(eligible, key=lambda d: len(queues[d]))
                travel = tts_list[dests_list.index(dest)] if len(tts_list) > 1 else tts_list[0]

                # form the pallet
                pallet = [queues[src].pop(0) for _ in range(batch_size)]
                # travel time
                yield env.timeout(travel)
                # deliver
                for uid in pallet:
                    queues[dest].append(uid)
                    unit_record[uid]['FinalStorage2Time'] = env.now
                    log_move(env, uid, src, dest, 'batch3')
                    log_wip(env, dest, queues)
                continue
        yield env.timeout(0.05)

def gr_pallet_machine(env, proc_time, queues, in_buf, out_buf, pallet_size=42):
    while True:
        if len(queues[in_buf]) >= pallet_size:
            batch = [queues[in_buf].pop(0) for _ in range(pallet_size)]
            for uid in batch:
                log_move(env, uid, in_buf, 'GR', 'start')
            log_wip(env, in_buf, queues)
            yield env.timeout(proc_time)
            for uid in batch:
                queues[out_buf].append(uid)
                log_move(env, uid, 'GR', out_buf, 'finish')
                log_wip(env, out_buf, queues)
        else:
            yield env.timeout(0.05)

def build(env, cfg, queues, finished_goods2, finished_goods3):
    net = cfg.network

    # ───── Register Downtime for All Machines in Stage 3 ─────
    for name in ('WC', 'GR', 'NIH1', 'NIH2', 'NP1', 'NP2'):
        if name in net and 'OEE' in net[name]:
            env.process(downtime(env, name, net[name]['OEE']))
            
     # and the four parallel RNBs
    for i in range(1, 5):
        rnb = f"RNB{i}"
        if rnb in net and 'OEE' in net[rnb]:
            env.process(downtime(env, rnb, net[rnb]['OEE']))

    # ───── Link Buffers ─────
    queues['finished_goods2'] = finished_goods2
    queues['finished_goods3'] = finished_goods3

    # ───── 1) Regulated Batch Feed to WC ─────
    env.process(regulated_batch_from_finished(
        env, queues,
        src='finished_goods2',
        dests=net['finished_goods2']['next'],
        tts=net['finished_goods2']['transport_times'],
        batch_size=42,
        high_limit=490,
        low_limit=245
    ))

    # ───── 2) WC Machine ─────
    if machine_status.get('WC', True):
        env.process(machine(env,
                            'WC',
                            net['WC']['process_time'],
                            queues,
                            net['WC']['output']))

# #     # ───── 3) WC to GR Transfer ─────
#     env.process(wc_to_gr_one(env,
#                               queues,
#                               net['WIPo_WC']['transport_times'],
#                               pallet_size=42))
    env.process(batch_move(
        env,
        'WIPo_WC',                            # source buffer
        queues,
        net['WIPo_WC']['next'],               # should be ['WIPi_GR']
        net['WIPo_WC']['transport_times'],
        batch_size=42
    ))


    # ───── 4) GR Furnace ─────
    if machine_status.get('GR', True):
        env.process(gr_pallet_machine(env,
                                      net['GR']['process_time'],
                                      queues,
                                      'WIPi_GR',
                                      net['GR']['output']))

#     # ───── 5) GR Final Stage ─────
#     if machine_status.get('GR', True):
#         env.process(machine(env,
#                             'GR',
#                             net['GR']['process_time'],
#                             queues,
#                             net['GR']['output']))

    # ───── 6) GR to NIH Move (only to active NIH machines) ─────
    from plant_sim import helpers as h
    def filtered_move(env, wipo, queues, dests, tts, poll=0.05):
        """
        Move one unit from wipo → shortest active destination (filtered by machine_status).
        Skips destinations where machine_status = False.
        """
        if not isinstance(tts, list):
            tts = [tts] * len(dests)

        while True:
            if queues[wipo]:
                # Filter out destinations with machine_status == False
                active_pairs = [
                    (d, t) for d, t in zip(dests, tts)
                    if machine_status.get(d, True)
                ]

                if not active_pairs:
                    yield env.timeout(poll)
                    continue

                dest, t_trans = min(active_pairs, key=lambda pair: len(queues[pair[0]]))
                uid = queues[wipo].pop(0)
                yield env.timeout(t_trans)
                queues[dest].append(uid)

                log_wip(env, dest, queues)
                log_move(env, uid, wipo, dest, 'transport')
            else:
                yield env.timeout(poll)

    env.process(filtered_move(env,
                              'WIPo_GR',
                              queues,
                              net['WIPo_GR']['next'],
                              net['WIPo_GR']['transport_times']))

    # ───── 7) NIH & NP Machines (independent toggles) ─────
    for nih, np in [('NIH1', 'NP1'), ('NIH2', 'NP2')]:
        if not machine_status.get(nih, True):
            continue

        # NIH process
        env.process(machine(env,
                            nih,
                            net[nih]['process_time'],
                            queues,
                            net[nih]['output']))

        # NP process only if machine is up
        if machine_status.get(np, True):
            env.process(machine(env,
                                np,
                                net[np]['process_time'],
                                queues,
                                net[np]['output']))

    # ───── 8) Regulated Pallet to RNB ─────
    env.process(regulated_np_to_rnb(
        env, queues,
        src='WIPo_NP',
        dests=net['WIPo_NP']['next'],              # ['WIPi_RNB1'…'WIPi_RNB4']
        tts=net['WIPo_NP']['transport_times'],
        batch_size=42,
        limit=450
    ))

    # ───── 9) RNB Machine ─────
    for i in range(1, 5):
        name   = f"RNB{i}"
        in_q   = f"WIPi_{name}"
        out_q  = net[name]['output']
        ptime  = net[name]['process_time']
        if machine_status.get(name, True):
            # each RNBi processes individually
            env.process(machine(env,
                                name,
                                ptime,
                                queues,
                                out_q))

    # ───── 10) Final Pallet Move to Finished Goods ─────
    for i in range(1, 5):
        wip_o = f"WIPo_RNB{i}"
        cfg_entry = net[wip_o]
        env.process(batch_move(env,
                               wip_o,
                               queues,
                               cfg_entry['next'],         # ['finished_goods3']
                               cfg_entry['transport_times'],
                               batch_size=42))




