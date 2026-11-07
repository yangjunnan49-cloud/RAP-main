"""Independent audit for the frozen F2 structured-motion development screen.

AMENDED COPY (F2-AMENDMENT-01): per-part center convention fix in the
independent decode crosscheck; see docs/maintenance/2026-09-27/
f2-structured-dev-01/AMENDMENT_01.md. The original frozen validator
validate_f2_structured.py is unchanged and its freeze-recorded hash remains
valid; this copy's SHA256 is recorded in validation.json as validator_sha256.

synthetic: pre-freeze geometry checks (nontrivial poses, gauge, permutation,
single-part reduction). validate: post-execution recomputation that trusts
nothing the runner produced; GT is loaded only after artifact hash
verification. Removes INCOMPLETE markers only when every check passes.
REPORT.md and validation.json are post-manifest records and are excluded from
the manifest coverage check.
"""
import hashlib, json, sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
MAIN = Path('/mnt/e/githouse/RAP-main')
ROOT = MAIN.parent / 'RAP-SLAM'
BASE = MAIN / 'docs/maintenance/2026-09-27/f2-structured-dev-01'
D00 = MAIN / 'docs/maintenance/2026-09-14/hl-v2/data-expansion-01'
D08 = MAIN / 'docs/maintenance/2026-09-14/support-control-01/data'
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts'), str(MAIN)]
CAPS = [2000, 1000, 1000, 2000, 1000, 1000]
ARMS = ['N', 'F', 'S', 'P', 'A']
POST_MANIFEST = {'INCOMPLETE', 'artifact_hashes.json', 'validation.json', 'REPORT.md',
                 'AMENDMENT_01.md'}


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def save(p, x):
    with Path(p).open('x') as f:
        json.dump(x, f, indent=2, allow_nan=False)


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for v in iter(lambda: f.read(2**20), b''):
            h.update(v)
    return h.hexdigest()


def fit(x, y):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    u, _, v = np.linalg.svd((x - x.mean(0)).T @ (y - y.mean(0)))
    d = np.eye(3)
    d[2, 2] = np.linalg.det(v.T @ u.T)
    r = v.T @ d @ u.T
    return r, y.mean(0) - r @ x.mean(0)


def apply(T, p):
    return p @ T[:3, :3].T + T[:3, 3]


def pose(r, t):
    T = np.eye(4)
    T[:3, :3] = r
    T[:3, 3] = t
    return T


def decode_part_poses(cond_parts, raw_parts, centers, scale):
    """float64 reimplementation of structured_motion.decode_parts."""
    out = []
    for p, y, c in zip(cond_parts, raw_parts, centers):
        r, t = fit(p, y)
        out.append(pose(r, scale * t - r @ c))
    return np.asarray(out)


def rigidity_numpy(cond_parts, raw_steps_parts, scale):
    """Official formula: sqrt(mean over all points of ||cond@R.T+t - pred||^2) * scale."""
    vals = []
    for raw_parts in raw_steps_parts:
        res = []
        for p, y in zip(cond_parts, raw_parts):
            r, t = fit(p, y)
            res.append(np.sum((p @ r.T + t - y) ** 2, axis=1))
        vals.append(float(np.sqrt(np.mean(np.concatenate(res))) * scale))
    return vals


def corrected(entry):
    raw = np.fromfile(entry['path'], np.float32).reshape(-1, 4)[:, :3]
    raw = raw[np.linalg.norm(raw, axis=1) >= 1.5]
    from rap_slam.real_dataset import kitti_vertical_correction
    return np.ascontiguousarray(kitti_vertical_correction(raw), dtype=np.float32)


