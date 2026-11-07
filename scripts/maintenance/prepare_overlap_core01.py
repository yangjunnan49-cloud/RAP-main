"""Freeze one pipeline interface and byte-identical existing finalization body."""
import time
START=time.monotonic()
import sys,ast,inspect,resource,traceback
from pathlib import Path
import overlap_core01 as p
def run():
    ok=False;error=None
    try:
        p.d.verify();assert p.read(p.BASE/'ADMISSION.json')['G_repeat_admission_passed'];assert p.used()<p.CAP
        original=inspect.getsource(p.d.worker);marker='    slam.generate_new_node();slam.local_map_graph.erase_last_local_map();initial='
        assert original.count(marker)==1
        body=original[original.index(marker):]
        header='from overlap_core01 import np,time,r,old,FINE,AD,module,cap,save,read\n'
        signature='def finish(cell,s,m,key,n,dest,c,slam,recorder,membership,o,fixed,reset_events,begin,timing,chain):\n'
        final=Path(__file__).with_name('overlap_finalize01.py');source=header+signature+body;compile(source,str(final),'exec')
        original_body=ast.parse('def finish():\n'+body).body[0].body
        assert ast.dump(ast.Module(body=original_body,type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=ast.parse(source).body[1].body,type_ignores=[]),include_attributes=False)
        with final.open('x') as f:f.write(source)
        main=Path(p.__file__);text=main.read_text()
        for expression in ['distance=np.linalg.norm(raw,axis=1)','front_points=legacy_f32_correction(raw[distance>=1.5].copy()).astype(np.float32)','map_points=kitti_vertical_correction(raw[(distance>=1.5)&(distance<=80.)].copy())','binding._correct_kitti_scan(binding._Vector3dVector(raw.astype(np.float64)))','front.register(front_points).copy()','slam.process_scan(map_points,timestamps)']:
            assert expression in text and expression in original,expression
        cells=[]
        for rep in (1,2,3):
            for si,s in enumerate(p.d.SEQS):
                for mi,m in enumerate(('G','K')):
                    for scheduler in (('S','P') if (rep+si+mi)%2==0 else ('P','S')):cells.append(dict(repeat=rep,sequence=s,mode=m,scheduler=scheduler,key=f'r{rep}_{s}_{m}_{scheduler}'))
        p.save(p.BASE/'schedule.json',dict(utc=p.now(),cells=cells,seed_tuning=False));assert len(cells)==72
        oldwrapper=main.with_name('launch_raw_input_run06.py');ws=oldwrapper.read_text().replace('import raw_input_system06 as d','import overlap_core01 as d').replace('run06','run').replace('LAUNCH_BINDING06','LAUNCH_BINDING').replace("d.BASE/'VARIANT02_FREEZE.json'","d.BASE/'EXECUTION_FREEZE.json'")
        wrapper=main.with_name('launch_overlap01.py');compile(ws,str(wrapper),'exec')
        with wrapper.open('x') as f:f.write(ws)
        for file in (main,final,wrapper,main.with_name('synthetic_overlap01.py')):compile(file.read_text(),str(file),'exec')
        for name in ('G','K'):p.save(p.BASE/f'config_{name}.json',p.read(p.d.BASE/f'config_{name}.json'))
        paths=[Path(__file__),main,final,wrapper,main.with_name('synthetic_overlap01.py'),main.with_name('invoke_raw_guard06.ps1'),p.BASE/'OWNER_SCOPE.md',p.BASE/'DESIGN.md',p.BASE/'THREADING_ADDENDUM.md',p.BASE/'PROTOCOL.md',p.BASE/'ADMISSION_SOURCE_FREEZE.json',p.BASE/'ADMISSION.json',p.BASE/'schedule.json',p.BASE/'config_G.json',p.BASE/'config_K.json',p.d.BASE/'CLOSE_DELIVERY_SEAL.json']
        p.save(p.BASE/'EXECUTION_FREEZE.json',dict(utc=p.now(),files={str(x):p.sha(x) for x in paths},finalization_AST_exact=True,source_numeric_calls_exact=True,original_raw_source_freeze=p.sha(p.d.BASE/'freeze.json'),G_gate_m=.001,G_rotation_gate=1e-5,cells=72,raw_launch_admitted=False,original_scope_remaining_seconds=p.CAP-p.used()))
        print('P0 interface/finalization/schedule frozen, no raw launch before synthetic',flush=True);ok=True
    except BaseException as e:error=repr(e);traceback.print_exc()
    finally:p.save(p.SUP/'prepare/child_exit.json',dict(utc=p.now(),success=ok,error=error,wall_seconds=time.monotonic()-START,**p.process_usage(),GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='prepare';run()
