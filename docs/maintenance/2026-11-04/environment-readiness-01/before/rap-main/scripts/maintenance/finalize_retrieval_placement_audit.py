"""Package validated LC0 facts without changing any frozen scientific output."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json

MAIN=Path(__file__).resolve().parents[2]
BASE=MAIN/'docs/maintenance/2026-10-07/retrieval-placement-audit-01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,text):p.write_text(text,encoding='utf-8')
def now():return datetime.now(timezone.utc).isoformat()

def main():
    r=read(BASE/'results.json');v=read(BASE/'validation.json');b=read(BASE/'bank_validation.json');e=read(BASE/'bank/execution.json');f=read(BASE/'freeze.json')
    assert v['passed'] and b['passed'] and not (BASE/'INCOMPLETE').exists()
    decision=r['gate']['decision'];positive=decision!='NO_FIXED_BUDGET_PLACEMENT_SIGNAL'
    cov=read(BASE/'evaluation/coverage.json');sel=read(BASE/'evaluation/selection.json')
    wall=sum(x['wall_s'] for x in [f,e,b,r,v]);peak=max(x.get('peak_rss_bytes',0) for x in [f,e,b,r,v])
    lines=['# LC0 complete retrieval and measurement-placement opportunity audit','',
      f"Status: **{'VALIDATED_OPPORTUNITY' if positive else 'VALIDATED_NEGATIVE'}**; decision **{decision}**.",'',
      'Owner requested proceeding on2026-10-07. This is a fixed-budget, evaluator-only diagnostic on historically exposed E0 A data. No executable accuracy or originality gain follows.','',
      '## Source and validation','',
      f"Frozen{len(f['files'])} identities before outputs, including1800 raw keyframe scans matched to original E0 hashes. Native two-producer/merger replay and independent extraction reproduce all71 original attempts, including endpoint order and attempt IDs. All58 accepted edges/native weights remain; native graphs reproduce saved E0. All319728 eligible pair rows, ring ranks, filters, pre-cap/capped/final lists are complete.",'',
      f"Independent raw processing reconstructs1800 descriptors from {b['totals']['points']} retained points: all2160000 float32 descriptor pixels and36000 ring-key values exact. Independent SC scores maxdelta{b['max_score_delta']:.3e}, native graph maxdelta{b['max_graph_delta']:.3e}. The validator shares numeric bin/rounding conventions but uses sorted-bin maxima and simultaneous shift scoring; it imports no new algorithm/runner/native retrieval or graph.",'',
      'Complete GT-free bank seal and independent validation seal precede GT pose parsing. GT position-proxy coverage, selections, oracle transforms, explicit graphs and metrics reconstruct independently.',
      f"Independent oracle graph maxdelta{v['max_graph_delta']:.3e}; {v['independent_segment_records']} segment records; aggregate metric maxdelta{v['max_metric_delta']:.3e}. No failure/amendment/repair. All previous failures and stops remain untouched.",'',
      '## Exposure','',
      'GT-near below15m is a position proxy; it is not overlap or physical registration truth. Mixed-query counts are ambiguous exposure, not identified aliases. Complete denominators are in evaluation/coverage.json.','',
      '| Seq | Eligible near/all | Native union pre-cap near/all | Final near/all | Near queries eligible/union/final | Oracle C/P/H counts |',
      '| --- | ---: | ---: | ---: | ---: | ---: |']
    for s,c in cov.items():
        x,y,z=c['eligible'],c['union_precap'],c['final']
        lines.append(f"| {s} | {x['near_pairs']}/{x['pairs']} | {y['near_pairs']}/{y['pairs']} | {z['near_pairs']}/{z['pairs']} | {x['near_queries']}/{y['near_queries']}/{z['near_queries']} | {'/'.join(str(sel[s][a]['count']) for a in ['C','P','H'])} |")
    lines += ['', 'Counts are maximum12 per sequence, not increased neural work. Oracle counts may differ; P/H versus C includes measurement availability and placement, not a location-only equal-count causal effect. N uses original poses/weights; C/P/H use the same declared reference noise and GT-near filter. All oracle edges are evaluator-only.','',
      '## Trajectory opportunity','',
      'N=native, C=original shortlist with ideal GT-near measurements, P=distributed native pre-cap measurements, H=distributed structurally eligible measurements.','',
      '| Cohort | Arm | Mean ter % | Aligned ATE m | ter gain vs N pp | ATE gain vs N % |',
      '| --- | --- | ---: | ---: | ---: | ---: |']
    for g,m in r['cohort_means'].items():
        for a in ['N','C','P','H']:
            lines.append(f"| {g} | {a} | {m[a]['ter']:.6f} | {m[a]['ate']:.6f} | {m['N']['ter']-m[a]['ter']:+.6f} | {(1-m[a]['ate']/m['N']['ate'])*100:+.3f} |")
    lines += ['', '| Seq | N ter/ATE | C ter/ATE | P ter/ATE | H ter/ATE |','| --- | ---: | ---: | ---: | ---: |']
    for s,row in r['rows'].items():lines.append('| '+s+' | '+' | '.join(f"{row[a]['ter']:.6f}/{row[a]['ate']:.6f}" for a in ['N','C','P','H'])+' |')
    lines += ['', 'The frozen gate requires >=.01pp mean ter and>=5% aligned ATE gain together, improvement over C in both means, plus all-six safety (<=.01pp ter regression and<=5% ATE regression). Full component booleans are in results.json; no post-result selection/radius/noise/budget/cohort rescue.','']
    for a,t in r['gate']['tests'].items():
        lines.append(f"- {a} actionable={t['actionable']}; cohorts={json.dumps(t['cohorts'],sort_keys=True)}; failed safety={[(s,k) for s,d in t['safety'].items() for k,ok in d.items() if not ok]}")
    lines += ['', '## Meaning and limits','',
      'This completes the formerly missing native candidate exposure record. A near-query omission is conditional on the15m GT-position proxy, not a calibrated recall estimate for physical revisits. A selected oracle is neither a global bound nor guaranteed recoverable by any matcher;09 physical label/geometry discrepancy remains unresolved. Six sequences and their graph outcomes are previously exposed, not independent confirmation. Unknown RAP checkpoint training membership persists. Generic temporal distribution/retrieval controls are prior art; no RAP novelty is established.','',
      f"Successful freeze/bank/independent-bank/evaluation/independent-evaluation stages total{wall:.3f}s, peak RSS{peak/2**30:.3f}GiB. Per-stage1h/4GiB and500MiB artifact caps pass; no GPU/model inference. See EXECUTION_SUMMARY.json for stage costs and payload size.",'',
      '## Continuation','',
      'Read NEXT_ROUND_PLAN.md and HANDOFF.md. All earlier stopped arms, sealed banks, official GT/metrics, manuscript pause and original breakthrough requirement persist. No training, production/default/model/manuscript edit, acquisition/install, commit or Git sync. Original HEADs/branches and dirty work preserved.','']
    write(BASE/'REPORT.md','\n'.join(lines))
    payload=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
    status=dict(stage='LC0',status='VALIDATED_OPPORTUNITY' if positive else 'VALIDATED_NEGATIVE',decision=decision,frozen_identities=len(f['files']),keyframe_scans=1800,eligible_pairs=319728,native_attempts_reproduced=71,native_accepted_edges=58,gt_free_validation_before_evaluation=True,independent_segment_records=v['independent_segment_records'],failure_or_repair=False,training=False,inference=False,production_edit=False,manuscript_edit=False,git_sync=False)
    write(BASE/'STATUS.json',json.dumps(status,indent=2)+'\n')
    execution=dict(utc=now(),stages={k:dict(wall_s=x['wall_s'],peak_rss_bytes=x.get('peak_rss_bytes')) for k,x in zip(['freeze','bank','bank_validation','evaluation','evaluation_validation'],[f,e,b,r,v])},total_wall_s=wall,peak_rss_bytes=peak,artifact_bytes=payload,per_stage_cpu_cap_s=3600,rss_cap_bytes=4*2**30,artifact_cap_bytes=500*2**20)
    assert payload<=500*2**20 and all(x['wall_s']<=3600 for x in [f,e,b,r,v]) and peak<=4*2**30
    write(BASE/'EXECUTION_SUMMARY.json',json.dumps(execution,indent=2)+'\n')
    print(decision,'packaged',wall,'s',payload,'bytes')

if __name__=='__main__':main()
