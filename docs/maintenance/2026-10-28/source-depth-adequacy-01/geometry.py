"""Fixed source-side projected-point association, no pose/reference API."""


def project(np, xyz, tr, k, width, height):
    index = np.arange(len(xyz), dtype=np.int64)
    camera = xyz @ tr[:3, :3].T + tr[:3, 3]
    good = np.isfinite(camera).all(axis=1) & (camera[:, 2] > 0)
    camera, index = camera[good], index[good]
    image = camera @ k.T
    uv = image[:, :2] / image[:, 2:3]
    keep = (uv[:, 0] >= 0) & (uv[:, 0] <= width-1) & (uv[:, 1] >= 0) & (uv[:, 1] <= height-1)
    uv, camera, index = uv[keep], camera[keep], index[keep]
    bins = np.floor(uv+.5).astype(np.int64)
    linear = bins[:, 1]*width + bins[:, 0]
    order = np.lexsort((index, camera[:, 2], linear))
    sorted_bins = linear[order]
    unique = np.r_[True, sorted_bins[1:] != sorted_bins[:-1]] if len(order) else np.empty(0, dtype=bool)
    chosen = order[unique]
    uv, camera, index, bins = uv[chosen], camera[chosen], index[chosen], bins[chosen]
    grid = {(int(x), int(y)): pos for pos, (x, y) in enumerate(bins)}
    return uv, camera, index, grid


def associate(np, queries, uv, camera, index, grid, radius=2.):
    assigned = np.full(len(queries), -1, dtype=np.int64)
    distance = np.full(len(queries), np.inf)
    for n, (x, y) in enumerate(queries):
        bx, by = int(np.floor(x+.5)), int(np.floor(y+.5))
        candidates = [grid[(i, j)] for i in range(bx-3, bx+4) for j in range(by-3, by+4) if (i, j) in grid]
        if not candidates:
            continue
        c = np.asarray(candidates, dtype=np.int64)
        squared = np.sum((uv[c]-[x, y])**2, axis=1)
        inside = squared <= radius**2
        c, squared = c[inside], squared[inside]
        if not len(c):
            continue
        best = np.lexsort((index[c], camera[c, 2], squared))[0]
        assigned[n], distance[n] = c[best], squared[best]
    deduplicated = []
    seen = set()
    for n in sorted(range(len(queries)), key=lambda i: (float(distance[i]), i)):
        pos = int(assigned[n])
        if pos >= 0 and int(index[pos]) not in seen:
            seen.add(int(index[pos]))
            deduplicated.append(n)
    return assigned, distance, np.asarray(sorted(deduplicated), dtype=np.int64)


def dense(np, query, uv, camera, index, radius=2.):
    squared = np.sum((uv-query)**2, axis=1)
    c = np.flatnonzero(squared <= radius**2)
    if not len(c):
        return -1
    return int(c[np.lexsort((index[c], camera[c, 2], squared[c]))[0]])
