# Pre-payload setup observations

Read existing SGC0 handoff/next plan, historical ICP comparator, PFG source/screens and physical cache/input provenance. No scientific payload yet.

First API-only WSL probe imported `open3d` and then explicitly `open3d.cpu.pybind`. It stopped with `ImportError: generic_type: type "Vector3dVector" is already registered!` before version/signature output, raw reading or any registration. Tool process wall4.2104872s; no captured ru_maxrss/child supervision. Preserve this gap; do not count it as a successful numerical stage or claim all-setup resource capture.

A following read-only entry-source command was not executed because automatic approval review could not complete due account usage limits. This was a review availability failure, not a safety finding. After the owner's "请继续", the same read-only check was retried successfully through the approval path; no bypass.

Installed entry source selects CUDA symbols when a visible CUDA device exists and otherwise CPU. A corrected API-only probe sets `CUDA_VISIBLE_DEVICES` empty in its own process before a single `open3d` import. It reports version0.19.0, selected CPU, binary `/root/miniconda3/envs/rap-inference/lib/python3.10/site-packages/open3d/cpu/pybind.cpython-310-x86_64-linux-gnu.so`, GICP API and explicit `(N,3,3)` covariance property. Tool process wall3.7397344s; setup RSS not captured. No configuration/install/process restart, numerical registration or project model load.

The frozen scientific runner uses the successful single CPU-binding route. Full scientific resource capture begins with its supervised freeze process; pre-payload inventory gaps are not retroactively repaired.

Primary references: [Open3D GICP API](https://www.open3d.org/docs/release/python_api/open3d.pipelines.registration.registration_generalized_icp.html), [Open3D0.19 GICP source](https://raw.githubusercontent.com/isl-org/Open3D/v0.19.0/cpp/open3d/pipelines/registration/GeneralizedICP.cpp), [registration loop source](https://raw.githubusercontent.com/isl-org/Open3D/v0.19.0/cpp/open3d/pipelines/registration/Registration.cpp). The installed binary is hashed; the online source documents the tagged implementation but is not proof of bit-identical binary compilation.
