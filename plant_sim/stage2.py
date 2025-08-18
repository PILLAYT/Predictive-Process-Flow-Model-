# plant_sim/stage2.py
# -----------------------------------------------------------
# Stage-2 flow: batch movers, ROD / RID / BR → finished
# -----------------------------------------------------------
import simpy
from . import config as cfg
from .helpers import log_move, log_wip, unit_record, downtime, machine_status
import plant_sim.helpers as helpers

# use the MACHINE_INPUT you defined in config.py
MACHINE_INPUT = cfg.MACHINE_INPUT
UNLOAD_TIME  = 0.5    # time for operator to place one shell on conveyor
CONV_TIME    = 0       # gravity transit time; keep 0 unless you want a delay
PALLET_SIZE  = 42

# ---------- batch mover: from one WIPo_ buffer to shortest dest ------
def batch_move(env, wipo, queues, dests, tts, batch_size=42):
    if not isinstance(tts, list):
        tts = [tts] * len(dests)
    while True:
        if len(queues[wipo]) >= batch_size:
            batch = [queues[wipo].pop(0) for _ in range(batch_size)]
            idx  = min(range(len(dests)),
                       key=lambda i: len(queues[dests[i]]))
            dest = dests[idx]

            # request a forklift before transporting batch
            with helpers.forklifts.request() as req:
                yield req
                yield env.timeout(tts[idx])

            queues[dest].extend(batch)
            log_wip(env, dest, queues)
            for u in batch:
                log_move(env, u, wipo, dest, "batch")
        else:
            yield env.timeout(0.05)

# ---------- generic machine ( ROD / RID / BR) --------------------
# def machine(env, name, proc_time, queues, out_name):
#     """Generic machine: waits until (a) it’s up, and (b) it has work."""
#     in_buf = MACHINE_INPUT.get(name, name)
#     while True:
#         if machine_status.get(name, True) and queues[in_buf]:
#             uid = queues[in_buf].pop(0)

#             # Simulate gantry transfer delay for ROD machines
#             if name.startswith("ROD"):
#                 yield env.timeout(cfg.network['WIPi_ROD']['transport_times'])

#             log_move(env, uid, in_buf, name, "start")
#             yield env.timeout(proc_time)
#             queues[out_name].append(uid)
#             log_move(env, uid, name, out_name, "finish")
#             log_wip(env, out_name, queues)
#         else:
#             yield env.timeout(0.05)

def machine(env, name, proc_time, queues, out_name):
    in_buf = cfg.MACHINE_INPUT.get(name, name)

    if not machine_status.get(name, True):
        print(f"[BLOCKED] Machine {name} was scheduled but is disabled")
        return  # Hard exit: do not run process

    while True:
        if machine_status.get(name, True) and queues[in_buf]:
            uid = queues[in_buf].pop(0)
            log_move(env, uid, in_buf, name, "start")
            yield env.timeout(proc_time)
            queues[out_name].append(uid)
            log_move(env, uid, name, out_name, "finish")
            log_wip(env, out_name, queues)
        else:
            yield env.timeout(0.05)

            
def rod_to_rid_one(env, queues, wipo_rod, t_trans):
    """Move each shell from WIPo_ROD# to the *shortest* WIPi_RID#."""
    rid_inputs = [
        'WIPi_RID1','WIPi_RID2','WIPi_RID3',
        'WIPi_RID4','WIPi_RID5','WIPi_RID6'
    ]

    while True:
        # nothing to do if no parts
        if not queues[wipo_rod]:
            yield env.timeout(0.05)
            continue

        # pull one shell
        uid = queues[wipo_rod].pop(0)

        # find only the UP RID buffers
        active = [
            d for d in rid_inputs
            if machine_status.get(d.replace('WIPi_',''), False)
        ]
        if not active:
            # no RID up: put it back and wait
            queues[wipo_rod].insert(0, uid)
            yield env.timeout(0.05)
            continue

        # pick the least-loaded active buffer
        dest = min(active, key=lambda d: len(queues[d]))

        # travel & deliver
        yield env.timeout(t_trans)
        queues[dest].append(uid)
        log_move(env, uid, wipo_rod, dest, 'rod_to_rid')
        log_wip(env, dest, queues)

# ---------- final batch to finished_goods ----------------------------
def final_batch(env, wipo, queues, finished_goods2, t_trans, batch_size=42):
    while True:
        if len(queues[wipo]) >= batch_size:
            batch = [queues[wipo].pop(0) for _ in range(batch_size)]

            with helpers.forklifts.request() as req:
                yield req
                yield env.timeout(t_trans)

            finished_goods2.extend(batch)
            for u in batch:
                unit_record[u]["FinalStorageTime"] = env.now
                log_move(env, u, wipo, "finished_goods2", "batch")
        else:
            yield env.timeout(0.05)
            