def synthetic():
    import torch
    from rap_slam.rap_backend import RAPBackend
    from rap_slam.structured_motion import group_coordinates, project_groups, decode_groups
    from rap_slam.rap_precision import ieee_matmul
    rng = np.random.default_rng(260927)
    errors, gauge_errors, perm_errors, single_errors = [], [], [], []
    for trial in range(20):
        points = [rng.normal(size=(300 if k in [0, 3] else 200, 3)) * 5 + rng.normal(size=3) * 4
                  for k in range(6)]
        L = [np.eye(4) if k in [0, 3] else pose(Rotation.random(random_state=rng).as_matrix(),
                                                rng.normal(size=3)) for k in range(6)]
        _, s, c, n, _ = RAPBackend._normalize_parts(points)
        c = np.asarray(c)
        q = group_coordinates(points, L, c, s, torch.device('cpu'))
        G = [pose(Rotation.random(random_state=rng).as_matrix(), rng.normal(size=3)) for _ in range(2)]
        y = np.concatenate([apply(G[0 if k < 3 else 1], apply(L[k], p)) / s for k, p in enumerate(points)])
        split = int(sum(n[:3]))
        with ieee_matmul():
            _, rt = project_groups(torch.tensor(y, dtype=torch.float32), q, split)
        recovered = decode_groups(rt, c, s)
        delta = float(np.max(np.abs(recovered - np.asarray(G))))
        assert delta < 1e-4
        errors.append(delta)
        gauge = pose(Rotation.random(random_state=rng).as_matrix(), rng.normal(size=3))
        z = np.concatenate([apply(gauge, part) for part in np.split(y, [split])])
        with ieee_matmul():
            _, rt2 = project_groups(torch.tensor(z, dtype=torch.float32), q, split)
        rec2 = decode_groups(rt2, c, s)
        gauge_errors.append(float(np.max(np.abs(np.linalg.inv(rec2[0]) @ rec2[1]
                                                - np.linalg.inv(recovered[0]) @ recovered[1]))))
        assert gauge_errors[-1] < 1e-4
        perm = [0, 2, 1, 3, 5, 4]  # swap the two supports inside each visit
        points_p = [points[k] for k in perm]
        L_p = [L[k] for k in perm]
        q_p = group_coordinates(points_p, L_p, c, s, torch.device('cpu'))
        y_p = np.concatenate([apply(G[0 if k < 3 else 1], apply(L_p[k], p)) / s for k, p in enumerate(points_p)])
        with ieee_matmul():
            _, rtp = project_groups(torch.tensor(y_p, dtype=torch.float32), q_p, split)
        perm_errors.append(float(np.max(np.abs(decode_groups(rtp, c, s) - recovered))))
        assert perm_errors[-1] < 1e-5
        # Single-part reduction: support parts identical to their anchor (L=I)
        # reduce the group fit to the anchor fit; per-part counts preserved.
        single = [points[0], points[0][:200], points[0][:200],
                  points[3], points[3][:200], points[3][:200]]
        L_s = [np.eye(4) for _ in range(6)]
        q_s = group_coordinates(single, L_s, c, s, torch.device('cpu'))
        y_s = np.concatenate([apply(G[0 if k < 3 else 1], p) / s for k, p in enumerate(single)])
        with ieee_matmul():
            _, rts = project_groups(torch.tensor(y_s, dtype=torch.float32), q_s, split)
        single_errors.append(float(np.max(np.abs(decode_groups(rts, c, s) - np.asarray(G)))))
        assert single_errors[-1] < 1e-4
    save(BASE / 'synthetic_validation.json', dict(
        passed=True, trials=20, max_pose_delta=max(errors), max_gauge_delta=max(gauge_errors),
        max_permutation_delta=max(perm_errors), max_single_part_delta=max(single_errors),
        scope='Group projection equation checks only; no model, cohort or efficacy content'))
    print('F2 synthetic passed', max(errors), flush=True)


