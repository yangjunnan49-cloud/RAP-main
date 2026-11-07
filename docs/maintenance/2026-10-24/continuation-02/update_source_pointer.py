"""Additive live handoff pointer after all source/model scopes have closed."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent;day=root.parent;repo=root.parents[3]
old=(repo/'AGENTS.md').read_bytes()
with (root/'AGENTS.before_source_pointer.md').open('xb') as f:f.write(old)
header=b'''# October24 concrete upstream-page decision pending

Read docs/maintenance/2026-10-24/continuation-02/SOURCE_POINTER_ADDENDUM.md, then CURRENT_HANDOFF.md. PSR2 binds3 already acquired metadata files by length/SHA256/published Git blob and identifies https://npm3d.fr/parisluco3d. source-request-01/REQUEST_PLAN.json is a concrete one-page/four-request/256KiB/60s-worker/120s-attempt proposal; external requests0. Owner authorization was requested and remains pending unless a later actual human answer/authorization receipt supersedes this pointer. Silence/preselection is not approval. Original-record requirement comes from AUTHENTICATION_DEPENDENCIES; no linked downloads/outreach/inference follow automatically. Exact RegX-to-upstream crosswalk and physical/reference/cohort membership remain UNKNOWN.

PSR2's initial default-GBK text decode failure and original source are preserved; prepare02 changes explicit UTF-8 text decoding only, other AST identical. Both attempts close120.040495/600s. CLOSED_SCOPES_WITH_SOURCE_REQUEST records12 closed scopes additively. Immutable110-member review ZIP SHA2563095B9068E67B034C4B32661F61E56D6BD7DBD9E8DC433A1F934C6DD83DB4BDD remains unchanged. Scientific/model/array scopes are closed; continuation/account availability is separate. Last saved47%/ordinaryTRUE/reset1792844337 at07:35:23UTC is NOT exhaustion. No automatic reset continuation, scheduler or goal-status change; original research UNRESOLVED/manuscript PAUSED. All earlier limits/failures/WSL E image/backup/Junction remain, old AGENTS bytes verbatim below/backed up.

---

'''
(repo/'AGENTS.md').write_bytes(header+old)
assert (repo/'AGENTS.md').read_bytes().endswith(old)
phase=day/'PHASE_RECORD.md';previous=phase.read_bytes()
with (root/'PHASE.before_source_pointer.md').open('xb') as f:f.write(previous)
phase.write_bytes(previous+b'''

# Concrete upstream pointer, external authorization pending

PSR2 length/SHA256/Git-blob verifies3 retained author metadata files and identifies the literal ParisLuco3D project URL. Fixed source request prepared; HTTP requests0. Initial Windows default-GBK decode error/source preserved; prepare02 only adds UTF-8, same original120.040495/600s account. Twelve closed scopes retain old results/caps. Requested owner authorization for one page/four requests/256KiB/60s worker/120s attempt; no linked data/paper/weights/outreach. Await actual human response or local original source, never infer approval from silence/preselection.47%/ordinaryTRUE at07:35:23UTC is not account exhaustion. E WSL image/backup/Junction retained, initialStopped restored, research UNRESOLVED/manuscript PAUSED.
''')
with (root/'SOURCE_POINTER_UPDATE_CHECKS.json').open('x') as f:json.dump(dict(passed=True,
    prior_AGENTS_sha256=hashlib.sha256(old).hexdigest().upper(),prior_AGENTS_verbatim_suffix=True,
    prior_phase_sha256=hashlib.sha256(previous).hexdigest().upper(),prior_phase_verbatim_prefix=True,
    closed_scope_costs_or_delivery_packages_changed=False,external_requests=0),f,indent=2)
print(json.dumps(dict(additive=True,source_authorization_pending=True,external_requests=0)))
