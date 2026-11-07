"""Post-hoc descriptive localization on all original pairs; no new gates/GT."""
from itertools import combinations
import numpy as np
import validation_core as c
def compare(a,b):
    pa=c.OLD/'bank02'/a;pb=c.OLD/'bank02'/b
    ba=c.read(pa/'source_binding.json');bb=c.read(pb/'source_binding.json')
    ta=np.load(pa/'poses.npy');tb=np.load(pb/'poses.npy')
    row=dict(left=a,right=b,final_max=float(np.max(abs(ta-tb))),reset_lists_equal=ba['reset_anchors']==bb['reset_anchors'])
    if '_G_' in a:
        oa=np.load(pa/'odometry.npy');ob=np.load(pb/'odometry.npy')
        ia=np.load(pa/'before_fine.npy');ib=np.load(pb/'before_fine.npy')
        aa=c.read(pa/'anchors.json');ab=c.read(pb/'anchors.json')
        row.update(frontend_bitwise_equal=bool(np.array_equal(oa,ob)),frontend_max=float(np.max(abs(oa-ob))),before_fine_max=float(np.max(abs(ia-ib))),coarse_anchor_max=float(np.max(abs(np.asarray(aa['coarse_poses'])-np.asarray(ab['coarse_poses'])))))
        tr=np.max(abs(ta[:,:3,3]-tb[:,:3,3]),axis=1);rr=np.max(abs(ta[:,:3,:3]-tb[:,:3,:3]),axis=(1,2));failed=np.flatnonzero((tr>.001)|(rr>1e-5))
        row['frames_exceeding_original_matrix_bounds']=len(failed);row['first_such_frame']=int(failed[0]) if len(failed) else None
        h1=np.load(pa/'producer_hashes.npy');h2=np.load(pb/'producer_hashes.npy')
        row['all_fresh_packet_digests_cross_run_equal']=bool(np.array_equal(h1,h2))
    la={x['query_id']:x for x in ba['loop_attempts']};lb={x['query_id']:x for x in bb['loop_attempts']}
    common=sorted(la.keys()&lb.keys());differ=[]
    for key in common:
        x=la[key];y=lb[key];same=all(x[k]==y[k] for k in ('accepted','source','target'))
        delta=None
        if x['pose'] is not None and y['pose'] is not None:delta=float(np.max(abs(np.asarray(x['pose'])-np.asarray(y['pose']))))
        if not same or (delta is not None and delta>1e-12):differ.append(dict(query=key,endpoint_and_accept_equal=same,transform_element_max=delta,left_accepted=x['accepted'],right_accepted=y['accepted']))
    row['common_loop_queries']=len(common);row['different_loop_records']=differ
    return row
def run():
    c.verify();assert c.read(c.OUT/'RESULTS02.json')['modes']['G']['qualified'] is False
    paired=[];within=[]
    for s in c.d.SEQS:
        for rep in (1,2,3):
            for m in ('G','K'):paired.append(compare(f'r{rep}_{s}_{m}_S',f'r{rep}_{s}_{m}_P'))
        for sched in ('S','P'):
            for a,b in combinations((1,2,3),2):within.append(compare(f'r{a}_{s}_G_{sched}',f'r{b}_{s}_G_{sched}'))
        c.cap()
    c.save(c.OUT/'DESCRIPTIVE_EQUIVALENCE.json',dict(posthoc_descriptive_only=True,original_qualification_unchanged=True,GT_reads=0,new_predictions=0,all36_cross_scheduler_pairs=paired,all36_within_G_scheduler_repeat_pairs=within))
    print('Described all36 S/P pairs and36 within-scheduler G repeat pairs; no new qualification',flush=True)
