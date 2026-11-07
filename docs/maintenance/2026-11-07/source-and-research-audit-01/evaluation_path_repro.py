from pathlib import Path
import tempfile,sys,json
sys.path.insert(0,str((Path(__file__).resolve().parent/'source/RAP-main')))
from rap_runtime.launch import parser,plan
with tempfile.TemporaryDirectory(prefix='rap-source-audit-') as d:
 r=Path(d); poses=r/'input/trajectories';data=r/'input/dataset';poses.mkdir(parents=True);(data/'poses').mkdir(parents=True);(data/'sequences/00').mkdir(parents=True)
 for p in [poses/'kitti00_poses_kitti.txt',data/'poses/00.txt',data/'sequences/00/calib.txt']:p.write_text('fixture: path check only\n')
 output=r/'runs/my-evaluation'
 args=parser().parse_args(['evaluate','--slam-root',str((Path(__file__).resolve().parent/'source/RAP-SLAM')),'--poses-dir',str(poses),'--dataset-root',str(data),'--method-label','audit','--sequences','00','--output',str(output),'--check'])
 result=plan(args,[])
 try:
  str((poses/'kitti00_poses_kitti.txt').resolve().relative_to(output.parent.resolve()))
  error=None
 except ValueError as e:error=str(e)
 out={'launcher_check_errors':result['errors'],'evaluator_relative_to_operation_error':error,'input_and_output_are_separate':True}
 print(json.dumps(out,indent=2));(Path(__file__).resolve().parent/'evaluation_path_repro.json').write_text(json.dumps(out,indent=2))
