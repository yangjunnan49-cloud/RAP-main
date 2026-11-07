# VR1 existing RAP environment lacks cv2

The exact existing rap-inference environment reports cv2 absent, NumPy/SciPy present and skimage absent. No classical feature or solver API can be admitted from this environment. This is an environment dependency result, not a failed image baseline or a reason to install into the existing project environment automatically.

One probe exits2 with explicit ImportError before any cv2/NumPy import, image/point/pose/model or feature/solver call. Native elapsed0.010856292999999795s, peak15196160bytes; Windows enclosing launch3.821383s, no forced stop. Fresh host headroom86622113792bytes/query0.3834s. Existing source/metadata untouched, no package installation. Initial WSLStopped restored and confirmed in WSL_FINAL.json. Old archive/image scopes and scientific failures remain unchanged.

Before proposing a new installation, a separate bounded metadata-only census can inspect the remaining three exact interpreter paths already identified in the sealed migration records. It must not reinterpret this rap-inference result or run an image experiment without a compatible method/runtime freeze.
