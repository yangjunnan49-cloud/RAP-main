from pathlib import Path
import hashlib,json,sys,time
import numpy as np
from scipy.spatial.transform import Rotation
MAIN=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent;SLAM=MAIN.parent/'RAP-SLAM'
sys.path[:0]=[str(SLAM),str(SLAM/'scripts'),str(BASE)]
from repeat_systems import read,save,sha,COUNTS,DATA,verify
import eval_paper_metrics as epm
from rap_slam import real_dataset
def independent_ate(gt,est):
 # First-pose anchors agree with the frozen metric's gauge convention.
 g=(np.linalg.inv(gt[0])@gt)[:,:3,3];e=(np.linalg.inv(est[0])@est)[:,:3,3]
 x=e-e.mean(0);y=g-g.mean(0)
 u,_,v=np.linalg.svd(x.T@y);d=np.eye(3);d[2,2]=np.linalg.det(v.T@u.T)
 r=v.T@d@u.T
 return float(np.sqrt(np.mean(np.sum((x@r.T-y)**2,axis=1))))
def independent_segments(gt,est):
 lengths=np.zeros(len(gt))
 for i in range(1,len(gt)):lengths[i]=lengths[i-1]+np.linalg.norm(gt[i,:3,3]-gt[i-1,:3,3])
 records=[]
 for a in range(0,len(gt),10):
  for distance in range(100,801,100):
   b=a
   while b<len(gt) and lengths[b]<=lengths[a]+distance:b+=1
   if b==len(gt):continue
   relative_g=np.linalg.solve(gt[a],gt[b]);relative_e=np.linalg.solve(est[a],est[b]);error=np.linalg.solve(relative_e,relative_g)
   records.append((a,b,distance,float(np.linalg.norm(error[:3,3])/distance),float(np.arccos(np.clip((np.trace(error[:3,:3])-1)*.5,-1,1))/distance)))
 return records
def metrics(seq,model,dest):
 n=COUNTS[seq];gt_cam=np.array(epm.load_kitti_format(str(DATA/'poses'/f'{seq}.txt')))
 tr=real_dataset._read_calib_transform(str(DATA/'sequences'/seq/'calib.txt'));inv=np.linalg.inv(tr)
 gt_lidar=inv@gt_cam@tr
 if model=='RAP-SLAM':
  summary=read(dest/'summary.json');cfg=summary['config'];frames=read(dest/'source_frames.json')
  assert summary['n_scans']==n and summary['odometry_backend']=='kiss-icp'
  assert frames['source_frame_ids']==list(range(n))
  assert cfg['apply_kitti_205'] and cfg['real_seq']==seq
  for key,val in {'odom_max_range':80.,'odom_min_range':1.5,'odom_voxel':.8,'seed':42,'rap_steps':5,'rap_max_points':4000,'multigen_k':1,'max_candidates':12,'loop_nms_width':0,'loop_weighting':'relfloor','robust_kernel':'huber','skip_loop_closure':False,'no_rap_features':False,'deskew':False,'allow_odom_fallback':False}.items():assert cfg[key]==val,(key,cfg[key])
  est_lidar=np.array(epm.load_kitti_format(str(dest/'optimized_poses.txt')));est_cam=tr@est_lidar@inv
  events=[json.loads(s) for s in (dest/'verification_measurements.jsonl').read_text().splitlines()]
  starts={e['attempt_id'] for e in events if e['event']=='candidate_started'}
  ends={e['attempt_id']:e for e in events if e['event']=='candidate_finished'}
  assert starts==ends.keys() and len(starts)==summary['n_loop_candidates']
  assert all(e['status'] in ('accepted','rejected') for e in ends.values())
  edges=read(dest/'accepted_loops.json');assert len(edges)==summary['n_loops_accepted']
  assert {e['measurement_id'] for e in edges}=={e['selected_measurement_id'] for e in ends.values() if e['status']=='accepted'}
  source=dest/'optimized_poses.txt';loops=len(edges)
 else:
  paths=list(dest.rglob(f'{seq}_poses_kitti.txt'));assert len(paths)==1;source=paths[0]
  est_cam=np.array(epm.load_kitti_format(str(source)));est_lidar=inv@est_cam@tr;loops=None
 assert est_cam.shape==est_lidar.shape==gt_cam.shape==gt_lidar.shape==(n,4,4)
 assert np.isfinite(est_lidar).all()
 assert np.max(np.abs(est_lidar[:,:3,:3].transpose(0,2,1)@est_lidar[:,:3,:3]-np.eye(3)))<1e-4
 assert np.max(np.abs(np.linalg.det(est_lidar[:,:3,:3])-1))<1e-4
 m=epm.evaluate_pair(list(gt_cam),list(est_cam),list(range(n)))
 l=epm.evaluate_pair(list(gt_lidar),list(est_lidar),list(range(n)))
 a=independent_ate(gt_lidar,est_lidar);assert abs(a-l['ape_aligned_rmse'])<1e-8
 seg=independent_segments(gt_cam,est_cam);assert len(seg)==m['kitti_segments']
 maximum=0.
 for independent,frozen in zip(seg,m['kitti_segment_records']):
  assert independent[:3]==(frozen['first'],frozen['last'],frozen['length_m'])
  delta=max(abs(independent[3]-frozen['translation_fraction']),abs(independent[4]-frozen['rotation_rad_per_m']));maximum=max(maximum,delta)
 assert maximum<1e-9,maximum
 return {'ter':m['kitti_ter_pct'],'rer':m['kitti_rer_deg100m'],'ate':l['ape_aligned_rmse'],'loops':loops,'frames':n,'source':str(source),'sha256':sha(source),'segment_count':len(seg),'independent_ate_delta':abs(a-l['ape_aligned_rmse']),'independent_segment_delta':maximum}
