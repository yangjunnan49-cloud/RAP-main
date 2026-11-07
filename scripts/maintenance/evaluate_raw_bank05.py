import sys,inspect
import raw_input_system05 as d
d.verify()
for p,h in d.read(d.BASE/'EVAL05_ROUTE_FREEZE.json')['files'].items():assert d.sha(p)==h,p
original=inspect.getsource(d.evaluate)
source=original.replace("BASE/'bank04'","BASE/'bank05'")
assert original.count("BASE/'bank04'")==5
exec(compile(source,__file__,'exec'),d.__dict__)
assert sys.argv[1]=='evaluate05'
d.run('evaluate05',False)
