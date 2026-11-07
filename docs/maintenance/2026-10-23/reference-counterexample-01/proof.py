"""Exact invented translation counterexample, with no data or transform fitting."""
from fractions import Fraction as F
import json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;START=time.monotonic()
physical=((0,0,0),(1,0,0),(0,2,0),(0,0,3))
offsets=((0,0,0),(5,0,0),(0,7,0))
augmentation=((2,-1,3),(-4,2,1),(1,6,-2))
def add(a,b):return tuple(F(x)+F(y) for x,y in zip(a,b))
def sub(a,b):return tuple(F(x)-F(y) for x,y in zip(a,b))
def norm2(a):return sum(x*x for x in a)
def show(a):return [str(x) for x in a]
world=[[add(p,d) for p in physical] for d in offsets]
inputs=[[add(p,a) for p in w] for w,a in zip(world,augmentation)]
labels=[tuple(-F(x) for x in a) for a in augmentation]
for i in range(3):assert [add(p,labels[i]) for p in inputs[i]]==world[i]
rows=[]
for reference in range(3):
    for source in range(3):
        # T_i is the published inverse augmentation: augmented view -> purported world.
        published_relative=sub(labels[source],labels[reference])
        independently_required=add(published_relative,sub(offsets[reference],offsets[source]))
        error=sub(published_relative,independently_required)
        assert norm2(error)==norm2(sub(offsets[source],offsets[reference]))
        for p_source,p_reference in zip(inputs[source],inputs[reference]):assert add(p_source,independently_required)==p_reference
        rows.append(dict(reference=reference,source=source,label_oracle_transform_error_squared='0',
            inverse_augmentation_consistency_exact=True,independent_physical_relative_translation=show(independently_required),
            published_relative_translation=show(published_relative),physical_correspondence_error_squared=str(norm2(error))))
assert {r['physical_correspondence_error_squared'] for r in rows}=={'0','25','49','74'}
result=dict(kind='INVENTED_MATHEMATICAL_COUNTEREXAMPLE_ONLY',published_inverse_labels_consistent=True,
    label_copying_oracle_is_not_an_admissible_predictor=True,physical_correspondences_stipulated_independently=True,
    all_ordered_pairs=rows,actual_author_data_correctness_assessed=False,actual_file_or_model_reads=0,
    claim='Inverse-augmentation self-consistency is insufficient to authenticate physical registration truth',
    elapsed_seconds=time.monotonic()-START)
with (ROOT/'RESULTS.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(pairs=len(rows),exact_synthetic_squared_errors=['0','25','49','74'],actual_data_reads=0)))
