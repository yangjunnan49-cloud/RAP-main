"""Bind inherited source/graph audit and exact metric loop before evaluation."""
import time
START=time.monotonic()
import sys,inspect,resource,traceback
from pathlib import Path
import overlap_core01 as p
def run():
    ok=False;error=None
    try:
        p.verify();assert p.used()<p.CAP
        original=Path(__file__).with_name('audit_raw_input_bindings06.py');source=original.read_text().replace('import raw_input_system06 as d','import overlap_core01 as d').replace("BASE/'bank_seal06.json'","BASE/'bank_seal.json'").replace("BASE/'bank06'","BASE/'bank'").replace("seal['cells']==36","seal['cells']==72").replace("f=d.read(BASE/'freeze.json')","f=d.read(d.d.BASE/'freeze.json')").replace("for cell in f['schedule']:","for cell in d.read(BASE/'schedule.json')['cells']:").replace('cells=36','cells=72').replace('All36','All72')
        token='            rows[key]=dict(frames=n,'
        assert source.count(token)==1
        added='''            ph=np.load(p/'producer_hashes.npy');ch=np.load(p/'consumer_hashes.npy');assert ph.dtype==np.uint8 and ph.shape==(n,32) and np.array_equal(ph,ch)
            info=d.read(p/'pipeline.json');pr=d.read(p/'producer_exit.json');wr=d.read(p/'worker_exit.json')
            assert info['packet_count']==n and info['all_packet_bytes_and_order_verified'] and pr['success'] and wr['success']
            assert max(pr['peak_RSS_bytes'],wr['peak_RSS_bytes'])<=4*2**30
'''
        source=source.replace(token,added+token);new=original.with_name('audit_overlap01.py');compile(source,str(new),'exec')
        with new.open('x') as f:f.write(source)
        # Same calibrated ATE/Horn/KITTI loop; output key only distinguishes service sum.
        e=inspect.getsource(p.d.evaluate);e=e[:e.index('    per={};means={}')]
        e=e.replace('def evaluate():','def evaluate_rows():').replace("BASE/'bank_seal06.json'","BASE/'bank_seal.json'").replace("BASE/'bank06'","BASE/'bank'").replace("seal['cells']==36","seal['cells']==72").replace("BASE/'evaluation06'","BASE/'evaluation'").replace("read(BASE/'freeze.json')['schedule']","read(BASE/'schedule.json')['cells']").replace("f=read(BASE/'freeze.json')","f=read(p.d.BASE/'freeze.json')").replace('frame_latency=dict','frame_service_time=dict')
        head='import numpy as np\nimport overlap_core01 as p\nBASE=p.BASE;r=p.r;read=p.read;save=p.save;sha=p.sha;now=p.now;verify=p.verify;cap=p.cap\n'
        e=head+e+'    return rows,segments,maximum\n';metric=new.with_name('overlap_metrics01.py');compile(e,str(metric),'exec')
        with metric.open('x') as f:f.write(e)
        scope=p.BASE/'BINDING_AUDIT_SCOPE.md';scope.write_text((p.d.BASE/'BINDING_AUDIT_SCOPE.md').read_text()+'''\nP0 adds all72 cells and per-cell producer/consumer packet SHA arrays, exact count/order flags and both process RSS receipts. This verifies exact IPC transmission within each cell. Fresh G odometry may differ within frozen source tolerance between runs, so full pose-containing packet SHA is not claimed bit-identical across independent S/P runs. Common raw hashes, builder/config/source AST and every original prepared frontend buffer contract remain; no separately independent all-point map-preprocessing implementation is claimed. Producer/consumer are cooperative, not OS-isolated.\n''')
        p.save(p.BASE/'AUDIT_EVALUATION_FREEZE.json',dict(utc=p.now(),files={str(x):p.sha(x) for x in (Path(__file__),original,new,metric,scope,p.BASE/'PROTOCOL.md',p.BASE/'EXECUTION_FREEZE.json')},metric_math_from_sealed_S1=True,only_schema_routes_and_service_clock_label_changed=True,GT_numeric_read=False,new_predictions=0))
        print('P0 all72 source/packet audit and inherited exact metric loop bound',flush=True);ok=True
    except BaseException as e:error=repr(e);traceback.print_exc()
    finally:p.save(p.SUP/'prepare_audit/child_exit.json',dict(utc=p.now(),success=ok,error=error,wall_seconds=time.monotonic()-START,**p.process_usage(),GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='prepare_audit';run()
