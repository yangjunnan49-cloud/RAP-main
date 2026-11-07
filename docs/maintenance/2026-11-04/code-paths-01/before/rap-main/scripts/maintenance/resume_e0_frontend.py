"""Resume only unfinished E0 cells; preserve original frozen runner and outputs."""
import ast,inspect,json,sys,time
from pathlib import Path
import e0_frontend as e

def freeze_resume():
    e.verify_freeze(raw=True)
    assert not (e.BASE/'selection.json').exists()
    assert (e.BASE/'odom-05-O').is_dir() and not list((e.BASE/'odom-05-O').iterdir())
    inherited={}
    for arm in e.ARMS:
        d=e.BASE/f'odom-00-{arm}';p=e.np.load(d/'poses.npy');e.verify_geometry(p)
        assert e.read(d/'source_ids.json')==list(range(e.COUNTS['00']))
        calculated=e.evaluate('00',p);saved=e.read(d/'metrics.json')
        for frame in ['lidar','camera']:
            for k,v in calculated[frame].items():assert abs(v-saved[frame][k])<1e-9
        for name in ['poses.npy','source_ids.json','metrics.json']:inherited[str(d/name)]=e.sha(d/name)
    sources=[Path(__file__),e.BASE/'RESUME_ANNEX_01.md',e.MAIN/'scripts/maintenance/validate_e0_frontend.py']
    for p in sources:
        if p.suffix=='.py':ast.parse(p.read_text())
    e.save(e.BASE/'resume_freeze.json',dict(utc=e.datetime.now(e.timezone.utc).isoformat(),
        sources={str(p):e.sha(p) for p in sources},inherited=inherited,original_freeze_sha256=e.sha(e.BASE/'freeze.json')))
    print('Resume freeze complete; inherited 4 KITTI00 cells',flush=True)

def run_resume():
    frozen=e.read(e.BASE/'resume_freeze.json')
    for group in ['sources','inherited']:
        for p,h in frozen[group].items():assert e.sha(p)==h,p
    e.verify_freeze()
    (e.BASE/'resume-01').mkdir(exist_ok=False)
    # Execute the exact frozen run function with administrative continuation only.
    # Explicit assertions below fail if the original template ever changes.
    src=inspect.getsource(e.run)
    old="verify_freeze();(BASE/'INCOMPLETE').write_text('E0 running\\n')"
    assert old in src;src=src.replace(old,'verify_freeze()')
    anchor="        results[seq]={}\n        for arm,"
    replacement="""        results[seq]={}
        if seq=='00':
            for arm in ARMS:
                out=BASE/f'odom-{seq}-{arm}'
                results[seq][arm]=read(out/'metrics.json')
            ref=np.asarray(epm.load_kitti_format(str(OLD/f'full-kitti{seq}-01/pipeline/odom_poses.txt')))
            delta=float(np.max(np.abs(ref-np.load(BASE/'odom-00-O/poses.npy'))))
            assert delta<=1e-5
            deltas[seq]=delta
            continue
        for arm,"""
    assert anchor in src;src=src.replace(anchor,replacement)
    old="out=BASE/f'odom-{seq}-{arm}';out.mkdir(exist_ok=False)"
    assert old in src;src=src.replace(old,"out=BASE/'resume-01'/f'odom-{seq}-{arm}';out.mkdir(exist_ok=False)")
    src=src.replace('start<7200','start<5400').replace('7200-(time.monotonic()-start)','5400-(time.monotonic()-start)')
    e.save(e.BASE/'resume_effective_source.json',dict(source=src,scope='Administrative skip/path/time-reserve changes only'))
    ns=dict(vars(e));exec(compile(src,'<frozen E0 continuation>','exec'),ns);ns['run']()
    f=e.read(e.BASE/'execution.json')
    e.save(e.BASE/'resume_accounting.json',dict(resumed_process_wall_s=f['wall_s'],
        inherited_complete_cell_wall_s=sum(e.read(e.BASE/f'odom-00-{a}/metrics.json')['wall_s'] for a in e.ARMS),
        interrupted_cell_wall_s=None,prior_budget_reserve_s=1800))
if __name__=='__main__':{'freeze':freeze_resume,'run':run_resume}[sys.argv[1]]()