def validate():
    f = read(BASE / 'freeze.json')
    for group in ['sources', 'raw', 'parents']:
        for p, h in f[group].items():
            assert sha(p) == h, p
    for s, h in f['inputs'].items():
        assert sha(BASE / f'inputs_{s}.json') == h, s
    manifest = read(BASE / 'artifact_hashes.json')
    for p, h in manifest.items():
        assert sha(BASE / p) == h, p
    present = {str(p.relative_to(BASE)) for p in BASE.rglob('*')
               if p.is_file() and p.name not in POST_MANIFEST}
    assert present == set(manifest), ('manifest coverage', present ^ set(manifest))
    from rap_slam.rap_backend import RAPBackend
    from rap_slam.measurement import transform_label
    from support_control import aggregate, STRATA
    g = RAPBackend.__new__(RAPBackend)
    g.voxel_size = .4; g.remove_outliers = True; g.max_points_per_scan = 4000; g.seed = 42
    g.feature_extractor = None
    max_project = max_pose = max_constraint = max_rigidity = max_gate = max_motion = 0.0
    n_generation = 0
    for seq, dd in [('00', D00), ('08', D08)]:
        out = BASE / seq
        role = 'discovery' if seq == '00' else 'confirmation'
        bank_rows = read(dd / f'{role}_inputs.json')
        inputs = read(BASE / f'inputs_{seq}.json')
        odom = np.load(dd / seq / 'odom.npy')
        assert len(inputs) == len(bank_rows) == 100
        for row, br in zip(inputs, bank_rows):
            assert (row['source_i'], row['source_j']) == (br['source_i'], br['source_j'])
            assert row['seeds'] == [int(hashlib.sha256(
                f"F2|structured-motion|kitti|{seq}|{row['source_i']}|{row['source_j']}|{k}".encode()
            ).hexdigest()[:8], 16) % (2**31) for k in range(4)]
            for side in ['i', 'j']:
                anchor = br['source_' + side]
                for sp in br['support_' + side]:
                    delta = float(np.max(np.abs(np.linalg.inv(odom[anchor]) @ odom[sp['source_id']]
                                                - np.asarray(sp['local_pose']))))
                    max_motion = max(max_motion, delta)
                    assert delta < 1e-8
        records = read(out / 'records.json')
        gates = read(out / 'gates.json')
        ridx = {(r['pair'], r['arm'], r['generation']): r for r in records}
        for row in inputs:
            dest = out / row['key']
            data = np.load(dest / 'inputs.npz')
            counts = data['counts']
            assert counts.tolist() == CAPS
            scale = float(data['scale'])
            centers = data['centers']
            motions = data['motions']
            # Independent points reproduction: filter -> 0.205 correction -> seed42 preprocessing.
            saved = np.split(data['points'], np.cumsum(counts)[:-1])
            for entry, cap, sv in zip(row['scans'], CAPS, saved):
                pts, _ = g.preprocess(corrected(entry), max_points=cap)
                assert pts.shape == (cap, 3)
                assert np.array_equal(pts, sv), ('points reproduction', row['key'], cap)
            assert np.max(np.abs(data['cond'] * scale + np.repeat(centers, counts, axis=0)
                                 - data['points'])) < 1e-4
            q = np.concatenate([(apply(motions[k], p) - centers[0 if k < 3 else 3]) / scale
                                for k, p in enumerate(saved)])
            assert np.max(np.abs(q - data['group_source'])) < 1e-6
            assert data['noise'].shape == (4, 8000, 3)
            anchors = [g.preprocess(corrected(row['scans'][sidx]))[0] for sidx in [0, 3]]
            cond_parts = np.split(data['cond'].astype(np.float64), np.cumsum(counts)[:-1])
            part_centers = [centers[k] for k in range(6)]
            for arm in ARMS:
                for k in range(4):
                    rec = ridx[(row['key'], arm, k)]
                    if not rec['valid']:
                        assert gates[row['key']][arm][str(k)]['accepted'] is False
                        continue
                    n_generation += 1
                    a = np.load(dest / f'{arm}{k}.npz')
                    assert a['end_point_trajectory'].shape[0] == 5
                    if arm in ('N', 'F', 'S'):
                        cps, cts, sc, nn = cond_parts, part_centers, scale, counts
                    else:
                        if arm == 'P':
                            ps_ = [np.concatenate([apply(motions[m], saved[m])
                                                   for m in range(3)]).astype(np.float32),
                                   np.concatenate([apply(motions[m], saved[m])
                                                   for m in range(3, 6)]).astype(np.float32)]
                        else:
                            ps_ = [np.asarray(saved[0], np.float32), np.asarray(saved[3], np.float32)]
                        cond2, sc, cc, nn, _ = RAPBackend._normalize_parts(ps_)
                        cps = np.split(cond2.astype(np.float64), np.cumsum(nn)[:-1])
                        cts = [np.asarray(cc)[0], np.asarray(cc)[1]]
                    if arm == 'F':
                        assert np.array_equal(a['end_point_trajectory'],
                                              np.load(dest / f'N{k}.npz')['end_point_trajectory'])
                    raw = a['end_point_trajectory'][-1].astype(np.float64)
                    lens = [len(p) for p in cps]
                    raw_parts = np.split(raw, np.cumsum(lens)[:-1])
                    poses = decode_part_poses(cps, raw_parts, cts, sc)
                    d = float(np.max(np.abs(poses - a['raw_poses'])))
                    max_pose = max(max_pose, d)
                    assert d < 1e-3, (row['key'], arm, k, d)
                    if arm in ('F', 'S'):
                        projected = []
                        gg2 = []
                        for gi, sl in enumerate([slice(0, 4000), slice(4000, None)]):
                            r_, t_ = fit(q[sl], raw[sl])
                            projected.append(q[sl] @ r_.T + t_)
                            gg2.append(pose(r_, sc * t_ - r_ @ centers[0 if gi == 0 else 3]))
                        pp = np.concatenate(projected)
                        if arm == 'S':
                            for step in range(5):
                                raw_s = a['end_point_trajectory'][step].astype(np.float64)
                                prs = []
                                for sl in [slice(0, 4000), slice(4000, None)]:
                                    r_, t_ = fit(q[sl], raw_s[sl])
                                    prs.append(q[sl] @ r_.T + t_)
                                pcs = np.concatenate(prs)
                                dp = float(np.max(np.abs(pcs - a['projected_clean_trajectory'][step])))
                                max_project = max(max_project, dp)
                                assert dp < 1e-4, (row['key'], k, step, dp)
                                time_next = 1 - (step + 1) / 5
                                ds = float(np.max(np.abs(pcs * (1 - time_next)
                                                         + data['noise'][k] * time_next
                                                         - a['trajectory'][step])))
                                assert ds < 1e-4, (row['key'], k, step, 'state', ds)
                        assert np.max(np.abs(pp - a['decoded_final'])) < 1e-4
                        d = float(np.max(np.abs(np.asarray(gg2) - a['group_poses'])))
                        max_pose = max(max_pose, d)
                        assert d < 1e-3
                        fitted = decode_part_poses(cond_parts, np.split(pp, np.cumsum(counts)[:-1]),
                                                   part_centers, scale)
                        residual = max(float(np.max(np.abs(np.linalg.inv(fitted[0 if m < 3 else 3])
                                                           @ fitted[m] - motions[m]))) for m in range(6))
                        max_constraint = max(max_constraint, residual)
                        assert residual < 1e-4
                        assert abs(rec['constraint_matrix_residual'] - residual) < 1e-3
                        T = np.linalg.inv(gg2[0]) @ gg2[1]
                    else:
                        T = np.linalg.inv(poses[0]) @ poses[3 if arm == 'N' else 1]
                    assert np.max(np.abs(T - a['T'])) < 1e-3
                    assert np.max(np.abs(T - np.asarray(rec['T']))) < 1e-3
                    rig = rigidity_numpy(cps, [np.split(s_, np.cumsum(lens)[:-1])
                                               for s_ in a['end_point_trajectory'].astype(np.float64)], sc)
                    dr = float(np.max(np.abs(np.asarray(rig) - a['rigidity_steps'])))
                    max_rigidity = max(max_rigidity, dr)
                    assert dr < 1e-3, (row['key'], arm, k, dr)
                    assert abs(float(np.mean(rig)) - rec['rigidity_rmse_m']) < 1e-3
                    ov, md = g._alignment_metrics(*anchors, np.asarray(rec['T']), thresh=1.)
                    saved_gate = gates[row['key']][arm][str(k)]
                    dg = max(abs(ov - saved_gate['overlap_ratio']), abs(md - saved_gate['mean_dist']))
                    max_gate = max(max_gate, dg)
                    assert dg < 1e-6
                    assert bool(ov >= .7 and md <= 2.5) == saved_gate['accepted']
        # Sensitivity records: perturbed motions and transform deltas recomputed.
        sens = read(out / 'sensitivity.json')
        for signame, sign in [('Sminus', -1), ('Splus', 1)]:
            aa = np.deg2rad(sign)
            D = np.eye(4)
            D[:3, :3] = [[np.cos(aa), -np.sin(aa), 0], [np.sin(aa), np.cos(aa), 0], [0, 0, 1]]
            D[0, 3] = sign * .1
            for pair in sens['pairs']:
                data = np.load(out / pair / 'inputs.npz')
                pert = np.load(out / pair / f"motions-{'minus' if sign < 0 else 'plus'}.npy")
                expected = data['motions'].copy()
                for m in [1, 2, 4, 5]:
                    expected[m] = D @ data['motions'][m]
                assert np.max(np.abs(pert - expected)) < 1e-12
                for entry in sens['deltas'][signame]:
                    if entry['pair'] != pair:
                        continue
                    base = ridx[(pair, 'S', entry['generation'])]
                    pr = ridx[(pair, signame, entry['generation'])]
                    lab = transform_label(np.asarray(pr['T']), np.asarray(base['T']))
                    assert abs(lab['gt_translation_error_m'] - entry['translation_m']) < 1e-9
                    assert abs(lab['gt_rotation_error_deg'] - entry['rotation_deg']) < 1e-9
    assert max_motion == f['max_local_motion_recheck_delta'], (max_motion, f['max_local_motion_recheck_delta'])
    execution = {s: read(BASE / s / 'execution.json') for s in ['00', '08']}
    for s, e in execution.items():
        assert e['cumulative_wall_s'] <= 4 * 3600 and e['peak_allocated'] <= 12 * 2**30
        assert e['no_hooks_installed'] and e['restoration_on_exception']
        assert e['gt_access'] == 'evaluator_only_after_generation_hash_freeze'
    assert execution['00']['native_max_delta'] <= 1e-6 and execution['00']['replay_max_delta'] <= 1e-6
    assert read(BASE / '00/preflight_validation.json')['passed']
    total_bytes = sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
    assert total_bytes < 20 * 2**30
    # Only now load evaluator truth, after all generation artifacts verified.
    decision = read(BASE / 'decision.json')
    seq_signals = {}
    for seq, dd in [('00', D00), ('08', D08)]:
        role = 'discovery' if seq == '00' else 'confirmation'
        labels = read(dd / f'{role}_evaluator.json')
        gt = np.load(dd / seq / 'evaluator_gt.npy')
        records = read(BASE / seq / 'records.json')
        gates = read(BASE / seq / 'gates.json')
        joined_saved = read(BASE / seq / 'evaluator_only_decisions.json')
        bypair = {}
        for rec in records:
            if rec['arm'] in ARMS:
                bypair.setdefault(rec['pair'], {}).setdefault(rec['arm'], {})[rec['generation']] = rec
        joined = []
        for row in labels:
            i, j = row['source_i'], row['source_j']
            key = f'{seq}_{i}_{j}'
            Tgt = np.linalg.inv(gt[i]) @ gt[j]
            methods = {}
            for arm in ARMS:
                gens = bypair[key][arm]
                labs = {}
                for k, rec in gens.items():
                    if rec['valid']:
                        lab = transform_label(np.asarray(rec['T']), Tgt)
                        t, an = lab['gt_translation_error_m'], lab['gt_rotation_error_deg']
                        labs[k] = dict(RTE_m=t, RRE_deg=an, error=max(t, an / 5),
                                       clipped_error=min(5, max(t, an / 5)),
                                       strict=bool(t <= 1 and an <= 5), legacy_safe=lab['label'] == 'safe')
                good = [k for k, rec in gens.items() if rec['valid']]
                sel = min(good, key=lambda k: (gens[k]['rigidity_rmse_m'], k)) if good else None
                lab = labs[sel] if sel is not None else dict(RTE_m=None, RRE_deg=None, error=5.,
                                                             clipped_error=5., strict=False, legacy_safe=False)
                accepted = gates[key][arm][str(sel)]['accepted'] if sel is not None else False
                methods[arm] = dict(generation=sel, accepted=accepted,
                                    incorrect_accepted=bool(accepted and not lab['strict']),
                                    failed=sel is None, **lab)
                osel = min(labs, key=lambda k: (labs[k]['error'], k)) if labs else None
                olab = labs[osel] if osel is not None else dict(RTE_m=None, RRE_deg=None, error=5.,
                                                                clipped_error=5., strict=False, legacy_safe=False)
                oacc = gates[key][arm][str(osel)]['accepted'] if osel is not None else False
                methods[arm + '-OR4'] = dict(generation=osel, accepted=oacc,
                                             incorrect_accepted=bool(oacc and not olab['strict']),
                                             failed=osel is None, **olab)
            joined.append(dict(sequence=seq, source_i=i, source_j=j, stratum=row['stratum'], methods=methods))
        assert json.dumps(joined, sort_keys=True, allow_nan=False) == \
            json.dumps(joined_saved, sort_keys=True, allow_nan=False), f'{seq} evaluator rows differ'
        names = ARMS + [a + '-OR4' for a in ARMS]
        overall = {m: aggregate(joined, m) for m in names}
        strata = {s: {m: aggregate([r for r in joined if r['stratum'] == s], m) for m in names} for s in STRATA}
        saved_m = read(BASE / seq / 'metrics.json')
        assert json.dumps(overall, sort_keys=True, allow_nan=False) == \
            json.dumps(saved_m['overall'], sort_keys=True, allow_nan=False)
        assert json.dumps(strata, sort_keys=True, allow_nan=False) == \
            json.dumps(saved_m['by_stratum'], sort_keys=True, allow_nan=False)
        conditions = {}
        for tag, other in [('C1_vs_N', 'N'), ('C2_vs_F', 'F'), ('C3_vs_P', 'P')]:
            conditions[tag + '_recall_3pp'] = overall['S']['selection_recall'] - overall[other]['selection_recall'] >= .03
            conditions[tag + '_error_5pct'] = overall['S']['mean_clipped_positive_error'] <= .95 * overall[other]['mean_clipped_positive_error']
        conditions['C4_no_more_incorrect_than_N'] = overall['S']['incorrect_accepted'] <= overall['N']['incorrect_accepted']
        conditions['C4_ordinary_loss_2pp'] = strata['ordinary']['N']['selection_recall'] - strata['ordinary']['S']['selection_recall'] <= .02
        assert conditions == saved_m['conditions']
        seq_signals[seq] = all(conditions.values())
        assert seq_signals[seq] == saved_m['sequence_signal']
    e00, e08 = execution['00'], execution['08']
    c5 = bool(e00['cumulative_wall_s'] <= 4 * 3600 and e08['cumulative_wall_s'] <= 4 * 3600
              and e00['peak_allocated'] <= 12 * 2**30 and e08['peak_allocated'] <= 12 * 2**30
              and e00['native_max_delta'] <= 1e-6 and e00['replay_max_delta'] <= 1e-6)
    expected = 'DEVELOPMENT_MECHANISM_SIGNAL' if (seq_signals['00'] and seq_signals['08'] and c5) \
        else 'NO_DEVELOPMENT_MECHANISM_SIGNAL'
    assert decision['decision'] == expected
    assert decision['sequence_signals'] == seq_signals
    result = dict(passed=True, decision=expected, pairs=200, valid_generations=n_generation,
                  max_independent_projected_delta=max_project, max_independent_pose_delta=max_pose,
                  max_constraint_delta=max_constraint, max_rigidity_delta=max_rigidity,
                  max_gate_delta=max_gate, max_local_motion_recheck=max_motion,
                  artifact_bytes=total_bytes, sequence_signals=seq_signals, C5_engineering=c5,
                  evaluator_rows_exact=True, decision_arithmetic_independent=True,
                  validator_sha256=sha(Path(__file__)), amendment='F2-AMENDMENT-01',
                  scope='Independent recomputation of geometry, selection, gates, labels, aggregates and '
                        'decision; observed development cohorts; no efficacy claim beyond the frozen gates')
    save(BASE / 'validation.json', result)
    for s in ['00', '08']:
        (BASE / s / 'INCOMPLETE').unlink()
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    {'synthetic': synthetic, 'validate': validate}[sys.argv[1]]()
