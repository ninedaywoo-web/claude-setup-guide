#!/usr/bin/env python3
"""Author-side: regenerate package checksums before publishing."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]
files={}
for p in sorted(root.rglob('*')):
 rel=p.relative_to(root)
 if any(x in {'.git','.local','__pycache__'} for x in rel.parts) or p.name in {'manifest.json','.DS_Store'} or p.suffix=='.pyc':continue
 if p.is_file():files[rel.as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(root/'manifest.json').write_text(json.dumps({'files':files},ensure_ascii=False,indent=2)+'\n')
print('Manifest:',len(files),'files')
