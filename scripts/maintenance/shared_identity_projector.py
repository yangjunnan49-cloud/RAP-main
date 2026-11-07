"""SID0 isolated NumPy projector. No model, dataset or production imports."""
from __future__ import annotations

import numpy as np

FIT_TOL = 1e-12
STOP_TOL = 1e-12
MAX_SWEEPS = 64


class UndefinedFit(ValueError):
    pass


def apply(T, p):
    return p @ T[:3, :3].T + T[:3, 3]


def inverse(T):
    out = np.eye(4)
    out[:3, :3] = T[:3, :3].T
    out[:3, 3] = -out[:3, :3] @ T[:3, 3]
    return out


def fit(p, y, weights=None):
    """Unique proper Kabsch source-to-target fit, including planar inputs."""
    p, y = np.asarray(p, dtype=np.float64), np.asarray(y, dtype=np.float64)
    if p.shape != y.shape or p.ndim != 2 or p.shape[1] != 3 or len(p) < 3:
        raise UndefinedFit("invalid shape")
    w = np.ones(len(p)) if weights is None else np.asarray(weights, dtype=np.float64)
    if w.shape != (len(p),) or np.any(w <= 0) or not np.isfinite(w).all():
        raise UndefinedFit("invalid weights")
    if not np.isfinite(p).all() or not np.isfinite(y).all():
        raise UndefinedFit("nonfinite points")
    w = w / w.sum()
    pc, yc = (p * w[:, None]).sum(0), (y * w[:, None]).sum(0)
    U, sigma, Vt = np.linalg.svd((p - pc).T @ ((y - yc) * w[:, None]))
    eps = FIT_TOL * max(1., float(sigma[0]))
    reflected = np.linalg.det(Vt.T @ U.T) < 0
    if sigma[1] <= eps or (reflected and sigma[1] - sigma[2] <= eps):
        raise UndefinedFit("nonunique proper rigid optimum")
    sign = np.diag([1., 1., -1. if reflected else 1.])
    T = np.eye(4)
    T[:3, :3] = Vt.T @ sign @ U.T
    T[:3, 3] = yc - T[:3, :3] @ pc
    return T


def unpack(data):
    pstart = np.r_[0, np.cumsum(data['point_counts'])]
    factors = []
    for f, (i, w) in enumerate(zip(data['factor_scans'], data['factor_windows'])):
        sl = slice(int(data['factor_offsets'][f]), int(data['factor_offsets'][f+1]))
        rows = data['factor_rows'][sl]
        n = int(data['point_counts'][i])
        if len(rows) != n or not np.array_equal(np.sort(rows), np.arange(n)):
            raise UndefinedFit("inexact canonical row identity")
        p = data['points'][pstart[i]:pstart[i+1]][rows]
        factors.append(dict(i=int(i), w=int(w), p=p, y=data['raw'][sl]*data['scales'][w],
                            rows=rows, sl=sl))
    return factors


