"""Final immutable-artifact/source identity receipt; no numerical reruns."""
import subprocess
from pathlib import Path
import flow_directional_response as f

BASE=f.B.parent
NAMES=['dense-propagation-screen-01','joint-loop-oracle-01','geotransformer-feasibility-01','online-geotransformer-01','online-geometry-consistency-01','temporal-identity-audit-01','flow-directional-response-01','flow-directional-information-01']
CACHE={}
def digest(p):
    p=Path(p)
    if p not in CACHE: CACHE[p]=f.sha(p)
    return CACHE[p]
def main():
    checks=0; experiments={}
    for name in NAMES:
        root=BASE/name; assert not (root/'INCOMPLETE').exists()
        validation=f.read(root/('validation-v3.json' if name=='flow-directional-information-01' else 'validation.json')); status=f.read(root/'STATUS.json'); assert validation['passed'] and status['stage']=='VALIDATED'
        record=f.read(root/'artifact_hashes.json'); record=record.get('files',record)
        for relative,expected in record.items():
            if isinstance(expected,str) and len(expected)==64: assert digest(root/relative)==expected,(name,relative); checks+=1
        for pattern in ['*freeze.json']:
            for freeze in root.glob(pattern):
                for path,expected in f.read(freeze).get('files',{}).items(): assert digest(path)==expected,(name,path); checks+=1
        experiments[name]=dict(stage=status['stage'],decision=validation.get('decision',status.get('decision')),validation_passed=True)
    heads={}
    for name,expected in [('RAP-main','4055d929c594b0033aafc6eed339c910369eef55'),('RAP-SLAM','6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6')]:
        path=f.MAIN.parent/name
        head=subprocess.check_output(['git','-c',f'safe.directory={path}','-C',str(path),'rev-parse','HEAD'],text=True).strip(); assert head==expected; heads[name]=head
    continuity={p.name:digest(p) for p in [f.MAIN/'AGENTS.md',f.MAIN/'docs/maintenance/README.md',BASE/'PHASE_RECORD.md',BASE/'MAINLINE_UPDATE.md']}
    f.save(BASE/'CONTINUATION_INTEGRITY_02.json',dict(passed=True,utc=f.now(),identity_checks=checks,unique_files_checked=len(CACHE),experiments=experiments,heads=heads,continuity_sha256=continuity,scope='artifact/source/freeze integrity and unchanged HEADs; no numeric recomputation'))
    print('final integrity passed',checks,'identities',len(CACHE),'unique files',flush=True)
if __name__=='__main__': main()