def main():
 verify();f=read(BASE/'evaluation_freeze.json');assert f['sha256']==sha(__file__)
 start=time.monotonic();execution=read(BASE/'execution.json');assert execution['complete_runs']==36
 sources={}
 for row in execution['rows']:
  dest=BASE/row['name']
  files=[dest/'optimized_poses.txt',dest/'odom_poses.txt',dest/'summary.json',dest/'run_manifest.json',dest/'source_frames.json',dest/'verification_measurements.jsonl',dest/'accepted_loops.json'] if row['model']=='RAP-SLAM' else list(dest.rglob(f"{row['sequence']}_poses_kitti.txt"))
  sources.update({str(p):sha(p) for p in files})
 save(BASE/'trajectory_seal.json',sources)
 rows=[]
 for row in execution['rows']:
  m=metrics(row['sequence'],row['model'],BASE/row['name']);rows.append({**row,**m})
  print('Validated',row['name'],m['ter'],m['ate'],flush=True)
 statistics={}
 for model in ['RAP-SLAM','KISS-SLAM']:
  statistics[model]={}
  for seq in COUNTS:
   cell=[r for r in rows if r['model']==model and r['sequence']==seq];assert len(cell)==3
   statistics[model][seq]={key:{'values':[r[key] for r in cell],'mean':float(np.mean([r[key] for r in cell])),'std':float(np.std([r[key] for r in cell],ddof=0)),'min':float(min(r[key] for r in cell))} for key in ['ter','rer','ate']}
 cohort={}
 for model in statistics:
  cohort[model]={}
  for name,seqs in {'00/05/06':['00','05','06'],'07/09/10':['07','09','10'],'all6':list(COUNTS)}.items():
   repetitions=[{'rep':rep,**{key:float(np.mean([r[key] for r in rows if r['model']==model and r['rep']==rep and r['sequence'] in seqs])) for key in ['ter','rer','ate']}} for rep in range(1,4)]
   best=min(repetitions,key=lambda x:(x['ter'],x['ate'],x['rep']))
   cohort[model][name]={'repetitions':repetitions,'best_single_rep':best,'summary':{key:{'mean':float(np.mean([r[key] for r in repetitions])),'std':float(np.std([r[key] for r in repetitions],ddof=0))} for key in ['ter','rer','ate']}}
 verify(raw=True)
 wall=time.monotonic()-start;assert wall+execution['wall_s']<=7200
 save(BASE/'results.json',{'rows':rows,'statistics':statistics,'cohorts':cohort,'evaluation_wall_s':wall,'complete_runs':36,'independent_metrics_validated':True,'scope':'fresh complete fixed-pipeline repeats; no tuning or new scientific method'})
 save(BASE/'validation.json',{'passed':True,'checks':['historical source/input identities','36 complete pipelines','exact frames/config/candidate completion/edge binding','proper finite poses','independent anchored alignment','explicit independent KITTI segments','all repeat and cohort statistics'],'total_segment_records':sum(r['segment_count'] for r in rows),'max_ate_delta':max(r['independent_ate_delta'] for r in rows),'max_segment_delta':max(r['independent_segment_delta'] for r in rows)})
 (BASE/'INCOMPLETE').unlink();print('ALL repeat metrics independently validated',flush=True)
if __name__=='__main__':main()
