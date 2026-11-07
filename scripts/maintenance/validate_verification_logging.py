"""CPU regression for formal candidate logging, including interrupted generations."""
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import numpy as np
ROOT=Path('/mnt/e/githouse/RAP-SLAM');sys.path.insert(0,str(ROOT))
from rap_slam.rap_backend import RAPBackend
from rap_slam.loop_closure import verify_candidates
from rap_slam.verification_log import VerificationLog, RecordingError

class FakeBackend:
    register_consistent=RAPBackend.register_consistent
    def __init__(self, outputs):self.outputs=iter(outputs)
    def register(self, a, b):
        value=next(self.outputs)
        if isinstance(value,Exception):raise value
        return value

def generation(overlap=.9,md=1.,x=0):
    t=np.eye(4);t[0,3]=x
    return t,dict(overlap_ratio=overlap,mean_dist=md,t_inference=.1,t_total=.2)

def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    poses=[np.eye(4),np.eye(4)];scans=[np.zeros((3,3))]*2;checks=[]
    def recorder(name):return VerificationLog(out/(name+'.jsonl'),name,'kitti','06',[128,130],poses)
    log=recorder('single')
    result=verify_candidates([(0,1)]*3,scans,poses,FakeBackend([generation(),generation(.1,9),RuntimeError('injected')]),gt_poses=poses,measurement_log=log)
    assert len(result)==1 and log.summary()==dict(started=0,accepted=1,rejected=1,failed=1)
    assert result[0]['measurement_id'] in log.measurements
    assert len(log.measurements)==2 and len(set(log.measurements))==2
    checks.append('accept_reject_failure_all_logged_and_duplicate_attempts_unique')
    log=recorder('multi')
    result=verify_candidates([(0,1)],scans,poses,FakeBackend([generation(.9,2),generation(.8,.5,50)]),multigen_k=2,gt_poses=poses,measurement_log=log)
    assert len(result)==1 and len(log.measurements)==2
    chosen=log.measurements[result[0]['measurement_id']]
    assert chosen['generation_id']==0 and chosen['mean_dist']==2 and chosen['labels']['label']=='safe'
    assert any(r['labels']['label']=='dangerous' for r in log.measurements.values())
    checks.append('multigen_selected_transform_metrics_label_and_ID_match')
    log=recorder('partial')
    result=verify_candidates([(0,1)],scans,poses,FakeBackend([generation(),RuntimeError('second generation failed')]),multigen_k=2,measurement_log=log)
    assert result==[] and len(log.measurements)==1 and log.summary()['failed']==1
    events=[json.loads(line) for line in log.path.read_text().splitlines()]
    assert events[-1]['completed_measurement_ids']==list(log.measurements)
    checks.append('partial_generation_retained_after_later_failure')
    log=recorder('invalid_rotation');t,d= generation();t[0,0]=1.01
    assert verify_candidates([(0,1)],scans,poses,FakeBackend([(t,d)]),measurement_log=log)==[]
    assert list(log.measurements.values())[0]['labels']['label']=='unlabeled' and log.summary()['failed']==1
    checks.append('invalid_transform_logged_and_not_accepted')
    log=recorder('io_failure')
    original=log._write
    def fail_generation(event):
        if event['event']=='generation':raise RecordingError('injected storage failure')
        original(event)
    with patch.object(log,'_write',side_effect=fail_generation):
        try:verify_candidates([(0,1)],scans,poses,FakeBackend([generation()]),measurement_log=log)
        except RecordingError:checks.append('evidence_write_failure_is_fatal')
        else:raise AssertionError('Storage failure swallowed')
    log=recorder('mismatch');attempt=log.start(0,1);t,d=generation();log.generation(attempt,0,t,d)
    try:log.decision(attempt,0,True,'heuristic',t,dict(d,mean_dist=7))
    except RecordingError:checks.append('selected_metrics_mismatch_is_fatal')
    else:raise AssertionError('Selection mismatch accepted')
    try:recorder('single')
    except FileExistsError:checks.append('existing_log_rejected')
    else:raise AssertionError('Existing log overwritten')
    # Existing callers keep their return contract when no recorder is requested.
    result=verify_candidates([(0,1)],scans,poses,FakeBackend([generation(),generation()]),multigen_k=2)
    assert len(result)==1
    checks.append('legacy_call_without_recorder_still_works')
    (out/'validation.json').write_text(json.dumps(dict(status='passed',checks=checks),indent=2))
    print(json.dumps(dict(status='passed',checks=checks),indent=2))

if __name__=='__main__':main()
