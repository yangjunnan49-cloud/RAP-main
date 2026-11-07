"""Complete-six portability/equivalence test under original cumulative LMB cap."""
import time
START=time.monotonic()
import os,sys,resource,signal,traceback,subprocess,ast,copy
from pathlib import Path
import numpy as np
import e0_local_map_six as x
r=x.r
BASE=r.MAIN/'docs/maintenance/2026-10-20/e0-anchor-capsule-01'
SUP=BASE/'supervision'
def used():
    total=x.used()
    for d in SUP.glob('*'):
        if d.is_dir():total+=max([r.read(d/n)['wall_seconds'] for n in ('child_exit.json','exit.json') if (d/n).exists()]+[0])
    return total
def ast_check():
    old=Path(r.__file__).with_name('coarse_anchor_fine_control.py');new=BASE/'anchor_fine.py'
    a=copy.deepcopy(next(n for n in ast.parse(old.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='fine'))
    b=next(n for n in ast.parse(new.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='fine')
    a.args.args.append(ast.arg(arg='pose_graph_config'))
    class Change(ast.NodeTransformer):
        def visit_Attribute(self,n):
            if ast.unparse(n)=='r.config().pose_graph_optimizer':return ast.Name(id='pose_graph_config',ctx=ast.Load())
            return self.generic_visit(n)
    a=Change().visit(a);assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
    return dict(passed=True,only_math_source_change='Explicit configuration argument replaces r.config().pose_graph_optimizer',source_sha256=r.sha(old),portable_sha256=r.sha(new))
def native():
    config=r.read(x.OLD/'config.json')['pose_graph_optimizer'];r.save(BASE/'pose_graph_config.json',config);dest=BASE/'cases';dest.mkdir();rows={}
    env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=''
    for s in x.SEQS:
        d=dest/s;d.mkdir();o=r.proper(r.poses(x.src(s)/'odom_poses.txt'));initial_path=(x.BASE if s in x.NEW else x.OLD)/f'bank/{s}/before_fine.npy';initial=np.load(initial_path)
        meta=r.read(x.BASE/f'bank/{s}/source_binding.json') if s in x.NEW else r.read(x.OLD/f'anchor_corrected_bank/{s}/anchors.json')
        np.save(d/'odometry.npy',o);np.save(d/'initial.npy',initial);r.save(d/'anchors.json',dict(anchor_frames=meta['anchor_frames'],coarse_poses=meta['coarse_poses']))
        command=[r.KISS,'-u','-B',str(BASE/'anchor_fine.py'),'--odometry',str(d/'odometry.npy'),'--initial',str(d/'initial.npy'),'--anchors',str(d/'anchors.json'),'--config',str(BASE/'pose_graph_config.json'),'--output',str(d/'G.npy')]
        begin=time.monotonic();p=subprocess.run(command,env=env,timeout=60);assert p.returncode==0
        reference=(x.BASE/f'bank/{s}/G.npy') if s in x.NEW else (x.OLD/f'anchor_corrected_bank/{s}/G.npy');ref=np.load(reference);t=np.load(d/'G.npy');assert t.shape==ref.shape
        error=float(np.max(abs(ref-t)));assert error<=1e-8,error
        rows[s]=dict(frames=len(t),maximum_matrix_delta=error,cli_seconds=time.monotonic()-begin,existing_G_sha256=r.sha(reference),initial_source_sha256=r.sha(initial_path),source_pose_sha256=r.sha(x.src(s)/'odom_poses.txt'))
        print('Portable CLI equivalent',s,error,flush=True)
    r.save(BASE/'EQUIVALENCE.json',dict(utc=r.now(),passed=True,all_six=True,GT_numeric_read=False,new_accuracy_metrics=False,original_failed_safety_unchanged=True,rows=rows,
        peak_child_RSS_bytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*1024))
def run():
    left=1800-used();assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('original cumulative LMB cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None;peak=0
    try:
        x.verify();proof=ast_check();paths=[Path(__file__),BASE/'anchor_fine.py',BASE/'OWNER_SCOPE.md',x.BASE/'bank_seal.json',x.OLD/'anchor_corrected_seal.json']
        r.save(BASE/'FREEZE.json',dict(utc=r.now(),files={str(p):r.sha(p) for p in paths},AST_equivalence=proof,original_LMB_charged_seconds=used(),remaining_original_seconds=left))
        env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';p=subprocess.run([r.KISS,'-u','-B',__file__,'--native'],env=env,timeout=left-1);receipt=r.read(SUP/'capsule_equivalence/native_exit.json');peak=receipt['peak_RSS_bytes'];assert p.returncode==0 and receipt['success']
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=4*2**30
        assert sum(p.stat().st_size for b in (x.OLD,x.BASE,BASE) for p in b.rglob('*') if p.is_file())<=128*2**20;ok=True
    except BaseException as e:err=repr(e);traceback.print_exc();r.save(BASE/'FAILURE_capsule_equivalence.json',dict(utc=r.now(),error=err))
    finally:
        signal.alarm(0);r.save(SUP/'capsule_equivalence/child_exit.json',dict(utc=r.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),GPU_calls=0,charged_original_LMB_cap=True))
    if not ok:sys.exit(1)
if __name__=='__main__':
    if '--native' in sys.argv:
        good=False
        try:native();good=True
        finally:r.save(SUP/'capsule_equivalence/native_exit.json',dict(utc=r.now(),success=good,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)*1024,GPU_calls=0))
    else:assert sys.argv[1]=='capsule_equivalence';run()
