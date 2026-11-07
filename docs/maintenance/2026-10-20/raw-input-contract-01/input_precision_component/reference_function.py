import numpy as np

def kitti_vertical_correction(points: np.ndarray,
                              angle_deg: float = 0.205) -> np.ndarray:
    """KITTI HDL-64 intrinsic vertical-angle correction (S0b).

    Exact CT-ICP convention (jedeschaud/ct_icp src/ct_icp/dataset.cpp,
    KITTI_GLOBAL_VERTICAL_ANGLE_OFFSET = 0.205, "Issue in the intrinsic
    calibration of the KITTI Velodyne HDL64"; same convention in MULLS /
    Traj-LO): every point p is rotated by +angle about the horizontal axis
    a = normalize(p x z_hat) — i.e. the axis perpendicular to the point's
    azimuth direction. Since a is perpendicular to p, Rodrigues reduces to
        p' = p cos(t) + (-x*z/rho, -y*z/rho, rho) sin(t),
    rho = sqrt(x^2+y^2). Points with rho ~ 0 (near-vertical) are untouched.
    """
    t = np.deg2rad(angle_deg)
    x, y, z = points[:, 0], points[:, 1], points[:, 2]
    rho = np.hypot(x, y)
    safe = rho > 1e-6
    c, s = np.cos(t), np.sin(t)
    out = points.copy()
    sxz = np.where(safe, x * z / np.maximum(rho, 1e-6), 0.0)
    syz = np.where(safe, y * z / np.maximum(rho, 1e-6), 0.0)
    sz = np.where(safe, rho, 0.0)
    out[:, 0] = np.where(safe, x * c - sxz * s, x)
    out[:, 1] = np.where(safe, y * c - syz * s, y)
    out[:, 2] = np.where(safe, z * c + sz * s, z)
    return out
