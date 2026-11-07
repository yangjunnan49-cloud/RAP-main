"""Custom public-input normalization and conditional rigid-transform recovery."""
import math, sys
TOL=1024*sys.float_info.epsilon


def finite(value):
    if not isinstance(value,(float,int)) or not math.isfinite(value):
        raise ValueError('finite real scalar required')
    return float(value)


def rigid(matrix):
    if len(matrix)!=4 or any(len(row)!=4 for row in matrix):
        raise ValueError('4x4 matrix required')
    a=[[finite(x) for x in row] for row in matrix]
    if max(abs(a[3][j]-(1. if j==3 else 0.)) for j in range(4))>TOL:
        raise ValueError('homogeneous row invalid')
    for i in range(3):
        for j in range(3):
            if abs(math.fsum(a[k][i]*a[k][j] for k in range(3))-(i==j))>TOL:
                raise ValueError('nonrigid prediction')
    det=(a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])
         -a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0])
         +a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]))
    if abs(det-1.)>TOL:raise ValueError('improper rotation')
    return a


def normalize(views):
    if not views or any(not isinstance(key,str) or not key for key in views):
        raise ValueError('named public views required')
    points={}
    for key,rows in views.items():
        if not rows:raise ValueError('empty view')
        points[key]=[]
        for row in rows:
            if len(row)!=3:raise ValueError('XYZ points required')
            points[key].append([finite(x) for x in row])
    centers={key:[math.fsum(row[j] for row in rows)/len(rows) for j in range(3)] for key,rows in points.items()}
    scale=max(abs(row[j]-centers[key][j]) for key,rows in points.items() for row in rows for j in range(3))
    if not math.isfinite(scale) or scale<=0:raise ValueError('degenerate shared scale')
    normalized={key:[[(row[j]-centers[key][j])/scale for j in range(3)] for row in rows] for key,rows in points.items()}
    return normalized,dict(version='CUSTOM_RIGID_V1',view_ids=list(points),centers=centers,shared_scale=scale)


def recover(predictions,metadata,reference):
    if set(metadata)!={'version','view_ids','centers','shared_scale'} or metadata['version']!='CUSTOM_RIGID_V1':
        raise ValueError('custom shared-scale metadata required')
    ids=metadata['view_ids'];centers=metadata['centers'];scale=finite(metadata['shared_scale'])
    if scale<=0 or len(set(ids))!=len(ids) or set(predictions)!=set(ids) or set(centers)!=set(ids) or reference not in ids:
        raise ValueError('scale/view identity mismatch')
    if any(len(centers[key])!=3 for key in ids):raise ValueError('center shape')
    centers={key:[finite(x) for x in centers[key]] for key in ids}
    transforms={key:rigid(predictions[key]) for key in ids};ref=transforms[reference]
    result={}
    for key,a in transforms.items():
        rotation=[[math.fsum(ref[k][i]*a[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
        translation=[math.fsum(ref[k][i]*(a[k][3]-ref[k][3]) for k in range(3)) for i in range(3)]
        recovered=[rotation[i]+[math.fsum([scale*translation[i],centers[reference][i]]+[-rotation[i][j]*centers[key][j] for j in range(3)])] for i in range(3)]
        result[key]=recovered+[[0.,0.,0.,1.]]
    return result
