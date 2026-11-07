"""CV1 implementation-only retry; original51entryfreeze/failure/INCOMPLETE retained."""
import argparse
import importlib.metadata
import json
import shutil
from pathlib import Path
import cross_visit_map_pilot as run
import cross_visit_map_attempt02 as repaired

ORIGINAL = run.BASE
run.BASE = ORIGINAL/'attempt-02'
run.alg = repaired


def freeze():
    original = run.read(ORIGINAL/'freeze.json')
    for path, digest in original['files'].items():
        assert run.sha(path) == digest
    run.previous.check_delivery(run.previous.BASE)
    sources = [Path(__file__), Path(__file__).with_name('validate_cross_visit_map_pilot_attempt02.py'),
               run.BASE/'algorithm_staging.py', run.old.SLAM/'scripts/cross_visit_map_attempt02.py', ORIGINAL/'AMENDMENT_01.md']
    assert run.sha(sources[2]) == run.sha(sources[3])
    snapshot = run.BASE/'source_snapshot'
    snapshot.mkdir()
    files = list(map(Path, original['files']))+sources
    for i, source in enumerate(sources):
        target = snapshot/f'{i:02d}-{source.name}'
        shutil.copyfile(source,target)
        files.append(target)
    files += [ORIGINAL/name for name in ('freeze.json','FAILURE_preflight.json','PREFLIGHT_DIAGNOSIS.json','preflight_diagnosis.py','RESOURCE_LOG.json','INCOMPLETE')]
    run.save(run.BASE/'freeze.json', dict(utc=run.utc(), files={str(p):run.sha(p) for p in files}, binding=original['binding'],
             packages={p:importlib.metadata.version(p) for p in ('numpy','scipy')},
             original_freeze_sha256=run.sha(ORIGINAL/'freeze.json'), implementation_only_repair=True,
             new_raw_coordinates_parsed=False,new_numeric_gt_parsed=False,
             exposed_development=True,new_cpu_wall_cap_s=1800,rss_cap_bytes=2*2**30,artifact_cap_bytes=512*2**20))
    (run.BASE/'INCOMPLETE').write_text('CV1 retry requires complete preflight/bank/decision validation\n')
    print('CV1 retry frozen',len(set(files)),'entries',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage',choices=('freeze','preflight','bank','evaluate'))
    stage = parser.parse_args().stage
    if stage == 'freeze':
        assert not (run.BASE/'RESOURCE_LOG.json').exists()
        (run.BASE/'RESOURCE_LOG.json').write_text(json.dumps(run.read(ORIGINAL/'RESOURCE_LOG.json'),indent=2)+'\n')
    run.record_stage(stage, freeze if stage == 'freeze' else getattr(run,stage))
