"""Pipeline failure/reuse guards and independent inspection of real run links."""
import json
import hashlib
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import numpy as np
ROOT=Path('/mnt/e/githouse/RAP-SLAM');sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import run_pipeline
import rap_slam.rap_backend as backend_module
from validate_verification_logging import FakeBackend,generation

def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    checks=[]
    with tempfile.TemporaryDirectory() as temporary:
        tmp=Path(temporary);destination=tmp/'failed_run';weight=tmp/'weight';weight.write_bytes(b'test-only')
        poses=[np.eye(4) for _ in range(3)]
        for i,t in enumerate(poses):t[0,3]=i
        def data(args):
            (Path(args.output)/'source_frames.json').write_text(json.dumps(dict(source_frame_ids=[128,129,130],timestamps=None)))
            return np.array(poses),[np.zeros((5,3))]*3
        fake=FakeBackend([generation(),RuntimeError('second generation injected failure')])
        fake.ckpt_path=str(weight);fake.feature_extraction_on=False
        argv=['run_pipeline.py','--source','real','--real-apply-calib','--real-seq','06',
              '--loop-method','proximity','--multigen-k','2','--output',str(destination)]
        with patch.object(sys,'argv',argv),patch.object(run_pipeline,'get_sequence',side_effect=data),\
             patch.object(run_pipeline.odometry,'run_odometry',return_value=(poses,'kiss-icp')),\
             patch.object(run_pipeline.loop_closure,'find_candidates',return_value=[(0,2)]),\
             patch.object(backend_module,'RAPBackend',return_value=fake):
            try:run_pipeline.main()
            except RuntimeError as error:assert 'Incomplete candidate verification' in str(error)
            else:raise AssertionError('Pipeline declared success despite failed inference')
        assert (destination/'INCOMPLETE').exists() and not (destination/'summary.json').exists()
        counts=json.loads((destination/'verification_summary.json').read_text());assert counts['failed']==1
        events=[json.loads(l) for l in (destination/'verification_measurements.jsonl').read_text().splitlines()]
        assert len([e for e in events if e['event']=='generation'])==1
        checks.append('failed_pipeline_preserves_partial_records_and_INCOMPLETE')
        before=hashlib.sha256((destination/'verification_measurements.jsonl').read_bytes()).hexdigest()
        with patch.object(sys,'argv',argv):
            try:run_pipeline.main()
            except FileExistsError:checks.append('pipeline_refuses_existing_run_directory')
            else:raise AssertionError('Pipeline overwrote existing run')
        assert hashlib.sha256((destination/'verification_measurements.jsonl').read_bytes()).hexdigest()==before
    actual=Path('/mnt/e/githouse/RAP-main/.maintenance-archive/2026-09-11-m3-pipeline-01')
    assert not (actual/'INCOMPLETE').exists()
    events=[json.loads(l) for l in (actual/'verification_measurements.jsonl').read_text().splitlines()]
    measurements={e['measurement']['measurement_id']:e['measurement'] for e in events if e['event']=='generation'}
    accepted=json.loads((actual/'accepted_loops.json').read_text())
    assert len(accepted)==2 and len(measurements)==4
    for edge in accepted:
        m=measurements[edge['measurement_id']]
        np.testing.assert_array_equal(m['T_rel'],edge['T_rel'])
        assert m['overlap']==edge['overlap'] and m['mean_dist']==edge['mean_dist']
        assert m['source_frame_ids']==[edge['i']+128,edge['j']+128]
    checks.append('real_GPU_pipeline_measurement_to_edge_and_source_ID_links')
    summary=json.loads((actual/'summary.json').read_text())
    (out/'validation.json').write_text(json.dumps(dict(status='passed',checks=checks,real_pipeline_summary=summary),indent=2))
    print(json.dumps(dict(status='passed',checks=checks),indent=2))

if __name__=='__main__':main()
