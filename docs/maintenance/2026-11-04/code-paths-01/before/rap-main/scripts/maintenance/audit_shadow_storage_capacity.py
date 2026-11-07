"""Read-only ZIP/header/byte accounting; no NumPy/model/reference metrics/packing."""
import hashlib,json,resource,time,zipfile
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'docs/maintenance/2026-10-13/shadow-conditioned-fit-pilot-01';BASE=ROOT/'docs/maintenance/2026-10-13/shadow-storage-capacity-review-01';START=time.monotonic();BASE.mkdir()
def sha(q):
    h=hashlib.sha256()
    with Path(q).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def save(name,value):(BASE/name).write_text(json.dumps(value,indent=2)+'\n')
seal=json.loads((SOURCE/'AVAILABLE_DELIVERY_SEAL.json').read_text());assert len(seal['files'])==576
compressed=Counter();raw=Counter();cases=Counter();directories=Counter();bindings={};steps=[]
for x in seal['files']:
    q=(SOURCE/x['path'].replace(chr(92),'/')).resolve();assert SOURCE.resolve() in q.parents and sha(q)==x['sha256'];bindings[str(q)]=x['sha256']
for q in SOURCE.rglob('*'):
    if q.is_file():directories[q.relative_to(SOURCE).parts[0]]+=q.stat().st_size
for q in (SOURCE/'predictions').iterdir():
    if q.is_dir():cases[q.name.split('_')[0]]+=1
for q in sorted((SOURCE/'predictions').glob('*/step_*.npz')):
    with zipfile.ZipFile(q) as z:
        rows=[dict(name=x.filename,compressed_bytes=x.compress_size,raw_member_bytes=x.file_size) for x in z.infolist()]
        for x in rows:compressed[x['name']]+=x['compressed_bytes'];raw[x['name']]+=x['raw_member_bytes']
    steps.append(dict(path=str(q),sha256=sha(q),members=rows))
assert len(steps)==185 and cases==Counter(U=17,V=17,P=3)
prefix_compressed=compressed['prefix.npy'];prefix_raw=raw['prefix.npy'];ratio=prefix_compressed/prefix_raw;prediction_bytes=directories['predictions'];cap=2147483648
estimated_full_prefix_compressed=prefix_compressed*255/185;approx_other_dossier=directories['fits']+directories['preflight'];approx_full_bytes=approx_other_dossier+prediction_bytes*51/37
save('CHECKS.json',dict(passed=True,scope='read-only identity and ZIP directory byte accounting; not a compression/numerical experiment',original_available_entries=576,all_available_hashes_match=True,files=bindings,step_archives=185,case_counts=dict(cases),directory_bytes=dict(directories),compressed_member_bytes=dict(compressed),raw_member_bytes=dict(raw),member_records=steps,
    actual_prefix_share_of_prediction_bytes=prefix_compressed/prediction_bytes,prefix_raw_with_NPY_headers=prefix_raw,prefix_compression_ratio=ratio,observed_prediction_prefix_compressed_bytes=prefix_compressed,raw_prefix_array_bytes_per_step=6144000,all51_raw_prefix_array_bytes=1566720000,
    extrapolated_full_prefix_compressed_bytes=estimated_full_prefix_compressed,rough_full_dossier_bytes=approx_full_bytes,original_cap_bytes=cap,extrapolation_not_a_complete_bank_bound=True,missing_P_files_not_synthesized=True,no_NumPy_neural_GT_metrics=True))
(BASE/'REPORT.md').write_text('\n'.join(['# Shadow artifact storage capacity review — read only','',f'All576 available HFIT0 delivery identities match.37 source-case directories(U17/V17/P3),185 step archives; no reference/GT/model/NumPy/packing execution.',
    '',f'Prefix members consume{prefix_compressed} compressed bytes of{prediction_bytes} prediction-directory bytes ({100*prefix_compressed/prediction_bytes:.4f}%). Their NPY raw member total is{prefix_raw}; ratio{ratio:.6f}. Fit directory{directories["fits"]}, preflight{directories["preflight"]} bytes. The failed study retains its original2GiB cap and INCOMPLETE; no files deleted or repacked.',
    '',f'At51x5 steps, raw prefix arrays alone require1,566,720,000 bytes. A uniform extrapolation of observed data gives roughly{approx_full_bytes:.0f} whole-dossier bytes, versus{cap} original cap. This is descriptive sizing, not a bound on unobserved P cases or evidence that a future corpus fits. Numeric fields include archive headers/metadata where stated.',
    '', 'Prospective lossless source-reference deduplication or bitwise XOR deltas may reduce paired prefix storage, but require their own encoder/decoder bit-identity/source/layout/budget validation on all available comparable arrays before any distinct future bank protocol. No codec/packing or scientific retry is executed here. Original failed cap/seals/partial files/negative decisions/physical unknowns remain; no gain, novelty or noise comparison conclusion.'])+'\n')
save('STATUS.json',dict(status='READ_ONLY_ARTIFACT_STORAGE_CAPACITY_REVIEW_COMPLETE',codec_created=False,codec_or_packing_executed=False,scientific_retry=False,HFIT0='INCOMPLETE_ARTIFACT_CAP',next='DESIGN_ONLY_LOSSLESS_REPRESENTATION'))
(BASE/'review_source.py').write_bytes(Path(__file__).read_bytes());save('BOOKKEEPING.json',dict(standard_library_only=True,wall_seconds_before_seal=time.monotonic()-START,RSS_observed_before_seal_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,no_numerical_scientific_replay=True))
files=[dict(path=str(q.relative_to(BASE)),sha256=sha(q),bytes=q.stat().st_size) for q in sorted(BASE.rglob('*')) if q.is_file()];save('DELIVERY_SEAL.json',dict(status='READ_ONLY_ARTIFACT_STORAGE_CAPACITY_REVIEW_COMPLETE',files=files,entries=len(files)))
print(json.dumps(dict(status='READ_ONLY_ARTIFACT_STORAGE_CAPACITY_REVIEW_COMPLETE',available_source_entries=576,step_archives=185,prefix_share_percent=100*prefix_compressed/prediction_bytes,rough_full_bytes=approx_full_bytes,review_deliveries=len(files)),indent=2))
