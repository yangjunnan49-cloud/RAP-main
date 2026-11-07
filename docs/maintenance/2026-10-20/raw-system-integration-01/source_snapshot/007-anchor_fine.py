"""Explicit-configuration coarse-anchor-preserving dense pose graph.

Requires the existing KISS-SLAM Python environment. No package is installed here.
"""
import argparse
import json
import resource
import signal
from pathlib import Path
import numpy as np

def fine(o,initial,anchors,coarse,pose_graph_config):
    from kiss_slam.pose_graph_optimizer import PoseGraphOptimizer
    p=PoseGraphOptimizer(pose_graph_config); initial=initial.copy()
    for i,t in zip(anchors,coarse): initial[i]=t
    for i,t in enumerate(initial): p.add_variable(i,t)
    for i in anchors:p.fix_variable(i)
    for i in range(len(o)-1):p.add_factor(i+1,i,np.linalg.solve(o[i],o[i+1]),np.eye(6))
    p.optimize(); estimates=p.estimates(); return np.asarray([estimates[i] for i in range(len(o))])

def check_inputs(o,initial,anchors,coarse):
    if o.ndim!=3 or o.shape[1:]!=(4,4) or initial.shape!=o.shape:raise ValueError('Require matching N x 4 x 4 odometry/initial arrays')
    if not isinstance(anchors,list) or not anchors or any(type(i) is not int for i in anchors):raise ValueError('Anchor source IDs must be nonempty integer list')
    if anchors!=sorted(set(anchors)) or anchors[0]!=0 or anchors[-1]>=len(o):raise ValueError('Require unique ascending in-range source IDs including0')
    if coarse.shape!=(len(anchors),4,4):raise ValueError('One coarse world pose per anchor required')
    for a in (o,initial,coarse):
        if not np.isfinite(a).all() or np.max(abs(a[:,3,:]-[0,0,0,1]))>1e-8:raise ValueError('Invalid finite homogeneous matrices')
        rot=a[:,:3,:3]
        if np.max(abs(rot.transpose(0,2,1)@rot-np.eye(3)))>1e-5 or np.max(abs(np.linalg.det(rot)-1))>1e-5:raise ValueError('Invalid rotations')

def cli():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('odometry','initial','anchors','config','output'):p.add_argument('--'+key,required=True,type=Path)
    a=p.parse_args()
    if a.output.exists() or not a.output.parent.is_dir():raise FileExistsError('Output must be fresh with an existing parent')
    signal.signal(signal.SIGALRM,lambda x,y:(_ for _ in ()).throw(TimeoutError('60s per capsule invocation ceiling')));signal.alarm(60)
    o=np.load(a.odometry,allow_pickle=False);initial=np.load(a.initial,allow_pickle=False);meta=json.loads(a.anchors.read_text());anchors=meta['anchor_frames'];coarse=np.asarray(meta['coarse_poses'],dtype=np.float64)
    check_inputs(o,initial,anchors,coarse)
    from kiss_slam.config.config import PoseGraphOptimizerConfig
    config=PoseGraphOptimizerConfig(**json.loads(a.config.read_text()));result=fine(o,initial,anchors,coarse,config)
    if result.shape!=o.shape or not np.isfinite(result).all() or np.max(abs(result[anchors]-coarse))>1e-8:raise ValueError('Output violates coarse-anchor contract')
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>4*2**30:raise MemoryError('Original per-Python-process memory ceiling')
    with a.output.open('xb') as f:np.save(f,result)
    signal.alarm(0)

if __name__=='__main__':cli()
