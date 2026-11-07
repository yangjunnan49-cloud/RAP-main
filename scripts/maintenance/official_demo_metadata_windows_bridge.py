"""MDA0 Windows transport and route-only validator, under original outer caps."""
import ast
import json
import subprocess
import sys
from pathlib import Path
import types
import official_demo_metadata as p


def main(stage):
    binding=p.read(p.BASE/'WINDOWS_BINDING.json')
    for name,row in binding['files'].items():assert p.sha(Path(name))==row['sha256'] and Path(name).stat().st_size==row['bytes']
    if stage=='prepare':raise ValueError('Preparation is separate')
    if stage=='windows':
        def execute():
            p.verify()
            code=subprocess.run(['/mnt/c/Program Files/PowerShell/7/pwsh.exe','-NoLogo','-NoProfile','-NonInteractive','-File',
                'E:\\githouse\\RAP-main\\scripts\\maintenance\\official_demo_metadata_windows_control.ps1'],check=False).returncode
            assert code==0
            p.verify()
        spent=sum(p.read(q)['wall_seconds'] for q in p.SUP.glob('*/exit.json'));assert spent<900
        import signal
        signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('MDA0 aggregate cap')))
        signal.alarm(max(1,int(900-spent)));ok=False;error=None
        try:
            execute();u=p.usage()
            assert u['peak_RSS_bytes']<=128*2**20 and u['artifact_bytes']<16*2**20
            assert u['acquired_network_body_bytes']<=p.CAP
            assert p.read(p.SUP/'host_latest.json')['headroom_bytes']>=4*2**30
            ok=True
        except BaseException as ex:
            error=repr(ex);p.save('FAILURE_windows.json',dict(error=error,**p.usage()));raise
        finally:
            signal.alarm(0);p.save('supervision/windows/child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**p.usage()))
    elif stage=='validate':
        source=(p.ROOT/'scripts/maintenance/validate_official_demo_metadata.py').read_text();tree=ast.parse(source);changes=0
        for n in ast.walk(tree):
            if isinstance(n,ast.Constant) and n.value=='catalog.json':n.value='catalog_windows.json';changes+=1
        assert changes==1;ast.fix_missing_locations(tree)
        module=types.ModuleType('validate_official_demo_metadata');exec(compile(tree,'<MDA0 exact catalog-route variant>','exec'),module.__dict__)
        sys.modules['validate_official_demo_metadata']=module;p.run('validate')
    else:raise ValueError(stage)


if __name__=='__main__':main(sys.argv[1])