def project(data):
    factors = unpack(data)
    ns, nw = len(data['point_counts']), len(data['scales'])
    byscan = [[f for f in factors if f['i'] == i] for i in range(ns)]
    bywindow = [[f for f in factors if f['w'] == w] for w in range(nw)]
    if any(not x for x in byscan+bywindow):
        raise UndefinedFit("unobserved node")
    if len({(f['w'], f['i']) for f in factors}) != len(factors):
        raise UndefinedFit("duplicate incidence")
    # Connectivity/topology precede any numerical fit.
    reached_w, reached_i = {0}, set()
    for _ in range(ns+nw):
        reached_i |= {f['i'] for f in factors if f['w'] in reached_w}
        reached_w |= {f['w'] for f in factors if f['i'] in reached_i}
    if len(reached_w) != nw or len(reached_i) != ns:
        raise UndefinedFit("disconnected incidence")
    tree = len(factors) == ns+nw-1
    shared = [i for i in range(ns) if len(byscan[i]) > 1]
    if not tree and not (nw == 2 and len(shared) == 2 and all(len(byscan[i]) == 2 for i in shared)):
        raise UndefinedFit("unsupported incidence cycle")
    native = np.array([fit(f['p'], f['y']) for f in factors])
    for f, T in zip(factors, native):
        f['T'] = T
    G, Z = np.tile(np.eye(4), (nw,1,1)), np.tile(np.eye(4), (ns,1,1))
    constants = sum(float(np.mean(np.sum((f['y']-apply(f['T'],f['p']))**2,axis=1)))
                    for i in range(ns) if len(byscan[i]) == 1 for f in byscan[i])

    def fit_scans():
        for i, fs in enumerate(byscan):
            if len(fs) == 1:
                Z[i] = G[fs[0]['w']] @ fs[0]['T']
            else:
                src = np.concatenate([f['p'] for f in fs])
                target = np.concatenate([apply(G[f['w']], f['y']) for f in fs])
                weights = np.concatenate([np.full(len(f['p']),1/(len(fs)*len(f['p']))) for f in fs])
                Z[i] = fit(src,target,weights)

    def shared_cost():
        return sum(float(np.mean(np.sum((apply(G[f['w']], f['y'])-apply(Z[i],f['p']))**2,axis=1)))/len(byscan[i])
                   for i in shared for f in byscan[i])

    if tree:
        known_w, known_i = {0}, set()
        for _ in range(ns+nw):
            for f in factors:
                i,w = f['i'],f['w']
                if w in known_w and i not in known_i:
                    Z[i] = G[w] @ f['T']; known_i.add(i)
                if i in known_i and w not in known_w:
                    G[w] = Z[i] @ inverse(f['T']); known_w.add(w)
        # Native rigid fits are exact local return for all tree factors.
        shared_value = shared_cost()
        full_value = sum(float(np.mean(np.sum((apply(G[f['w']],f['y'])-apply(Z[f['i']],f['p']))**2,axis=1)))/len(byscan[f['i']]) for f in factors)
        Gs,Zs,objs,shareds = [G.copy()],[Z.copy()],[full_value],[shared_value]
        converged = True
    else:
        left,right,weights = [],[],[]
        for i in shared:
            fl,fr = [next(f for f in byscan[i] if f['w'] == w) for w in (0,1)]
            left.append(fl['y'][np.argsort(fl['rows'])]); right.append(fr['y'][np.argsort(fr['rows'])])
            weights.append(np.full(len(fl['p']),1/(2*len(fl['p']))))
        G[1] = fit(np.concatenate(right),np.concatenate(left),np.concatenate(weights))
        fit_scans()
        value = shared_cost()
        Gs,Zs,objs,shareds = [G.copy()],[Z.copy()],[value+constants],[value]
        converged = False
        for _ in range(MAX_SWEEPS):
            fs = [f for f in factors if f['w'] == 1 and f['i'] in shared]
            src = np.concatenate([f['y'] for f in fs])
            target = np.concatenate([apply(Z[f['i']],f['p']) for f in fs])
            weight = np.concatenate([np.full(len(f['p']),1/(2*len(f['p']))) for f in fs])
            G[1] = fit(src,target,weight)
            fit_scans()
            new_value = shared_cost()
            Gs.append(G.copy()); Zs.append(Z.copy()); objs.append(new_value+constants); shareds.append(new_value)
            if abs(new_value-value) <= STOP_TOL*max(1.,value):
                converged = True
                break
            value = new_value
    clean,native_clean = np.empty_like(data['raw']),np.empty_like(data['raw'])
    for f in factors:
        clean[f['sl']] = apply(inverse(G[f['w']]) @ Z[f['i']],f['p']) / data['scales'][f['w']]
        native_clean[f['sl']] = apply(f['T'],f['p']) / data['scales'][f['w']]
    return dict(clean=clean,native_clean=native_clean,native_T=native,G=G,Z=Z,
                G_trace=np.array(Gs),Z_trace=np.array(Zs),objective_trace=np.array(objs),
                shared_objective_trace=np.array(shareds),converged=np.array(converged),
                sweeps=np.array(len(Gs)-1),rel=inverse(Z[0])@Z[1])
