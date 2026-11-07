"""Independent PNG structure/CRC checks for every admitted right observation."""
import sys,struct,zlib,binascii
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
out=Path(sys.argv[1]);manifest_path=ROOT/'packet/RIGHT_IMAGE_MANIFEST.json'
manifest=read(manifest_path)
paths=[manifest_path]+[r['path'] for r in manifest['rows']]
gate(paths,out);lease(out,True)
chunk_count=0;pixel_counts=0;unique=set()
for row in manifest['rows']:
    lease(out)
    data=Path(row['path']).read_bytes()
    assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
    assert binascii.crc32(data)&0xffffffff==int(row['CRC32'],16)
    pos=8;idat=[];seen_ihdr=False;seen_iend=False
    while pos<len(data):
        size=struct.unpack_from('>I',data,pos)[0];kind=data[pos+4:pos+8]
        payload=data[pos+8:pos+8+size];crc=struct.unpack_from('>I',data,pos+8+size)[0]
        assert binascii.crc32(kind+payload)&0xffffffff==crc
        chunk_count+=1
        if kind==b'IHDR':
            assert not seen_ihdr and size==13;seen_ihdr=True
            width,height,bitdepth,colortype,compression,filtering,interlace=struct.unpack('>IIBBBBB',payload)
            assert (width,height,bitdepth,colortype,compression,filtering,interlace)==(row['width'],row['height'],8,0,0,0,0)
        elif kind==b'IDAT':idat.append(payload)
        elif kind==b'IEND':seen_iend=True
        pos+=12+size
    assert pos==len(data) and seen_ihdr and seen_iend
    unfiltered=zlib.decompress(b''.join(idat))
    assert len(unfiltered)==(width+1)*height
    assert all(unfiltered[y*(width+1)]<=4 for y in range(height))
    pixel_counts+=width*height;unique.add((row['sequence'],row['frame']))
assert len(unique)==273
complete(out,independent_PNGs=273,PNG_chunks_checked=chunk_count,pixels_declared=pixel_counts,all_member_byte_hashes_and_CRCs_pass=True,PNG_scanline_structure_checked=True,independent_pixel_reconstruction=False,new_depth_or_pose_calls=0)
