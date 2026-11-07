"""Validate HL0 outputs and write the bounded preflight completion record."""
import ast
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
from datetime import datetime,timezone

ROOT=Path('/mnt/e/githouse/RAP-main')
SLAM=Path('/mnt/e/githouse/RAP-SLAM')
OUT=ROOT/'docs/maintenance/2026-09-14/hl-v1/preflight-01'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(n): return json.loads((OUT/n).read_text())
def save(n,v):
    with (OUT/n).open('x') as f: json.dump(v,f,indent=2,allow_nan=False)

assert read('rng_validation.json')['passed'] and read('rng_fresh_process.json')['exact']
assert read('rng_fresh_process.json')['caller_states_restored']
assert read('bank_validation.json')['valid_se3']==40
assert read('bank_validation.json')['valid_support_scores']==40
assert all(not r['mismatches'] for r in read('provenance_validation.json'))
assert not (OUT/'failure.txt').exists() and not (OUT/'resource_blocker.json').exists()
for name,digest in read('bank_hashes.json').items():assert sha(OUT/'bank'/name)==digest
helpers=[SLAM/'scripts/hl0_preflight.py',SLAM/'scripts/validate_hl0_preflight.py',ROOT/'scripts/maintenance/hl0_provenance.py',Path(__file__).resolve()]
for p in helpers:ast.parse(p.read_text())
sources={str(p):sha(p) for p in helpers}
# Bound the final stability check to all used profile scans and parent metadata,
# plus all source/checkpoint inputs; full raw datasets were hashed at entry.
rechecked=0
for seq in ['05','06']:
    d=read(f'data_{seq}.json')
    for p,h in d['parent_files'].items():assert sha(p)==h;rechecked+=1
    assert sha(Path(d['parent'])/'pipeline/odom_poses.txt')==d['odometry_sha256']
    manifest=json.loads((Path(d['parent'])/'input_manifest.json').read_text())
    for p,h in manifest.items():
        if not p.endswith('.bin'):assert sha(p)==h;rechecked+=1
used=set()
for p in read('profile_pairs.json'):
    used.update([p['source_i'],p['source_j']])
    used.update(s['source_id'] for k in ['support_i','support_j'] for s in p[k])
scans=read('data_05.json')['scans']
for i in used:assert sha(scans[i]['path'])==scans[i]['sha256'];rechecked+=1
states={}
for repo in [ROOT,SLAM]:
    def git(*args):return subprocess.check_output(['git','-c',f'safe.directory={repo}','-C',str(repo),*args],text=True)
    states[str(repo)]=dict(head=git('rev-parse','HEAD').strip(),branch=git('branch','--show-current').strip(),status=git('status','--short'))
save('final_source_validation.json',dict(helper_sha256=sources,final_stability_hashes_rechecked=rechecked,used_profile_scan_count=len(used),git=states))
r=read('resource_summary.json');p=r['profiles'];times=[x['wall_s'] for x in p]
alloc=max(x['peak_allocated_bytes'] for x in p)/2**30
reserved=max(x['peak_reserved_bytes'] for x in p)/2**30
save('decision.json',dict(stage='HL0',decision='PASS',scope='Bounded engineering preflight only',HL1='NOT STARTED',H1='NOT EVALUATED',H2='NOT EVALUATED',HL2='NOT AUTHORIZED BY RESULTS',
    support_shortage_risk=True,completed_utc=datetime.now(timezone.utc).isoformat(),
    limitations=['10 resource pairs are correlated KITTI05 proximity samples, not stratified hard-loop evidence','HL1 four-stratum adequacy remains unknown','GT checks establish serialization precision, not a new physical accuracy certification','Official RAP rigidity selector adapter remains for HL1; no novelty certificate']))
