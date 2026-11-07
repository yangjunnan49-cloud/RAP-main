"""Fixed robust five-parameter Sampson refit, no reference input or scale."""
import baseline_lib as base


def cross(np, v):
    x, y, z = v
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def update(np, rotation, direction, step):
    omega = step[:3]
    angle = float(np.linalg.norm(omega))
    skew = cross(np, omega)
    if angle < 1e-12:
        exponential = np.eye(3) + skew + .5 * skew @ skew
    else:
        exponential = np.eye(3) + (np.sin(angle) / angle) * skew + ((1 - np.cos(angle)) / angle ** 2) * skew @ skew
    axis = np.eye(3)[int(np.argmin(np.abs(direction)))]
    first = np.cross(direction, axis)
    first /= np.linalg.norm(first)
    second = np.cross(direction, first)
    new_t = direction + step[3] * first + step[4] * second
    return exponential @ rotation, new_t / np.linalg.norm(new_t)


def residuals(np, rotation, direction, first, second, invk):
    f = invk.T @ cross(np, direction) @ rotation @ invk
    l2, l1 = first @ f.T, second @ f
    denominator = np.sqrt(np.sum(l2[:, :2] ** 2, axis=1) + np.sum(l1[:, :2] ** 2, axis=1))
    return np.sum(second * l2, axis=1) / np.maximum(denominator, 1e-12)


def _refine(cv2, np, first, second, k, method, key, initial, arrays):
    result = {**initial, 'initial_pose': initial.copy(), 'refinement': {'state': 'RAW_NO_EVIDENCE', 'trace': []}}
    if initial['status'] != 'POSE':
        return result, arrays
    arrays['raw_E'] = arrays['E'].copy()
    arrays['raw_cheirality_mask'] = arrays['cheirality_mask'].copy()
    rotation = np.asarray(initial['R_i_to_j'])
    direction = np.asarray(initial['unit_t_i_to_j'])
    keep = arrays['essential_mask'] != 0
    p1 = np.column_stack((first[keep], np.ones(int(keep.sum()))))
    p2 = np.column_stack((second[keep], np.ones(int(keep.sum()))))
    invk = np.linalg.inv(k)
    cfg = method['refinement']
    trace = result['refinement']['trace']
    state = 'ITERATION_CAP'
    for iteration in range(cfg['iterations']):
        residual = residuals(np, rotation, direction, p1, p2, invk)
        scale = max(cfg['scale_floor_px'], cfg['median_multiplier'] * float(np.median(np.abs(residual))))
        normalized = residual / (cfg['cutoff_multiplier'] * scale)
        weights = np.where(np.abs(normalized) < 1, (1 - normalized ** 2) ** 2, 0.)
        if int(np.count_nonzero(weights)) < 8:
            state = 'INSUFFICIENT_WEIGHTED_SUPPORT'
            break
        jacobian = np.empty((len(residual), 5), dtype=np.float64)
        for col in range(5):
            delta = np.zeros(5)
            delta[col] = cfg['derivative_step_rad']
            rp, tp = update(np, rotation, direction, delta)
            rm, tm = update(np, rotation, direction, -delta)
            jacobian[:, col] = (residuals(np, rp, tp, p1, p2, invk) - residuals(np, rm, tm, p1, p2, invk)) / (2 * cfg['derivative_step_rad'])
        root = np.sqrt(weights)
        step, _, rank, singular = np.linalg.lstsq(jacobian * root[:, None], -residual * root, rcond=None)
        if rank != 5 or not np.isfinite(step).all():
            state = 'RANK_OR_STEP_FAILURE'
            break
        magnitude = float(np.linalg.norm(step))
        if magnitude < cfg['step_stop_rad']:
            state = 'SMALL_STEP'
            break
        if magnitude > cfg['maximum_step_rad']:
            step *= cfg['maximum_step_rad'] / magnitude
        old_cost = float(np.dot(weights, residual ** 2))
        entry = {'iteration': iteration, 'scale_px': scale, 'positive_weights': int(np.count_nonzero(weights)),
                 'old_cost': old_cost, 'R_before': rotation.tolist(), 't_before': direction.tolist(),
                 'step': step.tolist(), 'line_search': [], 'accepted': False}
        for index in range(cfg['backtracks']):
            fraction = 2. ** (-index)
            candidate_r, candidate_t = update(np, rotation, direction, fraction * step)
            new_residual = residuals(np, candidate_r, candidate_t, p1, p2, invk)
            new_cost = float(np.dot(weights, new_residual ** 2))
            entry['line_search'].append({'fraction': fraction, 'cost': new_cost})
            if np.isfinite(new_cost) and new_cost < old_cost:
                rotation, direction = candidate_r, candidate_t
                entry.update(accepted=True, R_after=rotation.tolist(), t_after=direction.tolist(), new_cost=new_cost)
                break
        trace.append(entry)
        if not entry['accepted']:
            state = 'NO_DECREASE'
            break
    result['refinement']['state'] = state
    essential = cross(np, direction) @ rotation
    count, final_r, final_t, mask = cv2.recoverPose(essential, first, second, cameraMatrix=k,
            mask=arrays['essential_mask'].reshape(-1, 1).copy())
    final_t = final_t.reshape(3)
    mask = (np.asarray(mask).reshape(-1) != 0).astype(np.uint8)
    assert int(mask.sum()) == int(count) and np.all(mask <= arrays['essential_mask'])
    arrays.update(E=essential, cheirality_mask=mask)
    result.update(cheirality_inliers=int(count), selected_essential_index=0, candidate_counts=[int(count)])
    norm = float(np.linalg.norm(final_t))
    tol = method['rotation_validity_tolerance']
    valid = np.isfinite(final_r).all() and np.isfinite(final_t).all() and norm > 0 and np.linalg.norm(final_r.T @ final_r - np.eye(3), ord=np.inf) < tol and abs(np.linalg.det(final_r) - 1) < tol
    if not valid or count < method['minimum_matches']:
        result.update(status='NO_EVIDENCE_REFINED_POSE', R_i_to_j=None, unit_t_i_to_j=None)
    else:
        result.update(status='POSE', R_i_to_j=final_r.tolist(), unit_t_i_to_j=(final_t / norm).tolist())
    return result, arrays


def estimate(cv2, np, first, second, k, method, key):
    initial, arrays = base.estimate(cv2, np, first, second, k, method, key)
    try:
        return _refine(cv2, np, first, second, k, method, key, initial, arrays)
    except (cv2.error, np.linalg.LinAlgError, FloatingPointError) as exc:
        return {**initial, 'initial_pose': initial.copy(), 'status': 'NO_EVIDENCE_REFINEMENT_ERROR',
                'R_i_to_j': None, 'unit_t_i_to_j': None,
                'refinement': {'state': 'NUMERICAL_ERROR', 'error': str(exc)[:800], 'trace': []}}, arrays
