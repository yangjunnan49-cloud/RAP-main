"""Fixed external odometry adapter; requires the existing KISS-SLAM environment."""
import numpy as np

class FixedOdometry:
    def __init__(self,c,o):
        from kiss_icp.kiss_icp import KissICP
        original=KissICP(c); self.local_map=original.local_map; self.preprocessor=original.preprocessor; self.voxelize=original.voxelize
        self.o=o; self.index=-1; self.anchor=0; self._pose=np.eye(4); self.last_delta=np.eye(4); self.resets=[]; self.max_relative_error=0.
    @property
    def last_pose(self): return self._pose
    @last_pose.setter
    def last_pose(self,t):
        assert np.max(abs(t-np.eye(4)))<=1e-12
        self.anchor=max(self.index,0); self._pose=np.eye(4); self.resets.append(self.anchor)
    def register_frame(self,frame,timestamps):
        self.index+=1; frame=self.preprocessor.preprocess(frame,timestamps,self.last_delta); source,down=self.voxelize(frame)
        new=np.linalg.solve(self.o[self.anchor],self.o[self.index])
        # Independent expression for this rigid relative pose.
        ai=self.o[self.anchor]; expected=np.eye(4); expected[:3,:3]=ai[:3,:3].T@self.o[self.index,:3,:3]
        expected[:3,3]=ai[:3,:3].T@(self.o[self.index,:3,3]-ai[:3,3]); self.max_relative_error=max(self.max_relative_error,float(np.max(abs(expected-new))))
        self.local_map.update(down,new); self.last_delta=np.linalg.solve(self._pose,new); self._pose=new
        return frame,source
