# G1: fixed full-scan external global-registration comparator

G0's equal 2000-point KISS-Matcher control produced <5 final inliers on
199/200 pairs, making it a weak representation of this established method.
This separately scoped G1 tests the same official wheel, 0.3 m resolution,
all 200 exact F2 pairs, but supplies the full raw anchor scans after the F2
range>=1.5 m filter and exact 0.205 deg KITTI correction. This is a strong
external component baseline at a much larger point/computation budget; it
is not an equal-budget RAP comparison, new mechanism, or G0 parameter rescue.
No supports, GT, cross-visit odometry, initialization, learned adaptation or
pair selection enters registration.

Freeze protocol, G1 runner and independent validator, G0's pinned official
KISS-Matcher 1.0.2 wheel and extracted files, the unmodified RAP-SLAM
`real_dataset.py` correction source, all raw i/j scan identities and F2
pair/evaluator/GT identities before running any real pair. Run one fresh
`KISSMatcher(KISSMatcherConfig(0.3)).estimate(source_j,target_i)` per pair,
single threaded CPU. Record full input counts, inliers, pose, time and any
failure; never drop a pair. Runner hashes frozen labels but does not parse
them. SHA-seal the complete pose bank before evaluator labels are opened.

Reuse the G0 evaluator's exact strict <=1m/<=5deg and clipped positive
error semantics, 75 positives/25 confusers per sequence, native N/R4 and
N-OR4 paired diagnostics and the **same frozen G0 prospective decision
gate**: on 08 >=5 recoveries from native K4-unavailable, >=5 net strict
gains, clipped error <=0.95x native; on 00 no more than 3 net strict
losses. Any passing result only establishes independent external candidate
headroom and licenses a separately frozen integration question with
KISS-Matcher-alone, native RAP and cost controls. It cannot be described
as a RAP algorithmic gain. A failing result stops this fixed full-scan
baseline configuration, not all global registration.

Full raw point counts and cost must be reported next to G0's 2000-point
results. Independent validation rehashes sources and raw inputs, checks
bank/identity/SE(3), recomputes labels and decision. Caps: <=45 min CPU
wall, <=8 GiB peak RSS, <=2 GiB new artifacts. No GPU, downloads,
training, production edits or Git sync. If native package execution is
unstable or caps fail, report INCONCLUSIVE_ENGINEERING rather than adjust
the fixed resolution or data convention.
