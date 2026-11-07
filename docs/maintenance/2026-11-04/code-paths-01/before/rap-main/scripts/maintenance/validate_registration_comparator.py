"""Independent saved-attempt/edge association and policy checks."""
import json
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,'/mnt/e/githouse/RAP-SLAM')
from rap_slam.measurement import rotation_validity

base=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-11')
out=base/'comparator-01'
assert not (out/'INCOMPLETE').exists()
total=accepted=failed=0
for name in ['poss_off','kitti06_off','kitti05','kitti00']:
    pairs=json.loads((base/'m3-logging/core-replay-01'/name/'candidates.json').read_text())['merged']
    for arm in ['identity','odometry']:
        records=[json.loads(line) for line in (out/name/(arm+'_attempts.jsonl')).read_text().splitlines()]
        edges=json.loads((out/name/(arm+'_edges.json')).read_text())
        assert [[r['i'],r['j']] for r in records]==pairs
        selected={r['measurement_id']:r for r in records if r['accepted']}
        assert len(edges)==len(selected)
        for r in records:
            total+=1
            if r['status']=='failed':
                failed+=1
                continue
            assert r['labels']['validity']['valid']
            assert r['accepted']==(rotation_validity(r['T_rel'])['valid'] and r['overlap']>=.7 and r['mean_dist']<=2.5)
        for e in edges:
            r=selected[e['measurement_id']]
            assert [e['i'],e['j']]==[r['i'],r['j']]
            np.testing.assert_array_equal(e['T_rel'],r['T_rel'])
            accepted+=1
assert total==80 and failed==0
(out/'association_validation.json').write_text(json.dumps(dict(attempts=total,accepted_edges=accepted,failed=failed,candidate_order_exact=True,gate_recomputed=True,edge_transforms_exact=True),indent=2))
print(total,accepted,failed)
