"""Complete accounting and portable descriptions; no numerical result changes."""
import time
START=time.monotonic()
import sys,resource,traceback
from pathlib import Path
import raw_input_system06 as d
def run():
    ok=False;error=None
    try:
        d.verify();assert d.used()<7200
        original=Path(__file__).with_name('deliver_raw_input_benchmark06.py');source=original.read_text()
        start=source.index('def costs():');end=source.index('def run():',start)
        source=source[:start]+'''def costs():
    rows=[]
    for root in (R0,BASE):
        for folder in sorted((root/'supervision').iterdir()):
            if not folder.is_dir():continue
            receipts={name:d.read(folder/name) for name in ('child_exit.json','exit.json','wrapper_exit.json','enclosing_upper_bound.json') if (folder/name).exists()}
            if not receipts:continue
            rows.append(dict(scope=root.name,stage=folder.name,enclosing_seconds=max(x['wall_seconds'] for x in receipts.values()),
                receipts={n:dict(success=x.get('success'),exit_code=x.get('exit_code'),wall_seconds=x['wall_seconds']) for n,x in receipts.items()},
                Python_RSS=receipts.get('child_exit.json',{}).get('peak_RSS_bytes'),missing_child_receipt='child_exit.json' not in receipts,
                conservative_upper_bound_used='enclosing_upper_bound.json' in receipts))
    return rows
'''+source[end:]
        token="        d.save(export/'RESULTS.json',result);"
        assert source.count(token)==1
        addition='''        (export/'README.md').write_text("""# Complete fresh-raw trajectory-core G/K, 2026-10-20

36 complete trajectories: sequences00/05/06/07/09/10, G/K, repeats1/2/3. Each *_lidar.txt row contains the first three rows of a4x4 world-from-LiDAR pose, row-major, no alignment/scale fit. Append homogeneous row0 0 0 1. Units meters; frame index is original zero-based sequential scan index. Saved17-digit floats round-trip checked. No frames selected or dropped.

G is experimental fixed-E0 odometry plus native map closures and explicit source-frame anchor fine graph. Every repeat computes fresh E0 from original scans with certified original float32 correction; no cached eligibility poses supplied. K is native KISS-SLAM trajectory core. Minimal trajectory/evidence output only; full native CLI map/occupancy side-products omitted for both. Three fresh-process repeats are exposed development sequences, not independent scenes. First K00 is the single predeclared retained original complete control.

RESULTS.json contains all36 rows, three-repeat per-sequence summaries, six-sequence arithmetic means and separately reported mean objective/safety results. Aligned ATE uses LiDAR poses; KITTI ter/rer use camera calibration internally, but exported poses remain LiDAR and unaligned. OPERATIONAL_RESULTS reports measured batch cost/tail latency; not a guaranteed10Hz service. CONFIG_G/K preserve used configurations. No automatic default promotion/new RAP efficacy/generalization claim.

The precision/fixed-odometry/anchor modules are the tested components, not a standalone data loader or complete environment installer. Raw scans and GT are not included. Full provenance/failure/cost/seal records remain in the companion repository report. Existing library/default/reference/Git state was not changed.
""",encoding='utf-8')
        import shutil
        for name in ('config_G.json','config_K.json'):shutil.copy2(BASE/name,export/name.upper())
        for path in (BASE/'legacy_f32_correction.py',d.AD/'fixed_odometry.py',d.FINE/'anchor_fine.py'):shutil.copy2(path,export/path.name)
'''
        source=source.replace(token,addition+token)
        source=source.replace('独立Horn/KITTI复核','独立Horn/KITTI复核')
        source=source.replace('所有36预测先封存，后读GT。','所有36预测先封存，后读GT。运行中保留跨主机UTC保护失败、响应指针替换冲突和两个准备/记账错误；分别接续5/22个完成单元，从不重放完整单元。最终使用唯一nonce不可变请求/响应，以原2秒单调时钟往返和12GiB条件保护启动。')
        source=source.replace('不重复加内部父子clock。','不重复加内部父子clock。run05观察器中断缺少原生Windows结束收据，使用单独保守包围上界计费；prepare06b缺少子收据而Windows失败收据仍计费，不声称所有阶段成功。')
        output=original.with_name('deliver_raw_input_benchmark07.py');compile(source,str(output),'exec')
        with output.open('x',encoding='utf-8') as f:f.write(source)
        d.save(d.BASE/'DELIVERY07_FREEZE.json',dict(utc=d.now(),files={str(p):d.sha(p) for p in (Path(__file__),original,output,d.BASE/'GUARD06_FREEZE.json')},changes=['all-stage conservative costs including missing child receipts','portable pose README/configs/tested modules','retained-failure disclosure'],new_numeric_predictions=False,new_metrics=False))
        print('Delivery07 frozen; no numerical change',flush=True);ok=True
    except BaseException as e:error=repr(e);traceback.print_exc()
    finally:d.save(d.SUP/'prepare_delivery07/child_exit.json',dict(utc=d.now(),success=ok,error=error,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='prepare_delivery07';run()
