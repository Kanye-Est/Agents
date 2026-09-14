#!/usr/bin/env python3
from pathlib import Path
import argparse,json,hashlib,tarfile,shutil,datetime
parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--label',required=True);parser.add_argument('--include',action='append',required=True)
a=parser.parse_args();root=Path(a.root).resolve();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
assert a.label and all(c.isalnum() or c in '-_' for c in a.label)
snapshot=root/'archives'/('.snapshot-'+a.label+'-'+stamp);snapshot.mkdir()
items=list(dict.fromkeys(a.include+['rig_context.env','rig_helpers.sh','archive_phase.py']))
for item in items:
    src=(root/item).resolve();assert src.is_relative_to(root) and src!=root and not src.is_relative_to(root/'archives')
    dst=snapshot/item;dst.parent.mkdir(parents=True,exist_ok=True)
    if src.is_dir():shutil.copytree(src,dst)
    else:shutil.copyfile(src,dst)
lines=[]
for f in sorted(snapshot.rglob('*')):
    if f.is_file():
        with f.open('rb') as fp:h=hashlib.file_digest(fp,'sha256').hexdigest()
        lines.append(h+'  '+f.relative_to(snapshot).as_posix())
(snapshot/'evidence.sha256').write_text('\n'.join(lines)+'\n')
archive=root/'archives'/(a.label+'-'+stamp+'.tar.gz')
with tarfile.open(archive,'w:gz') as t:t.add(snapshot,arcname=a.label)
with archive.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
Path(str(archive)+'.sha256').write_text(digest+'  '+str(archive)+'\n')
with tarfile.open(archive,'r:gz') as t:count=sum(m.isfile() for m in t.getmembers())
record={'run':0,'label':a.label,'archive':str(archive),'sha256':digest,'bytes':archive.stat().st_size,'files':count,'included':items}
(root/'archives'/(a.label+'-'+stamp+'.json')).write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
