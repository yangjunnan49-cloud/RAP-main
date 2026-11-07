# E0 execution continuation after host/session interruption

2026-09-27. Owner requested continuation. The prior tool session no longer
exists; a read-only process listing after WSL startup shows no experiment.
The exact cause/time of termination is unknown. All four KITTI00 cells contain
complete poses/IDs/metrics. KITTI05-O directory contains no files. No selection
or complete-system outcome exists. Do not rerun KITTI00 or overwrite any file.

Verify original frozen sources and inputs, independently recompute the four
completed cells, then inherit them by SHA256. Resume only KITTI05/06 under
resume-01/odom-*. Leave the empty interrupted directory untouched. Existing
arm definitions, ordering, selection gates, evaluation and full-system settings
are unchanged. New full runs use the unused original full-* paths. The source
of the continuation runner and validator is frozen in resume_freeze.json before
new inference; the original runner, protocol and freeze remain unchanged.

This administrative continuation does not create independent evidence. Runtime
accounting records completed-cell wall times plus resumed process wall. Time
spent inside the interrupted cell is unknown and is explicitly not presented
as total compute cost. Reserve 1800s of the original 7200s engineering cap for
the prior process, allowing at most5400s resumed wall; full-system process cap
remains1800s. This reserve is a budget policy, not a measured upper bound on
the unobserved interrupted interval. A host interruption is not a method failure.

No F1 GPU process starts until E0 generation is complete. F1 has a separate
frozen protocol, four inputs and successful synthetic validation already saved.
