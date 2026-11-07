"""Display sealed prepared arrays through existing poses; never fit/evaluate them."""
import hashlib, importlib.util, json, os, resource, sys, time
from pathlib import Path, PureWindowsPath
ROOT=Path(__file__).resolve().parent
SCOPE=ROOT.parent
OUT=Path(sys.argv[1]);CASE=sys.argv[2];START=time.monotonic()
SOURCE=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-24/real-interface-02/run01/real')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(name,obj):
    payload=json.dumps(obj,indent=2,allow_nan=False)
    with (OUT/name).open('x') as f:f.write(payload)
def audit(event,args):
    if event=='socket.connect':raise PermissionError('OV1 network forbidden')
    if event=='open' and args and isinstance(args[0],(str,bytes)):
        name=os.fsdecode(args[0])
        if name.endswith(('.ckpt','.pth')) or 'regx-interface-contract-01' in name or 'regx-reference-' in name:
            raise PermissionError('OV1 raw/reference/weights forbidden')
sys.addaudithook(audit)
ok=False;error=None
try:
    freeze=json.loads((OUT.parent/'SOURCE_FREEZE.json').read_text())
    assert sha(SCOPE/'INPUTS.json')==freeze['inputs_sha256']
    assert sha(SCOPE/'PROTOCOL.md')==freeze['protocol_sha256']
    bindings=json.loads((SCOPE/'INPUTS.json').read_text())
    allowed={PureWindowsPath(row['path']).name:row for row in bindings}
    for name,row in allowed.items():
        p=SOURCE/name;assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
    if CASE=='preflight':
        assert not any(n in sys.modules for n in ('numpy','matplotlib','torch'))
        assert importlib.util.find_spec('numpy') and importlib.util.find_spec('matplotlib')
        write('RESULTS.json',dict(passed=True,stdlib_only=True,inputs=len(allowed),
            matplotlib_available=True,interpreter_sha256=sha(Path(sys.executable).resolve()),python=sys.version))
    else:
        assert CASE=='plots'
        os.environ['MPLBACKEND']='Agg';os.environ['MPLCONFIGDIR']=str(OUT/'mpl-cache')
        import numpy as np
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        assert 'torch' not in sys.modules
        meta=json.loads((SOURCE/'RESULTS.json').read_text());assert meta['passed']
        colors=['#2563EB','#D55E00','#00876C'];records=[]
        plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':11,
            'axes.labelsize':9,'savefig.facecolor':'white','axes.facecolor':'#FAFBFD'})
        for capture in meta['captures']:
            case=capture['case'];assert case in ('case-000','case-001')
            spec=json.loads((SOURCE/(case+'_RAP_OUTPUT.json')).read_text())
            proof=json.loads((SOURCE/(case+'_RAP_SEAL.json')).read_text())
            assert sha(SOURCE/proof['file'])==proof['sha256']
            original=[];registered=[];display_ids=[]
            for i,(view,Tlist) in enumerate(zip(spec['prepared'],spec['T_parts'])):
                row=view['xyz'];assert row['file'] in allowed
                p=SOURCE/row['file'];assert sha(p)==row['sha256']
                x=np.load(p,allow_pickle=False)
                assert list(x.shape)==row['shape'] and str(x.dtype)==row['dtype']
                assert x.shape==(4000,3) and np.isfinite(x).all()
                T=np.asarray(Tlist,dtype=np.float64)
                assert T.shape==(4,4) and np.isfinite(T).all() and np.array_equal(T[3],[0,0,0,1])
                ids=np.linspace(0,len(x)-1,min(1500,len(x)),dtype=np.int64)
                xx=x[ids].astype(np.float64);yy=xx@T[:3,:3].T+T[:3,3]
                assert np.isfinite(yy).all()
                original.append(xx);registered.append(yy);display_ids.append(ids.tolist())
            assert len(original)==len(capture['counts'])
            groups=[original,registered];bounds=[]
            for values in groups:
                all_values=np.concatenate(values,axis=0)
                bounds.append((all_values.min(0),all_values.max(0)))
            span=max(float(np.max(hi-lo)) for lo,hi in bounds);assert span>0
            fig,axes=plt.subplots(2,3,figsize=(12,7.4),dpi=160)
            for r,values in enumerate(groups):
                center=(bounds[r][0]+bounds[r][1])/2
                for c,(a,b,name) in enumerate([(0,1,'XY'),(0,2,'XZ'),(1,2,'YZ')]):
                    ax=axes[r,c]
                    for i,v in enumerate(values):
                        ax.scatter(v[:,a],v[:,b],s=.9,alpha=.60,color=colors[i],linewidths=0,
                            rasterized=True,label=f'view {i:02d}')
                    ax.set_xlim(center[a]-.55*span,center[a]+.55*span)
                    ax.set_ylim(center[b]-.55*span,center[b]+.55*span)
                    ax.set_aspect('equal',adjustable='box');ax.grid(alpha=.16)
                    ax.set_xlabel('XYZ'[a]+' (input units)');ax.set_ylabel('XYZ'[b]+' (input units)')
                    ax.set_title(('Separate input frames' if r==0 else 'Estimated case-common frame')+' / '+name)
            handles,labels=axes[0,0].get_legend_handles_labels()
            fig.legend(handles,labels,loc='upper right',bbox_to_anchor=(.98,.985),ncol=len(original),markerscale=3)
            fig.suptitle(case+' | sealed public RAP outputs',x=.035,ha='left',y=.98,fontsize=16,fontweight='bold')
            fig.text(.035,.025,'1500 fixed rows/view from 4000 prepared rows; identical rows before/after. Same span in all six panels.\n'
                'Plot bounds recenter each row gauge. Input units and physical alignment are unverified; no GT/accuracy score.',fontsize=9,color='#455368')
            fig.subplots_adjust(top=.89,bottom=.15,left=.07,right=.98,hspace=.38,wspace=.27)
            name=case+'_geometry.png';assert not (OUT/name).exists()
            fig.savefig(OUT/name,dpi=160);plt.close(fig)
            records.append(dict(case=case,views=len(original),display_rows_per_view=1500,
                prepared_rows_per_view=4000,display_indices=display_ids,shared_axis_span=span,
                file=name,sha256=sha(OUT/name),separate_case_common_gauge=True))
        assert len(records)==2 and 'torch' not in sys.modules
        write('RESULTS.json',dict(passed=True,plots=records,numpy_version=np.__version__,
            matplotlib_version=matplotlib.__version__,python=sys.version,
            model_calls=0,new_pose_estimates=0,reference_reads=0,accuracy_metrics=0,
            physical_efficacy_claim=False,claim='Sealed-output geometric display only'))
    ok=True
except BaseException as caught:
    error=repr(caught)
    import traceback
    write('FAILURE.json',dict(error=error,traceback=traceback.format_exc()));raise
finally:
    write('worker_exit.json',dict(success=ok,error=error,elapsed_seconds=time.monotonic()-START,
        peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        sealed_public_output_visualization_only=True))
