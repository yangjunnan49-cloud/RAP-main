"""Bind certified original-float32 frontend realization; carry one valid K control."""
import time
START=time.monotonic()
import ast,json,sys,resource,traceback,hashlib,shutil
from pathlib import Path
import certify_raw_input_contract as c
d=c.d;BASE=c.BASE;SUP=c.SUP;R0=c.R0
def run():
    ok=False;err=None
    try:
        d.verify();assert d.read(BASE/'INPUT_CERTIFICATE.json')['passed'] and d.read(BASE/'FRONTEND_ELIGIBILITY.json')['passed'];assert c.used()<7200
        old=Path(__file__).with_name('raw_system_integration03.py');new=old.with_name('raw_input_system04.py');text=old.read_text();source=text
        def replace(a,b):
            nonlocal source
            assert source.count(a)==1,(a,source.count(a));source=source.replace(a,b)
        replace("BASE=r.MAIN/'docs/maintenance/2026-10-20/raw-system-integration-01';SUP=BASE/'supervision'", "BASE=r.MAIN/'docs/maintenance/2026-10-20/raw-input-contract-01';SUP=BASE/'supervision'\nR0=BASE.parent/'raw-system-integration-01'\nsys.path.insert(0,str(BASE))\nfrom legacy_f32_correction import legacy_f32_correction")
        begin=source.index('def used():');end=source.index('def cap():',begin)
        source=source[:begin]+"""def used():
    total=0.
    for root in (R0,BASE):
        for folder in (root/'supervision').glob('*'):
            if folder.is_dir():total+=max([read(folder/n)['wall_seconds'] for n in ('child_exit.json','exit.json') if (folder/n).exists()]+[0])
    return total
"""+source[end:]
        replace("sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())", "sum(p.stat().st_size for root in (R0,BASE) for p in root.rglob('*') if p.is_file())")
        marker="    for p,h in read(BASE/'VARIANT03_FREEZE.json')['files'].items():assert sha(p)==h,p"
        replace(marker,marker+"\n    for p,h in read(BASE/'S1_EXECUTION_FREEZE.json')['files'].items():assert sha(p)==h,p")
        for a,b in [("BASE/'bank03'","BASE/'bank04'"),("BASE/'bank_seal03.json'","BASE/'bank_seal04.json'"),("BASE/'evaluation03'","BASE/'evaluation04'"),("BASE/'results03.json'","BASE/'results04.json'"),("SUP/'run03'","SUP/'run04'")]:source=source.replace(a,b)
        source=source.replace("'run03':run_bank,'evaluate03':evaluate","'run04':run_bank,'evaluate04':evaluate")
        replace("front_points=kitti_vertical_correction(raw[distance>=1.5].copy()).astype(np.float32)","front_points=legacy_f32_correction(raw[distance>=1.5].copy()).astype(np.float32)")
        replace("        front=KissOdometry(max_range=80.,min_range=1.5,voxel_size=.8,deskew=False);", "        prepared_reference=read(BASE/'original_prepared_reference.json')['rows'][s]\n        front=KissOdometry(max_range=80.,min_range=1.5,voxel_size=.8,deskew=False);")
        replace("        after_preprocess=time.perf_counter()", "        if m=='G':\n            point_reference=prepared_reference[i];assert len(front_points)==point_reference['points'] and hashlib.sha256(front_points.tobytes(order='C')).hexdigest()==point_reference['prepared_sha256'],('prepared input contract',s,i)\n        after_preprocess=time.perf_counter()")
        replace("frontend_delta=float(np.max(abs(reference-o)));assert frontend_delta<=1e-5", "frontend_delta=float(np.max(abs(reference-o)))\n        if frontend_delta>1e-5:np.save(dest/'failed_frontend.npy',o);np.save(dest/'failed_initial.npy',initial)\n        assert frontend_delta<=1e-5")
        replace("    for cell in f['schedule']:\n        launch=guard();", "    retained=read(BASE/'RETAINED_K1_FREEZE.json')\n    for p,h in retained['files'].items():assert sha(p)==h,p\n    import shutil\n    shutil.copytree(R0/'bank03/r1_00_K',BASE/'bank04/r1_00_K')\n    retained_dir=SUP/'run04/r1_00_K';retained_dir.mkdir()\n    shutil.copy2(R0/'supervision/run03/r1_00_K/controller_exit.json',retained_dir/'controller_exit.json')\n    save(retained_dir/'retained.json',dict(original_R0_cell=True,no_rerun=True,original_clock_already_charged=True,source_freeze_sha256=sha(BASE/'RETAINED_K1_FREEZE.json')))\n    for cell in f['schedule']:\n        if cell['key']=='r1_00_K':continue\n        launch=guard();")
        compile(source,str(new),'exec')
        def numeric(code,normalize=False):
            tree=ast.parse(code);worker=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='worker')
            if normalize:
                for node in ast.walk(worker):
                    if isinstance(node,ast.Name) and node.id=='legacy_f32_correction':node.id='kitti_vertical_correction'
            names={'front.register','slam.process_scan','slam.generate_new_node','slam.local_map_graph.erase_last_local_map','fine_module.fine','slam.fine_grained_optimization','np.linalg.solve','kitti_vertical_correction','binding._correct_kitti_scan','proper_one'}
            return [ast.dump(n,include_attributes=False) for n in ast.walk(worker) if isinstance(n,ast.Call) and ast.unparse(n.func) in names]
        assert numeric(text)==numeric(source,True)
        with new.open('x',encoding='utf-8') as f:f.write(source)
        wrapper=Path(__file__).with_name('launch_raw_integration_run03.py');outwrapper=wrapper.with_name('launch_raw_input_run04.py');ws=wrapper.read_text().replace('import raw_system_integration03 as d','import raw_input_system04 as d').replace("'LAUNCH_BINDING03.json'","'LAUNCH_BINDING04.json'").replace("SUP/'run03/","SUP/'run04/").replace("d.run('run03',False)","d.run('run04',False)").replace("sys.argv[1]=='run03'","sys.argv[1]=='run04'")
        compile(ws,str(outwrapper),'exec')
        with outwrapper.open('x',encoding='utf-8') as f:f.write(ws)
        for name in ('freeze.json','config_G.json','config_K.json','synthetic.json','VARIANT02_FREEZE.json','VARIANT03_FREEZE.json'):shutil.copy2(R0/name,BASE/name)
        retained_paths=[p for p in (R0/'bank03/r1_00_K').rglob('*') if p.is_file()]+[R0/'supervision/run03/r1_00_K/controller_exit.json']
        assert d.read(R0/'bank03/r1_00_K/worker_exit.json')['success']
        d.save(BASE/'RETAINED_K1_FREEZE.json',dict(utc=d.now(),files={str(p):d.sha(p) for p in retained_paths},predeclared_only_complete_control=True,GT_numeric_read=False,no_rerun=True,no_best_run_selection=True))
        audit_old=Path(__file__).with_name('audit_raw_system_bindings.py');audit_new=audit_old.with_name('audit_raw_input_bindings04.py');aud=audit_old.read_text().replace('import raw_system_integration03 as d','import raw_input_system04 as d').replace("'bank03'","'bank04'").replace("'bank_seal03.json'","'bank_seal04.json'")
        compile(aud,str(audit_new),'exec')
        with audit_new.open('x',encoding='utf-8') as f:f.write(aud)
        shutil.copy2(R0/'BINDING_AUDIT_SCOPE.md',BASE/'BINDING_AUDIT_SCOPE.md')
        paths=[new,outwrapper,Path(__file__),BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',BASE/'legacy_f32_correction.py',BASE/'SOURCE_PREFREEZE.json',BASE/'INPUT_CERTIFICATE.json',BASE/'original_prepared_reference.json',BASE/'FRONTEND_ELIGIBILITY.json',BASE/'ELIGIBILITY_FREEZE.json',BASE/'RETAINED_K1_FREEZE.json',audit_new,BASE/'BINDING_AUDIT_SCOPE.md']
        paths += [BASE/n for n in ('freeze.json','config_G.json','config_K.json','synthetic.json','VARIANT02_FREEZE.json','VARIANT03_FREEZE.json')]
        d.save(BASE/'S1_EXECUTION_FREEZE.json',dict(utc=d.now(),files={str(p):d.sha(p) for p in paths},numeric_call_AST_equal_after_certified_correction_name_normalization=True,
            original_1e5_correspondence_guard_unchanged=True,whole_campaign_cap_seconds=7200,shared_charged_seconds=c.used(),old_R0_failed_result_preserved=True,remaining_new_cells=35,GT_numeric_read=False))
        print('S1 executable bound; certified original input semantics,35 new/1 retained cells; same shared7200s',flush=True);ok=True
    except BaseException as e:err=repr(e);traceback.print_exc()
    finally:d.save(SUP/'prepare04/child_exit.json',dict(utc=d.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0,shared_R0_cap=True))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='prepare04';run()
