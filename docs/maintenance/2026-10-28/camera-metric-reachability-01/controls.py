"""MR1 lexical categorical join of previously sealed rows only."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import baseline_lib as lib

OUT=lib.ROOT/'controls'
try:
    lib.verify_freeze('controls');binding=lib.load(lib.ROOT/'INPUT_BINDING.json')
    tables={}
    for name,item in binding.items():
        assert lib.sha(item['path'])==item['sha256'];data=lib.load(Path(item['path']))
        assert len(data)==200 and len({r['key'] for r in data})==200;tables[name]={r['key']:r for r in data}
    assert set(tables['PR1'])==set(tables['ER1'])==set(tables['VR1'])
    rows=[]
    for key,p in tables['PR1'].items():
        e=tables['ER1'][key];v=tables['VR1'][key];pose=p['status']=='POSE';epose=e['status']=='POSE'
        rows.append({'key':key,'sequence':p['sequence'],'stratum':p['stratum'],'historical_N_category':v['historical_N_category'],
            'historical_incorrect_accepted_overlay':v['historical_N_incorrect_accepted_overlay'],
            'PnP_pose':pose,'PnP_R5_t2':bool(pose and p['rotation_error_deg']<=5 and p['translation_error_m']<=2),
            'PnP_R5_d15':bool(pose and p['rotation_error_deg']<=5 and p['direction_error_deg'] is not None and p['direction_error_deg']<=15),
            'ER1_pose':epose,'ER1_R5_d15':v['visual_joint_5_15'],'source_depth_hypotheses':p['input_hypotheses']})
    def summary(data,name):
        return {'group':name,'pairs':len(data),'PnP_pose':sum(r['PnP_pose'] for r in data),
            'PnP_R5_t2':sum(r['PnP_R5_t2'] for r in data),'PnP_R5_d15':sum(r['PnP_R5_d15'] for r in data),
            'ER1_pose':sum(r['ER1_pose'] for r in data),'ER1_R5_d15':sum(r['ER1_R5_d15'] for r in data),
            'PnP_output_without_ER1_output':sum(r['PnP_pose'] and not r['ER1_pose'] for r in data),
            'PnP_direction_bin_without_ER1_bin':sum(r['PnP_R5_d15'] and not r['ER1_R5_d15'] for r in data),
            'both_direction_bins':sum(r['PnP_R5_d15'] and r['ER1_R5_d15'] for r in data)}
    groups=[summary(rows,'all200')]
    for seq in ('00','08'):
        data=[r for r in rows if r['sequence']==seq];assert len(data)==100
        groups.append(summary(data,seq+'/all100'))
        for category in ('correct_accepted','correct_rejected','selection_miss','proposal_unavailable','confuser'):
            groups.append(summary([r for r in data if r['historical_N_category']==category],seq+'/'+category))
        groups.append(summary([r for r in data if r['historical_incorrect_accepted_overlay']],seq+'/incorrect_accepted_overlay'))
        for stratum in sorted({r['stratum'] for r in data}):
            cell=[r for r in data if r['stratum']==stratum];assert len(cell)==25;groups.append(summary(cell,seq+'/stratum/'+stratum))
    lib.save(OUT/'ROWS.json',rows);lib.save(OUT/'SUMMARY.json',{'groups':groups,'role':'Post-hoc supplied-reference bin/ID intersections; no operational fusion or old metric equivalence'})
    lib.complete(OUT,{'complete_pairs':200,'groups':len(groups),'new_numeric_pose_or_error_calls':0})
    print('MR1 complete200 saved-output join')
except BaseException as error:
    lib.failure(OUT,error);raise