# ---------- operator unload: pallet → gravity conveyor --------------
def operator_unload(env, queues):
    """Keep placing shells on the conveyor until the pallet is empty or
       the conveyor is full (capacity 42)."""
    while True:
        # only work if both a pallet shell and conveyor space exist
        if queues['WIPo_GantryIn'] and len(queues['WIPo_GantryConv']) < PALLET_SIZE:
            uid = queues['WIPo_GantryIn'].pop(0)
            yield env.timeout(UNLOAD_TIME)

            queues['WIPo_GantryConv'].append(uid)
            log_move(env, uid, 'WIPo_GantryIn', 'WIPo_GantryConv', 'unload')
            log_wip(env, 'WIPo_GantryConv', queues)

        else:
            yield env.timeout(0.05)

# ---------- gravity conveyor: feed to shared WIPi_ROD --------------------
def gravity_to_shared_rod(env, queues):
    """Shells fall from conveyor into shared WIPi_ROD queue."""
    while True:
        if queues['WIPo_GantryConv']:
            uid = queues['WIPo_GantryConv'].pop(0)
            yield env.timeout(CONV_TIME)
            queues['WIPi_ROD'].append(uid)
            log_move(env, uid, 'WIPo_GantryConv', 'WIPi_ROD', 'conv_feed')
            log_wip(env, 'WIPi_ROD', queues)
        else:
            yield env.timeout(0.05)

# ---------- pallet move: RID → BR (forklift) ------------------------
def rid_pallet_move(env, queues, wipo_rid, wipi_br_list, t_trans):
    """Batch-move shells from WIPo_RID# to the *shortest* WIPi_BR#."""
    while True:
        if len(queues[wipo_rid]) < PALLET_SIZE:
            yield env.timeout(0.05)
            continue

        # pull a full pallet
        batch = [queues[wipo_rid].pop(0) for _ in range(PALLET_SIZE)]

        # filter only UP BR buffers
        active = [
            d for d in wipi_br_list
            if machine_status.get(d.replace('WIPi_',''), False)
        ]
        if not active:
            # no BR up: put back the pallet and wait
            queues[wipo_rid][0:0] = batch
            yield env.timeout(0.05)
            continue

        # pick the least-loaded active buffer
        dest = min(active, key=lambda d: len(queues[d]))

        # forklift & deliver
        with helpers.forklifts.request() as req:
            yield req
            yield env.timeout(t_trans)

        queues[dest].extend(batch)
        log_wip(env, dest, queues)
        for u in batch:
            log_move(env, u, wipo_rid, dest, 'batch')

def build(env, cfg, queues, finished_goods, finished_goods2):

    net = cfg.network

    # 1. forklift pallet: finished_goods → WIPo_GantryIn
    env.process(batch_move(env,
                           'finished_goods',
                           queues,
                           net['finished_goods']['next'],        # ['WIPo_GantryIn']
                           net['finished_goods']['transport_times']))

    # 2. operator unload & gravity conveyor
    env.process(operator_unload(env, queues))
    env.process(gravity_to_shared_rod(env, queues))
    
    for w in ('WIPo_ROD1','WIPo_ROD2','WIPo_ROD3','WIPo_ROD4','WIPo_ROD5','WIPo_ROD6','WIPo_ROD7','WIPo_ROD8','WIPo_ROD9','WIPo_ROD10'):
        env.process(rod_to_rid_one(env, queues, w, cfg.network[w]['transport_times']))

    # 3. pallet moves RID → BR  (one process per WIPo_RID#)
    for rid_out in ('WIPo_RID1', 'WIPo_RID2', 'WIPo_RID3', 'WIPo_RID4','WIPo_RID5','WIPo_RID6'):
        env.process(rid_pallet_move(env,
                                    queues,
                                    rid_out,
                                    ['WIPi_BR1','WIPi_BR2','WIPi_BR3','WIPi_BR4','WIPi_BR5','WIPi_BR6'],
                                    net[rid_out]['transport_times']))

    # 4. ROD machines
    for rod in ("ROD1","ROD2","ROD3","ROD4","ROD5","ROD6","ROD7","ROD8","ROD9","ROD10"):
        if machine_status.get(rod, True):
            env.process(machine(env, rod,
                                net[rod]['process_time'],
                                queues, net[rod]['output']))

    # 5. RID machines
    for rid in ("RID1","RID2","RID3","RID4","RID5","RID6"):
        if machine_status.get(rid, True):
            env.process(machine(env, rid,
                                net[rid]['process_time'],
                                queues, net[rid]['output']))

    # 6. BR machines
    for br in ("BR1","BR2","BR3","BR4","BR5","BR6"):
        if machine_status.get(br, True):
            env.process(machine(env, br,
                                net[br]['process_time'],
                                queues, net[br]['output']))

    # 7. final pallet BR → finished_goods2
    for w in ("WIPo_BR1","WIPo_BR2","WIPo_BR3","WIPo_BR4","WIPo_BR5","WIPo_BR6"):
        env.process(final_batch(env,
                                w,
                                queues,
                                finished_goods2,
                                net[w]['transport_times']))