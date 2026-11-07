"""Uninstalled cooperating reader for the eight fixed public XYZ64 files."""
from dataclasses import dataclass
import hashlib,json,math,os,re,stat,struct
from pathlib import Path,PurePosixPath
CASE_PATHS=['case-000/manifest.json','case-001/manifest.json']
FILES={'INDEX.json',*CASE_PATHS,'case-000/v00.xyz64','case-000/v01.xyz64','case-001/v00.xyz64','case-001/v01.xyz64','case-001/v02.xyz64'}
@dataclass(frozen=True)
class PublicView:
    view_id:str
    xyz:tuple
@dataclass(frozen=True)
class PublicCase:
    case_id:str
    views:tuple
def reject(message):raise ValueError(message)
def json_object(raw):
    def pairs(items):
        out={}
        for key,value in items:
            if key in out:reject('duplicate_json_key')
            out[key]=value
        return out
    def constant(value):reject('nonstandard_json_constant')
    return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)
def manifest(m):
    if not isinstance(m,dict) or set(m)!={'version','format','view_count','views'}:reject('manifest_keys')
    if type(m['version'])is not int or m['version']!=1 or m['format']!='xyz-f64le-v1':reject('manifest_version_format')
    if type(m['view_count'])is not int or m['view_count'] not in (2,3) or not isinstance(m['views'],list) or len(m['views'])!=m['view_count']:reject('view_count')
    for i,v in enumerate(m['views']):
        if not isinstance(v,dict) or set(v)!={'id','file','points','bytes','SHA256'}:reject('view_keys')
        if v['id']!=f'v{i:02d}' or v['file']!=f'v{i:02d}.xyz64':reject('view_path_or_order')
        if type(v['points'])is not int or not 0<v['points']<1000000 or type(v['bytes'])is not int or v['bytes']!=v['points']*24:reject('point_count_or_bytes')
        if not isinstance(v['SHA256'],str) or not re.fullmatch('[0-9a-f]{64}',v['SHA256']):reject('manifest_hash')
    return m
def ordinary(st,folder=False):
    if getattr(st,'st_file_attributes',0)&0x400 or stat.S_ISLNK(st.st_mode):reject('reparse_or_symlink')
    if not (stat.S_ISDIR(st.st_mode) if folder else stat.S_ISREG(st.st_mode)):reject('nonregular_input')
def catalog_check(catalog):
    if not isinstance(catalog,dict) or set(catalog)!=FILES:reject('catalog_paths')
    for row in catalog.values():
        if not isinstance(row,dict) or set(row)!={'bytes','sha256'} or type(row['bytes'])is not int or not 0<row['bytes']<32*2**20 or not isinstance(row['sha256'],str) or not re.fullmatch('[0-9A-Fa-f]{64}',row['sha256']):reject('catalog_identity')
def load(root,catalog):
    catalog_check(catalog);root=Path(root).absolute();access=[]
    for p in (root,*root.parents):ordinary(p.lstat(),folder=True)
    def read(relative):
        if relative not in FILES:reject('unapproved_read_path')
        parts=PurePosixPath(relative).parts
        if any(p in ('..','.') for p in parts):reject('relative_path')
        p=root.joinpath(*parts)
        for parent in p.parents:
            if parent==root:break
            ordinary(parent.lstat(),folder=True)
        before=p.lstat();ordinary(before)
        expected=catalog[relative]
        if before.st_size!=expected['bytes']:reject('pinned_size')
        with p.open('rb') as f:
            opened=os.fstat(f.fileno());ordinary(opened)
            if (opened.st_dev,opened.st_ino,opened.st_size)!=(before.st_dev,before.st_ino,before.st_size):reject('opened_identity_changed')
            raw=f.read(expected['bytes']+1)
        after=p.lstat();ordinary(after)
        if (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)!=(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns):reject('file_changed_during_read')
        if len(raw)!=expected['bytes'] or hashlib.sha256(raw).hexdigest().upper()!=expected['sha256'].upper():reject('pinned_bytes_or_hash')
        access.append(relative);return raw
    index=json_object(read('INDEX.json'))
    if not isinstance(index,dict) or set(index)!={'version','cases'} or type(index['version'])is not int or index['version']!=1 or index['cases']!=CASE_PATHS:reject('index_schema_or_order')
    cases=[];counts=[]
    for n,relative in enumerate(index['cases']):
        m=manifest(json_object(read(relative)))
        if m['view_count']!=n+2:reject('pinned_view_count')
        views=[]
        for row in m['views']:
            name=str(PurePosixPath(relative).parent/row['file']);raw=read(name)
            if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['SHA256']:reject('view_bytes_or_hash')
            points=tuple(struct.iter_unpack('<ddd',raw))
            if len(points)!=row['points'] or not all(math.isfinite(v) for p in points for v in p):reject('nonfinite_or_count')
            views.append(PublicView(row['id'],points))
        cases.append(PublicCase(PurePosixPath(relative).parent.name,tuple(views)));counts.append(sum(len(v.xyz) for v in views))
    return tuple(cases),dict(public_access=access,point_occurrences=sum(counts),case_point_counts=counts,private_reads_requested=False,cooperating_interface_only=True)
