# Estimated matrix convention and case-local frames

The five matrices are two views from case-000 and three views from case-001. Each registration has its own learned common frame/gauge. No alignment between the two case-common frames is authenticated. These are not a five-frame odometry trajectory or five poses in one physical global world.

Each4x4 matrix T_i maps original input-view coordinates into that case's common frame: column convention y=T_i x; row arrays use y=x R_i^T+t_i. Within the same case only, the source-to-reference mapping is inverse(T_reference) T_source. The pair backend already returns this relative mapping; no extra generic recovery or second inversion is needed.

Coordinates retain the backend's assumed input units, which have not been independently authenticated as physical metres. Valid rigidity, fit consistency and exact text roundtrip do not establish real alignment accuracy or truth. The active text exports are in output-contract-01/run02/verify; the first serialization-failed run is historical evidence, not a final result.

The clarified case-local ZIP adds this note and explicit case groups without changing any matrix bytes. Earlier packages and their hashes remain immutable. No new model, pose, metric, calibration or cross-case registration is computed.
