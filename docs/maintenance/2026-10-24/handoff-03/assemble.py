"""Add compact current pointers while preserving every prior byte."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
day=root.parent;repo=root.parents[3];continuation=day/'continuation-02'
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def write(name,value):
    with (root/name).open('x') as f:json.dump(value,f,indent=2)
old=(repo/'AGENTS.md').read_bytes()
with (root/'AGENTS.before.md').open('xb') as f:f.write(old)
header='''# October24 second renewal: source decision and review figures

Read docs/maintenance/2026-10-24/continuation-02/CURRENT_HANDOFF.md first for compact current authority. The owner explicitly renewed continuation at07:18:58UTC,4%/ordinaryTRUE/reset1792844337;30%/ordinaryTRUE at07:28:47UTC is not exhaustion. Current supplied receipts/later actual stop govern. Prior window boundary is UNOBSERVED: last conversation100%/ordinaryTRUE and saved98% do not establish ordinary-disabled or a quota-review failure. No automatic reset continuation or scheduler/goal-status change.

RC2 binds22 existing records/14 citations and closes the source/sampling-unit review: two augmentation cases/five view occurrences are one named scene/three source files, not independent confirmation.56557 point occurrences and60000 coordinate checks retain their occurrence meanings. No new raw/private/reference/model/metric reads or efficacy/cohort admission. Next scientific dependency is an owner-identified original local acquisition/reference/cohort record, then mechanism/role review; no more synthetic/interface prototypes can supply it. Research UNRESOLVED/manuscript PAUSED and all old failures/caps/stops remain.

OV1 adds two sealed-output-only geometry figures without model replay, new fit/pose/GT metric. Outer status-string and first preflight Windows/POSIX basename failures remain preserved. Frozen runtime02 changes path binding only, other worker AST/origin identical; repaired preflight/first render PASS and total327.188249/900s includes all failures/repair. Active PNGs are output-visualization-01/run02/plots. WSL initialStopped restored07:28:09UTC, exact scoped helper matches0; E VHD/backup/Junction retained, direct boot without link untested. No production/default/install/Git/outreach changes. All earlier AGENTS bytes follow verbatim and are backed up in handoff-03.

---

'''.encode()
(repo/'AGENTS.md').write_bytes(header+old)
assert (repo/'AGENTS.md').read_bytes()[len(header):]==old
phase=day/'PHASE_RECORD.md';previous=phase.read_bytes()
with (root/'PHASE_RECORD.before.md').open('xb') as f:f.write(previous)
append=b'''

# Second explicit October24 renewal

New window reset1792844337,4%/ordinaryTRUE at07:18:58UTC;30%/ordinaryTRUE at07:28:47UTC is NOT exhaustion. Previous window boundary remains UNOBSERVED, no actual disabled/review-failure receipt invented. Seven old closed costs and both delivery package hashes match.

RC2 completes22-source/14-citation physical-reference/cohort and sampling-unit review at276.351109/1200s. One named scene/three source files/two augmentations, no independent-confirmation admission. Source evidence specification and conditional comparison are concrete; no new model or metric is admitted. Owner source-path input is requested.

OV1 adds two public sealed-output figures at327.188249/900s. Retained outer Replace overload and admitted POSIX/Windows basename failures; frozen path-only runtime02 preserves all other worker AST/origin/input/config. Repaired preflight/first render PASS, worker98,738,176 bytes/watch99,237,888; model/GT/fit0. Native visual QA PASS; WSL initialStopped restored07:28:09UTC, exact helper0. Old scientific failures/caps/references and E backup/Junction remain, research UNRESOLVED/manuscript PAUSED. No Git/install/production/default/outreach/scheduler/goal-status change.
'''
phase.write_bytes(previous+append)
assert phase.read_bytes()[:len(previous)]==previous
source=(day/'continuation-01/record_account.py').read_text()
assert source.count('1792825078')==1
with (continuation/'record_account.py').open('x') as f:f.write(source.replace('1792825078','1792844337'))
write('ADDITIVE_POINTER_CHECKS.json',dict(passed=True,previous_AGENTS_sha256=sha(old),
    previous_AGENTS_verbatim_suffix=True,previous_phase_sha256=sha(previous),previous_phase_verbatim_prefix=True,
    account_writer_only_expected_reset_changed=True,old_account_pointer_not_written=True))
print(json.dumps(dict(additive_pointers=True,old_AGENTS_bytes_preserved=len(old))))
