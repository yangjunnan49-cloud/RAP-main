# S0 matched-noise 5→10-step preflight — complete

Decision: **PASS_STEPCOUNT_PREFLIGHT**, engineering only. RAP's released
inference config/demo defaults to 10 Euler steps, while RAP-SLAM/F2 use 5.
The frozen [protocol](PROTOCOL.md) fixed four saved-order pairs per
KITTI00/08 (indices 0,25,50,75), native generation k=0, identical six
corrected scans, sampled points, descriptors, normalized inputs and
explicit F2 noise. Protocol, code, validator, model weights and 139
source/input identities were SHA-frozen before inference.

All eight regenerated 5-step native raw clean endpoints **and** noisy
states matched their saved F2 N0 arrays exactly (maximum delta 0.0).
The same-input/noise 10-step native runs each produced finite 10×8000×3
raw and state trajectories and valid final relative SE(3) poses. The
model step count was restored to 5 after each run; scoped RNG and
precision states were checked. No GT or success labels were loaded,
so this says nothing about 10-step efficacy.

The eight-output bank was SHA-sealed before independent review. Wall
26.891s, peak allocated VRAM 2.414GiB, artifacts 14.23MB, all within
the 10min/12GiB/1GiB caps. Independent [`validation.json`](validation.json)
passed 232 checks, including frozen identities, exact pair order and
input convention, saved 5-step reproduction records, every 10-step
array's shape/finiteness and independent CPU pose decoding. `INCOMPLETE`
was removed after bank seal, before validation. No production/default
change, training, download or Git synchronization occurred.

This pass permits a separately frozen full observed-development K4
5-vs-10-step screen using the existing F2 native N bank as the exact
5-step comparator, unchanged R4 selection/gate and evaluator-only GT.
Neither 10 steps nor a new thesis mechanism is selected by S0 alone.
