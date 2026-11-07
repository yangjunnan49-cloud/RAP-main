# 2026-09-26 phase record

## Context recovery and research discussion

Read AGENTS.md, HC-V1 report/table/validation, the 2026-09-19 phase record and
the structured-generation research memo. Inspected both repository statuses:
HEADs remain 4055d92 / 6d3f2d2 with existing uncommitted work preserved.

Owner clarified HC-V1's weekly-meeting purpose and requested a return to the
research mainline, asking how VGGT-SLAM informs the original RAP-SLAM vision.
Read primary VGGT-SLAM 1.0/2.0 and RAP sources and inspected the official 1.0
solver and local pairwise registration path. Recorded findings and explicitly
unvalidated recommendations in [assessment](VGGT_SLAM_RESEARCH_ASSESSMENT.md).

Only handoff and maintenance documentation changed. No new experiment, GPU
inference, training, download campaign, cohort selection, production edit or
Git synchronization. Saved HC-V1 checks were read, not rerun. Documentation
checked for consistency with pending E0/F1 status and preservation of stops.

Next: existing F1 prospective engineering preparation remains the research task;
E0 remains a recommended engineering proposal requiring its specific approval
and prospective protocol. No broad architecture replacement selected.

## Later execution approval and preparation

Owner explicitly approved E0 followed by F1, superseding the earlier approval
boundary. Actual source inspection recovered unrecorded meeting_20260921
branches in both repositories, with unchanged old HEADs and extra uncommitted
meeting defaults/wiring edits in run_pipeline.py and odometry.py. The combined
frontend had already run on 00/05/06. Presentation/draft materials exist under
docs/meeting_20260921. All are preserved as prior observed development evidence.

Created codex/e0-f1-20260926 in both repositories, preserving dirty work and
commits. No commit/push. Baseline configs verify K1 and NMS0; HC table K4/NMS10
introductory prose is incorrect. New E0 protocol and source ZIP/hash freeze
preceded execution; 8421 input identities checked against baseline manifests.

F1-V1 protocol, isolated sampler and four exact KITTI00 pairs were prepared and
frozen. The 24 raw scans and local motions were verified against the original
causal odometry. New RAP-SLAM files: rap_slam/structured_motion.py and
scripts/structured_motion_preflight.py. 20 synthetic geometry/gauge trials passed
with maximum matrix difference1.916e-6. Pre-freeze setup fixes corrected a
validator import path and evaluator-hash lookup in the historical manifest.
No real F1 model inference occurred. Upstream and production files unchanged.

An additional read-only syntax-check command was not executed because automatic
approval review hit a usage limit; it was not classified unsafe. E0 had already
started. Exact continuation state was recovered on 2026-09-27; see that date's
phase record. Do not rerun completed E0 cells or launch the original runner.
