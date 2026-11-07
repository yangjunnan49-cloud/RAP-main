"""All72 post-seal equivalence, inherited metrics and actual runtime assessment."""
import time
START=time.monotonic()
import sys,signal,traceback,resource
from pathlib import Path
import numpy as np
import overlap_core02 as p
from overlap_metrics02 import evaluate_rows
BASE=p.BASE;SUP=p.SUP
def group_summary(values):
    a=np.asarray(values,dtype=float);return dict(mean=float(a.mean()),std=float(a.std(ddof=1)),minimum=float(a.min()),maximum=float(a.max()))
def loop_ids(binding):return [(x['source'],x['target']) for x in binding['loop_attempts'] if x['accepted']]
def run():
    remaining=p.CAP-p.used();assert remaining>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('P0 cumulative cap')));signal.alarm(max(1,int(remaining)));ok=False;error=None
    try:
        p.verify();assert p.read(BASE/'bank_seal02.json')['cells']==72 and p.read(BASE/'binding_audit.json')['passed']
        for file,h in p.read(BASE/'AUDIT_EVALUATION02_FREEZE.json')['files'].items():assert p.sha(file)==h,file
        p.save(BASE/'ASSESSMENT_SOURCE_BINDING02.json',dict(utc=p.now(),files={str(x):p.sha(x) for x in (Path(__file__),Path(evaluate_rows.__code__.co_filename),BASE/'PROTOCOL.md',BASE/'bank_seal02.json',BASE/'binding_audit.json')},GT_metric_loop_from_S1=True))
        rows,segments,maximum=evaluate_rows();assert len(rows)==72;lookup={}
        for row in rows:
            key=row['key'];cell=BASE/'bank02'/key;worker=p.read(cell/'worker_exit.json');prod=p.read(cell/'producer_exit.json');wall=p.read(SUP/'run02'/key/'controller_exit.json')['wall_seconds'];pt=np.load(cell/'pipeline_timing.npy');assert pt.shape==(row['frames'],3) and np.isfinite(pt).all() and (pt>=0).all()
            cpu=worker['user_CPU_seconds']+worker['system_CPU_seconds']
            if row['scheduler']=='P':cpu+=prod['user_CPU_seconds']+prod['system_CPU_seconds']
            row.update(controller_seconds=wall,CPU_seconds=cpu,peak_process_RSS=max(worker['peak_RSS_bytes'],prod['peak_RSS_bytes']),packet_age_seconds=dict(median=float(np.median(pt[:,2])),p95=float(np.quantile(pt[:,2],.95)),p99=float(np.quantile(pt[:,2],.99)),maximum=float(pt[:,2].max())),consumer_get_or_prepare_wait_seconds=float(pt[:,0].sum()),consumer_verify_seconds=float(pt[:,1].sum()))
            lookup[(row['repeat'],row['sequence'],row['mode'],row['scheduler'])]=row
        per={};means={};labels=['G_S','G_P','K_S','K_P']
        for seq in p.d.SEQS:
            per[seq]={}
            for label in labels:
                selected=[x for x in rows if x['sequence']==seq and x['mode']+'_'+x['scheduler']==label];assert len(selected)==3
                per[seq][label]={k:group_summary([x[k] for x in selected]) for k in ('ate','ter','rer','controller_seconds','CPU_seconds','peak_process_RSS')}
        for label in labels:means[label]={k:float(np.mean([per[s][label][k]['mean'] for s in p.d.SEQS])) for k in ('ate','ter','rer')}
        pairs=[]
        for rep in (1,2,3):
            for seq in p.d.SEQS:
                for mode in ('G','K'):
                    s=lookup[(rep,seq,mode,'S')];q=lookup[(rep,seq,mode,'P')];sp=BASE/'bank02'/s['key'];pp=BASE/'bank02'/q['key'];st=np.load(sp/'poses.npy');pt=np.load(pp/'poses.npy');sb=p.read(sp/'source_binding.json');pb=p.read(pp/'source_binding.json')
                    tr=float(np.max(abs(st[:,:3,3]-pt[:,:3,3])));rot=float(np.max(abs(st[:,:3,:3]-pt[:,:3,:3])))
                    gates=dict(translation=tr<=.001,rotation=rot<=1e-5,reset_ids=sb['reset_anchors']==pb['reset_anchors'],accepted_loop_ids=loop_ids(sb)==loop_ids(pb),ATE=abs(s['ate']-q['ate'])<=1e-4,ter=abs(s['ter']-q['ter'])<=1e-5,rer=abs(s['rer']-q['rer'])<=1e-5,source_chain=sb['consumed_ordered_hash_chain']==pb['consumed_ordered_hash_chain'])
                    pairs.append(dict(repeat=rep,sequence=seq,mode=mode,translation_element_max_m=tr,rotation_element_max=rot,ATE_delta_m=abs(s['ate']-q['ate']),ter_delta_percentage_points=abs(s['ter']-q['ter']),rer_delta_deg100m=abs(s['rer']-q['rer']),gates=gates,equivalence_passed=all(gates.values()),serial_seconds=s['controller_seconds'],parallel_seconds=q['controller_seconds']))
        modes={}
        for mode in ('G','K'):
            ss=[x for x in rows if x['mode']==mode and x['scheduler']=='S'];pp=[x for x in rows if x['mode']==mode and x['scheduler']=='P'];pair=[x for x in pairs if x['mode']==mode]
            serial=sum(x['controller_seconds'] for x in ss);parallel=sum(x['controller_seconds'] for x in pp);assert sum(x['frames'] for x in ss)==sum(x['frames'] for x in pp)==36888
            slowdown={seq:float(np.median([x['controller_seconds'] for x in pp if x['sequence']==seq])/np.median([x['controller_seconds'] for x in ss if x['sequence']==seq])) for seq in p.d.SEQS}
            gates=dict(all18_pair_equivalence=all(x['equivalence_passed'] for x in pair),aggregate_time_reduction_at_least10pct=parallel<=.9*serial,no_sequence_median_slowdown_over5pct=all(x<=1.05 for x in slowdown.values()),all_packet_source_graph_checks=p.read(BASE/'binding_audit.json')['passed'],all_individual_process_RSS_under4GiB=max(x['peak_process_RSS'] for x in ss+pp)<=4*2**30)
            modes[mode]=dict(serial_enclosing_seconds=serial,parallel_enclosing_seconds=parallel,parallel_to_serial_ratio=parallel/serial,time_reduction_percent=100*(1-parallel/serial),serial_batch_FPS=36888/serial,parallel_batch_FPS=36888/parallel,serial_CPU_seconds=sum(x['CPU_seconds'] for x in ss),parallel_CPU_seconds=sum(x['CPU_seconds'] for x in pp),median_sequence_ratios=slowdown,qualification_gates=gates,qualified=all(gates.values()),failed_equivalence_pairs=[f"r{x['repeat']}_{x['sequence']}" for x in pair if not x['equivalence_passed']])
        comparisons={}
        for a,b in [('G_S','K_S'),('G_P','K_S'),('G_P','K_P')]:
            primary=dict(mean_ATE_better=means[a]['ate']<means[b]['ate'],mean_ter_nonworse=means[a]['ter']<=means[b]['ter']+1e-5);safety={f'{s}_{k}':per[s][a][k]['mean']<=per[s][b][k]['mean']+.01 for s in p.d.SEQS for k in ('ter','rer')}
            comparisons[a+'_vs_'+b]=dict(primary=primary,primary_passed=all(primary.values()),safety=safety,safety_passed=all(safety.values()))
        p.save(BASE/'RESULTS02.json',dict(utc=p.now(),rows=rows,per_sequence=per,means=means,pairs=pairs,modes=modes,accuracy_comparisons=comparisons,independent_metric_validation_passed=True,independent_segments=segments,maximum_metric_delta=maximum,whole_native_tree_peak='UNKNOWN',native_auto_threads_preserved=True,equal_CPU_budget_certified=False,online10Hz_claim=False,new_RAP_efficacy=False,defaults_changed=False))
        p.cap();print('P0 assessed',modes,'means',means,flush=True);ok=True
    except BaseException as e:error=repr(e);traceback.print_exc();p.save(BASE/'ASSESSMENT_FAILURE02.json',dict(utc=p.now(),error=error))
    finally:signal.alarm(0);p.save(SUP/'assess/child_exit.json',dict(utc=p.now(),success=ok,error=error,wall_seconds=time.monotonic()-START,**p.process_usage(),GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='assess';run()
