"""Fresh ten-frame pipeline smoke, with actual sparse source-frame identities."""
import json
import subprocess
import sys
from pathlib import Path

root=Path('/mnt/e/githouse/RAP-SLAM')
home=Path('/mnt/e/githouse/RAP-main')
out=home/'.maintenance-archive/2026-09-10-m2-smoke-01'
out.mkdir(parents=True,exist_ok=False)
command=[sys.executable,'-B',str(root/'scripts/run_pipeline.py'),
         '--source','real','--real-root','/mnt/e/githouse/Datasets/data_odometry_velodyne',
         '--real-seq','06','--real-start','128','--real-end','146','--real-stride','2',
         '--real-apply-calib','--skip-loop-closure','--output',str(out)]
with (out/'run.log').open('w') as log:
    process=subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT)
process.check_returncode()
manifest=json.loads((out/'source_frames.json').read_text())
summary=json.loads((out/'summary.json').read_text())
assert manifest['source_frame_ids']==list(range(128,147,2))
assert summary['n_scans']==10 and summary['odometry_backend']=='kiss-icp'
evidence=dict(status='passed',scope='Ten-frame stride-2 integration smoke; no loop inference; not a research score',
              command=command,output=str(out),manifest=manifest,summary=summary)
target=home/'docs/maintenance/2026-09-10/m2-evaluation/pipeline_smoke.json'
with target.open('x') as f:json.dump(evidence,f,indent=2)
print(json.dumps(dict(status='passed',frames=10,source_frame_ids=manifest['source_frame_ids'],backend=summary['odometry_backend'])))
