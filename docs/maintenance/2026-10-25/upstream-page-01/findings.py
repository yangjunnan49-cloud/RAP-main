"""Bind narrow claims to this one captured page; no link traversal."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
lines=(root/'PAGE_TEXT.txt').read_text(encoding='utf-8').splitlines()
def claim(token,needle):
    found=[(i+1,s) for i,s in enumerate(lines) if needle in s]
    assert len(found)==1,(token,found)
    return dict(claim=token,text_line=found[0][0],literal=found[0][1])
rows=[claim('published_task_role','dataset specifically designed'),
      claim('details_deferred_to_readme','All details about the dataset'),
      claim('creation_details_deferred','more details about the creation'),
      claim('creation_paper_identifier','eid = {arXiv:2310.16542}')]
links=json.loads((root/'PAGE_LINKS.json').read_text(encoding='utf-8'))['links']
readme=[r for r in links if 'readme' in r['resolved_URL'].lower()]
assert readme==[]
for name in ('000.ply','001.ply','002.ply','paris_02'):
    assert name not in '\n'.join(lines)
value=dict(passed=True,scope='One complete captured main-HTML text snapshot only',
    body_sha256='B8A828DD1DCFD039A565E191EFE19DE79389C02F8812413017DD3BE0B5034A59',
    text_sha256=hashlib.sha256((root/'PAGE_TEXT.txt').read_bytes()).hexdigest().upper(),
    supported_claims=rows,direct_readme_anchor_found=False,
    exact_RegX_member_names_present_in_extracted_text=False,
    upstream_page_role_description_obtained=True,
    exact_RegX_to_upstream_crosswalk_authenticated=False,
    registration_pose_frame_units_timing_quality_authenticated=False,
    independent_confirmation_cohort_admitted=False,checkpoint_training_exclusion_authenticated=False,
    physical_efficacy_admitted=False,linked_content_or_media_assessed=False,
    broader_site_or_dataset_absence_not_claimed=True,new_model_or_numeric_reference_calls=0,
    research='UNRESOLVED',manuscript='PAUSED')
with (root/'SOURCE_FINDINGS.json').open('x',encoding='utf-8') as f:json.dump(value,f,indent=2)
print(json.dumps(dict(passed=True,source_claims=len(rows),links_followed=0,physical_efficacy_admitted=False)))
