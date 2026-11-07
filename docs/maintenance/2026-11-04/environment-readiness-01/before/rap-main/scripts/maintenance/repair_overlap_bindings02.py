"""One metadata namespace repair, original failure/cap/protocol remain historical."""
import time
START=time.monotonic()
import sys,ast,symtable,builtins,resource,traceback,importlib.util
from pathlib import Path
import overlap_core01 as old
def run():
    ok=False;error=None
    try:
        old.verify();assert not old.read(old.SUP/'run/child_exit.json')['success'];assert old.used()<old.CAP
        first=old.BASE/'bank/r1_00_G_P';failure=old.read(first/'worker_exit.json');assert 'now' in failure['error'] and not failure['success']
        assert old.read(first/'producer_exit.json')['success'];assert (first/'poses.npy').exists() and (first/'source_binding.json').exists()
        main=Path(old.__file__);code=main.read_text().replace("BASE/'bank'","BASE/'bank02'").replace("BASE/'bank_seal.json'","BASE/'bank_seal02.json'").replace("SUP/'run'","SUP/'run02'").replace("assert stage=='run';run_bank()","assert stage=='run02';run_bank()").replace('from overlap_finalize01 import finish','from overlap_finalize02 import finish')
        marker="    for p,h in read(BASE/'EXECUTION_FREEZE.json')['files'].items():assert sha(p)==h,p"
        assert code.count(marker)==1
        code=code.replace(marker,marker+"\n    for p,h in read(BASE/'EXECUTION02_FREEZE.json')['files'].items():assert sha(p)==h,p")
        new=main.with_name('overlap_core02.py');compile(code,str(new),'exec')
        # Exact worker statements after only output route + module-name normalization.
        def fn(text,name):return ast.dump(next(x for x in ast.parse(text).body if isinstance(x,ast.FunctionDef) and x.name==name),include_attributes=False)
        expected=main.read_text().replace("BASE/'bank'","BASE/'bank02'").replace('overlap_finalize01','overlap_finalize02')
        assert fn(expected,'worker')==fn(code,'worker')
        with new.open('x') as f:f.write(code)
        original=main.with_name('overlap_finalize01.py');final=main.with_name('overlap_finalize02.py');fs=original.read_text().replace('from overlap_core01 import np,time,','from overlap_core02 import np,time,now,')
        assert fn(original.read_text(),'finish')==fn(fs,'finish')
        with final.open('x') as f:f.write(fs)
        wrapper=main.with_name('launch_overlap01.py');nw=main.with_name('launch_overlap02.py');ws=wrapper.read_text().replace('import overlap_core01 as d','import overlap_core02 as d').replace("SUP/'run/","SUP/'run02/").replace("d.run('run',False)","d.run('run02',False)").replace("sys.argv[1]=='run'","sys.argv[1]=='run02'").replace('LAUNCH_BINDING.json','LAUNCH_BINDING02.json');compile(ws,str(nw),'exec')
        with nw.open('x') as f:f.write(ws)
        # Symbol-table globals: actual referenced names, not attribute-name guesses.
        spec=importlib.util.spec_from_file_location('overlap_finish_binding02',final);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        table=next(x for x in symtable.symtable(fs,str(final),'exec').get_children() if x.get_name()=='finish');names=sorted(x.get_name() for x in table.get_symbols() if x.is_global() and x.is_referenced())
        missing=[x for x in names if x not in module.__dict__ and not hasattr(builtins,x)];assert not missing,missing
        doc=old.BASE/'BINDING02_SUPPLEMENT.md';doc.write_text('''# One metadata-global repair, before any accuracy read

Original firstP00 computed all4541 scans, source frontend check, complete fine graph and pose/source/hash outputs, then failed at execution-metadata `now()` because the copied helper import omitted now. Original worker remainsFAILED, original bank and all costs immutable. No GT/paired candidate metrics were read. Synthetic IPC/map tests had not exercised metadata helper globals.

Owner's existing continuation/fix authorization covers this mechanical namespace correction. This supplement admits exactly one missing-import repair and one re-execution of this failed cell, superseding the original no-retry rule only for this implementation fault. No successful cell exists to replay. New bank02/run02/seal02 routes preserve old artifacts; original72-cell schedule starts unchanged, no partial-result selection/reclassification. Original failed216.3564823s remains in the SAME9000s account. No queue/seed/config/source-math/performance/accuracy-gate rescue or cap reset.

New helper adds only imported global now. Finalization function AST equals original exactly; worker AST equals after output route/module-name normalization. Symbol-table analysis checks every referenced global against the actual imported module/builtins before raw launch. Existing synthetic IPC/order/map/reset evidence remains applicable to the identical interface. This does not claim the original worker succeeded or replace historical failures. Subsequent scientific/gate failures do not authorize another candidate/parameter retry.
''')
        old.save(old.BASE/'BINDING02_GLOBAL_CHECK.json',dict(utc=old.now(),passed=True,referenced_globals=names,missing_globals=missing,worker_AST_equal_after_routes=True,final_function_AST_exact=True,new_GT_numeric_read=False,failed_original_worker_preserved=True))
        files=[Path(__file__),new,final,nw,doc,old.BASE/'BINDING02_GLOBAL_CHECK.json',old.BASE/'EXECUTION_FREEZE.json',old.SUP/'run/child_exit.json',old.SUP/'run/exit.json',first/'worker_exit.json']
        old.save(old.BASE/'EXECUTION02_FREEZE.json',dict(utc=old.now(),files={str(x):old.sha(x) for x in files},shared_original_P0_cap=9000,charged_before_repair=old.used(),only_missing_global_import_and_output_routes=True,no_successful_cell_replay=True))
        print('P0 now import repaired; all finalization globals resolved; original failure retained',flush=True);ok=True
    except BaseException as e:error=repr(e);traceback.print_exc()
    finally:old.save(old.SUP/'binding02/child_exit.json',dict(utc=old.now(),success=ok,error=error,wall_seconds=time.monotonic()-START,**old.process_usage(),GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='binding02';run()