report=f'''# HL0 preflight-01 report

2026-09-14. **HL0 PASS (bounded engineering prerequisites). HL1 NOT STARTED.**
H1/H2 have not been evaluated; this is not GO for training or evidence of hard-loop
accuracy. The owner requested HL0 only in this execution turn.

## Provenance and geometry

- Complete KITTI 05 source IDs 0-2760 (374 frozen keyframes) and KITTI 06
  source IDs 0-1100 (202 frozen keyframes) verified against the full-run parents.
- All 3,862 scans are present, nonempty, finite float32 XYZI with exact source
  names. All 3,996 parent manifest hashes match, including current RAP source,
  both checkpoints, calibration and GT. All timestamp counts, monotonicity and
  persisted values match the actual times.txt files. Parent reports/validation
  are present and parent INCOMPLETE markers absent.
- M0 snapshot manifest integrity matches its recorded digest and contains 1,568
  entries; INCOMPLETE is absent. Archived payloads were not all rehashed here.
  This remains same-volume preservation, not independent backup.
- Synthetic noncommuting rigid-transform transport checks: maximum point error
  3.55e-15, composition error 8.88e-16. Tested strict 1 m/5 degree labels on
  either side of thresholds, reflection rejection, invalid empty support,
  causal target selection, duplicate collapse and age exclusion.
- Maximum absolute GT rotation orthogonality residuals: 1.71e-7 (05), 1.80e-7
  (06). SVD projection used only for a rounding diagnostic changes an element
  by at most 9.31e-8. Saved hypotheses are never projected to repair validity.
  These checks support numerical labels against the supplied benchmark GT;
  they do not independently establish physical sensor/GT uncertainty.

## Support feasibility and sampling

| Sequence | Keyframes | Two distinct supports | One support | Zero supports |
|---|---:|---:|---:|---:|
| 05 | 374 | 51 | 321 | 2 |
| 06 | 202 | 22 | 179 | 1 |

The frozen keyframes often cross 2 m and 5 m at the same preceding frame, which
must collapse to one support under HL-V1. No frame-spacing or age rule was relaxed.
Local travel accumulates every frozen odometry step, not straight-line displacement.
Support metadata, timestamps and local poses are persisted for both sequences;
no KITTI 06 hypotheses or outcome labels were generated or inspected.

For resource profiling only, enumerated all KITTI 05 keyframe proximity pairs
within 30 m and separation >=200; 35 have two distinct causal supports per side.
The first ten by the declared HL-V1 pair hash were frozen before inference.
This is a feasibility sample, not the HL1 SC/proximity population, not the
four-stratum cohort, and not subject to the HL1 per-query stratified selection.
The complete profile candidate registry includes unsupported pairs. HL1 still
must build the expanded SC population, apply the three-per-query cap and four
stratum minima, and preserve shortages. The sparse support pool is a material
adequacy risk; it cannot justify a quantitative PASS or threshold relaxation.

## GPU and RNG results

Ten pairs, K=4 each: 40/40 outputs valid SE(3), 40/40 complete support scores,
160 valid support combinations, no inference failure and no CUDA OOM.
Four further generations were executed strictly for RNG validation, not added
to the hypothesis bank or used to improve any result.

- Synchronized complete pair wall time: {sum(times):.3f} s total;
  median {statistics.median(times):.3f} s, range {min(times):.3f}-{max(times):.3f} s.
- Peak allocated GPU memory: {alloc:.3f} GiB; peak reserved: {reserved:.3f} GiB.
  Reserved memory includes allocator retention between pairs.
- Main preflight script elapsed time: {r['total_wall_s']:.3f} s, including
  geometry/support enumeration, model load, profiles and three RNG repeats.
  This excludes provenance hashing, the separate fresh-process validator,
  documentation and literature review. GPU kernel-active time and human labour
  were not separately instrumented; do not equate wall time with GPU-active time.
- Pair timings include raw reads, four support scans' geometric preprocessing,
  four anchor generation calls (including learned features), all support scores
  and result writes. Inputs were warmed by the full provenance read; no cold-I/O
  benchmark or broad difficult-cohort throughput guarantee is claimed.
- Request seeds follow the exact protocol with dataset `kitti`, sequence `05`,
  ordered historical source_i < source_j and zero-based generation 0-3. Each
  request seeds/restores Python, NumPy, CPU/CUDA PyTorch RNG and backend cap seed.
  Geometric support uses the same rules with fixed cap seed 42 and no learned
  support features. Neural anchor features remain enabled.
- Isolated repeat, reversed request order, saved cache reload and a new-process
  first request all recover transforms exactly (maximum element difference 0).
  Caller RNG/backend states restore exactly. Declared tolerance was 1e-6.
  Cache means a hash-bound saved hypothesis lookup; no general cache service exists.
- Maximum hypothesis orthogonality residual 1.65e-6, determinant error 1.55e-6,
  within the existing 1e-5 validity threshold. IEEE rigid-fit protection retained.

Strict/legacy labels are in an evaluator-only file; no GT fields enter the
support score. No B1/B4/S4/OR4 pilot comparison, fitted score or trained head exists.
The 40 hypotheses are an immutable preflight bank, not the forthcoming HL1 bank.

## Literature and limitations

See [bounded primary-source difference matrix](LITERATURE_DIFFERENCE.md).
RAP rigidity selection, trajectory-prior verification, sequential descriptor
evidence and learned hypothesis scoring are established prior work. RegScorer
adds a close overlap to inspect before HL2. Publisher full-text access was limited
for the learned scorers; this limitation is explicit and no novelty certificate
is claimed. The official RAP rigidity selector exists upstream but the current
pair wrapper does not export its trajectory statistic; B4 must be named accurately.

## Validation, files and exact next step

The independent validator checked all bank seeds, geometry and four-way support
availability, cache contents, fresh-process repeat and strict evaluator labels.
Final stability recheck covered {rechecked} hashes including {len(used)} used scans,
both parent metadata sets and non-scan source/checkpoint manifests. Four helper
files parse successfully. The artifact hash manifest binds all final outputs.

New algorithm helpers are only in RAP-SLAM/scripts/hl0_preflight.py and
validate_hl0_preflight.py. RAP-main adds maintenance audit/finalization helpers
and documents; model source and production defaults are unchanged. WSL required
sandbox escalation, which was approved; the initial default attempt was denied.
No unresolved execution exception remains. Existing dirty worktrees are preserved;
HEADs remain 4055d92 / 6d3f2d2 on main. No commit/push/pull/reset/cleanup occurred.

Next authorized research continuation: create a fresh hl-v1/pilot-01, implement
the exact broader candidate registry and evaluator-only strata, check adequacy
before expensive inference, and run HL1 discovery on 05. Freeze its report before
06 confirmation outcomes. Reuse the verified conventions and request seed policy,
not the preflight cohort as hard-loop validation. Inadequacy means INCONCLUSIVE;
no training or manuscript restart follows from this HL0 PASS.
'''
(OUT/'REPORT.md').write_text(report)
save('artifact_hashes.json',{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='INCOMPLETE'})
(OUT/'INCOMPLETE').unlink()
print(json.dumps(read('decision.json'),indent=2))
