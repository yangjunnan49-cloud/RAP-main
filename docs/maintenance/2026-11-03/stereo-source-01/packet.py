"""Read exactly the new right-camera observations after successful API controls."""
import sys, struct, zlib
from pathlib import Path, PurePosixPath
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
out=Path(sys.argv[1])
calibs=[f'E:/githouse/Datasets/data_odometry_velodyne/dataset/sequences/{s}/calib.txt' for s in ('00','08')]
results_path=str(Path(METHOD['archive_admission']).parent/'RESULTS.json')
gate([METHOD['archive'],METHOD['archive_admission'],METHOD['image_manifest'],results_path,*calibs],out)
lease(out,True)
admission=read(METHOD['archive_admission']);old=read(results_path);images=read(METHOD['image_manifest'])['rows']
stat=Path(METHOD['archive']).stat()
assert stat.st_size==admission['archive_bytes']==old['archive_bytes'] and stat.st_mtime_ns==old['archive_mtime_ns']
requested={row['member'].replace('/image_0/','/image_1/'):row for row in images}
assert len(images)==len(requested)==273
rows=[];total=0;rawdir=out/'right';rawdir.mkdir()
with zipfile.ZipFile(METHOD['archive']) as archive:
    entries=archive.infolist();names=[e.filename for e in entries]
    assert len(entries)==old['index_entries'] and len(names)==len(set(names))
    assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n for n in names)
    indexed=set(names);assert set(requested)<=indexed
    for member,prior in sorted(requested.items()):
        lease(out)
        entry=archive.getinfo(member)
        assert 0<entry.file_size<=METHOD['max_image_bytes']
        data=archive.read(member)  # ZipFile checks the complete member CRC.
        assert len(data)==entry.file_size and (zlib.crc32(data)&0xffffffff)==entry.CRC
        assert data[:8]==b'\x89PNG\r\n\x1a\n'
        width,height=struct.unpack('>II',data[16:24])
        assert width==prior['width'] and height==prior['height']
        decoded=cv2.imdecode(np.frombuffer(data,dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
        assert decoded is not None and decoded.shape==(height,width) and decoded.dtype==np.uint8
        dest=rawdir/(prior['sequence']+'_'+Path(member).name)
        with dest.open('xb') as f:f.write(data)
        total+=len(data);assert total<=METHOD['max_packet_bytes']
        rows.append(dict(member=member,sequence=prior['sequence'],frame=int(Path(member).stem),path=str(dest),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),CRC32=f'{entry.CRC:08x}',width=width,height=height,left_image_identity=prior,fully_decoded=True))
after=Path(METHOD['archive']).stat();assert (stat.st_size,stat.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
calibration=[]
for path in calibs:
    lease(out)
    fields={}
    for line in Path(path).read_text().splitlines():
        key,values=line.split(':',1);fields[key]=[float(v) for v in values.split()]
    p0=np.array(fields['P0']).reshape(3,4);p1=np.array(fields['P1']).reshape(3,4)
    assert np.max(abs(p0[:,:3]-p1[:,:3]))<1e-8
    assert p0[0,0]>0 and np.max(abs(p0[:,3]))<1e-8
    assert abs(p1[1,3])<1e-8 and abs(p1[2,3])<1e-8
    baseline=-p1[0,3]/p1[0,0];assert 0<baseline<1
    point=np.array([1.2,-.4,9.,1.]);a=p0@point;b=p1@point
    disparity=a[0]/a[2]-b[0]/b[2]
    scalar_depth=float(-p1[0,3]/disparity)
    assert abs(scalar_depth-point[2])<1e-12
    calibration.append(dict(path=path,sha256=sha(path),sequence=Path(path).parent.name,P0=fields['P0'],P1=fields['P1'],Tr=fields['Tr'],baseline_m=float(baseline),scalar_projection_depth=scalar_depth,physical_version_authenticated=False))
save(out/'RIGHT_IMAGE_MANIFEST.json',dict(rows=rows,calibration=calibration,total_bytes=total,archive_stat_unchanged=True,current_whole_archive_sha_checked=False))
complete(out,requested_members=273,exact_members_found=273,new_right_images_decoded=273,total_right_bytes=total,archive_stat_unchanged=True,central_directory_entries=len(entries),calibration_baselines_m=[c['baseline_m'] for c in calibration],features_extracted=0,depth_maps=0,new_poses=0)
