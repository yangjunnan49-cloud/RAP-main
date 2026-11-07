"""Independent O3 comparator persisted-output checks."""
import json
from pathlib import Path
import sys
import numpy as np
sys.path[:0]=['/mnt/e/githouse/RAP-SLAM','/mnt/e/githouse/RAP-SLAM/scripts']
from rap_slam.measurement import rotation_validity, transform_label
import eval_paper_metrics as metrics


def validate(out):
    total=accepted=failed=0
    for name in ['poss','kitti06','kitti05','kitti00']:
        src=out.parent/'optimization-o3-01'/name/'12'
        parent=out.parent.parent/'2026-09-11'/('full-'+name+'-01')/'pipeline'
        pairs=json.loads((src/'candidates.json').read_text())['merged']
        ids=json.loads((parent/'source_frames.json').read_text())['source_frame_ids']
        odom=metrics.load_kitti_format(str(parent/'odom_poses.txt'))
        gt=metrics.gt_from_summary(str(parent))
        saved_metrics=json.loads((out/name/'metrics.json').read_text())
        for arm in ['identity','odometry']:
            records=[json.loads(s) for s in (out/name/(arm+'_attempts.jsonl')).read_text().splitlines()]
            edges=json.loads((out/name/(arm+'_edges.json')).read_text())
            assert [[r['i'],r['j']] for r in records]==pairs
            selected={r['measurement_id']:r for r in records if r['accepted']}
            assert len(edges)==len(selected)
            assert {e['measurement_id'] for e in edges}==selected.keys()
            for r in records:
                total+=1
                i,j=r['i'],r['j']
                initial=np.eye(4) if arm=='identity' else np.linalg.inv(odom[i])@odom[j]
                np.testing.assert_array_equal(r['initial'],initial)
                if r['status']=='failed':
                    failed+=1
                    continue
                assert r['source_frame_ids']==[ids[i],ids[j]]
                label=transform_label(r['T_rel'],np.linalg.inv(gt[i])@gt[j])
                assert label['label']==r['labels']['label'] and label['validity']['valid']
                assert r['accepted']==(rotation_validity(r['T_rel'])['valid'] and r['overlap']>=.7 and r['mean_dist']<=2.5)
            for e in edges:
                r=selected[e['measurement_id']]
                assert [e['i'],e['j']]==[r['i'],r['j']]
                np.testing.assert_array_equal(e['T_rel'],r['T_rel'])
                accepted+=1
            poses=metrics.load_kitti_format(str(out/name/(arm+'_poses.txt')))
            assert len(poses)==len(ids) and np.isfinite(poses).all()
            check=metrics.evaluate_pair(gt,poses,ids)
            for key in ['ape_unaligned_rmse','ape_aligned_rmse','kitti_ter_pct']:
                np.testing.assert_allclose(check[key],saved_metrics['arms'][arm]['metrics'][key],atol=1e-9,rtol=0)
    assert total==80 and failed==0
    result=dict(attempts=total,accepted_edges=accepted,failed=failed,candidate_order_exact=True,
        initial_transforms_exact=True,source_ids_exact=True,gate_and_labels_recomputed=True,
        edge_transforms_exact=True,saved_trajectory_metrics_recomputed=True)
    (out/'association_validation.json').write_text(json.dumps(result,indent=2))
    print(result)
