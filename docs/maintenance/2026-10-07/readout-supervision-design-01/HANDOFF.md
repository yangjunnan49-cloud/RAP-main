# DS0 read-only design handoff

READ_ONLY_DESIGN_COMPLETE, decision BOUNDED_EXPOSED_READOUT_PILOT_DRAFT.
Read REPORT,DATA_ROLES,TRAINING_ANNEX_DRAFT,NEXT_ROUND_PLAN,DATA_AUDIT,
WINDOW_MANIFEST_DRAFT,source_snapshot,STATUS and DELIVERY_SEAL.
Audit34.801s CPU only;23201 KITTI00-10 raw name/size entries, matching finite
12-column pose/1-column increasing timestamp/Tr schemas. No raw numeric cloud
payload, relative GT/label/error, model inference, GPU, head or fitting.
Pose files read for schema only, explicitly disclosed; no numeric poses retained.
Oxford five TUM files but no expected scans/calibration; unrelatedpart2 excluded.

Draft204 windows:144fit00-05,12development06,48exposed evaluation07-10;
count-only spaced target indices,no shared raw frame path. Not a science freeze,
site independence or checkpoint exclusion. Paper includes Oxford training and
excludes KITTI08-10; local checkpoint binding UNKNOWN. Historical02 M3/06/E0/
08 exposure remains. Very short KITTI GT noise prevents precise physical
correspondence claims; use weak set positives/dustbin/ignore/third-view support.
Oxford loader omits sensor extrinsic; anchoring does not generally remove lever
arm. No official GT or production loader edited.

Concrete RLP1 annex: frozen RAP+descriptor; matched521->128->64 small head for
D descriptors,I separated-context tokens,J joint tokens. I grouping is source-
feasible, not runtime validated; possible one-part OOD and differing attention
cost disclosed. Nominal75202 parameters,D13762 effective from zero padding,
I/J matched active capacity. Three fixed seeds x1000 updates, no search/selection.
Original-point SE3 solver; coupled weak motion loss and declared readout-only
proper-GT-rotation angular convention, no official metric rewrite. Prerequisites,
four preflight windows and full-bank/label/evaluator separations are specified.
Artifact cap4GiB,GPU3GiB,RSS4GiB,all compute<=60min,perfit<=5min.

Current no-fitting authorization persists. Next explicit owner scope can cover
only this bounded isolated head pilot plus mandatory prerequisites, never
backbone retraining or system/default promotion. Primary I/D comparison must
improve BOTH R/t,then G3/KISS usefulness. No pass means no trajectory; a pass
still requires a new full ter/ATE system protocol. No independent/site physical
confirmation or novelty is established. Do not keep expanding generic audits.

TR0 freeze/bank/validation rechecked unchanged before/after. All prior stopped
routes/scientific banks/official labels/metrics,09 discrepancy,unknown local
membership and original-breakthrough requirement remain. Both original HEADs/
branches/dirty work preserved. No training,acquisition/install,production/
default/model/manuscript edit,commit or Git synchronization. Draft code and
protocol must be implemented/frozen prospectively after the required scope;
DS0 source snapshot is an audit ledger, not a prospective experiment freeze.
