#!/usr/bin/env python3
"""Validate release licenses, notices, and product package contents."""
import argparse
import io
from pathlib import Path, PurePosixPath
import zipfile

def archive(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names=z.namelist()
        assert len(names)==len(set(names)), 'Duplicate entries'
        assert z.testzip() is None, 'Archive CRC error'
        for info in z.infolist():
            n=info.orig_filename
            p=PurePosixPath(n)
            assert not p.is_absolute() and '..' not in p.parts and '\\' not in n and ':' not in n, 'Unsafe path'
        return {n:z.read(n) for n in names if not n.endswith('/')}

def validate(root, dist, version):
    license=(root/'LICENSE').read_bytes();notice=(root/'NOTICE.md').read_bytes()
    jars=list(dist.glob(f'*-v{version}.jar'))
    extensions=list(dist.glob(f'*extension-v{version}.zip'))
    fulls=[p for p in dist.glob(f'*-v{version}.zip') if p not in extensions]
    assert len(jars)==len(extensions)==len(fulls)==1, 'Expected three product packages'
    j,e,f=jars[0],extensions[0],fulls[0]
    jar=archive(j.read_bytes());ext=archive(e.read_bytes());full=archive(f.read_bytes())
    assert jar['META-INF/LICENSE']==license and jar['META-INF/NOTICE.md']==notice
    assert ext['LICENSE']==license and ext['NOTICE.md']==notice
    prefix=next(n[:-len('LICENSE')] for n in full if n.count('/')==1 and n.endswith('/LICENSE'))
    assert full[prefix+'LICENSE']==license and full[prefix+'NOTICE.md']==notice
    assert full[prefix+'plugin/'+j.name]==j.read_bytes()
    for n,b in ext.items():assert full[prefix+'extension/'+n]==b, 'Extension package mismatch: '+n
    for n in full:
        rel=n[len(prefix):]
        assert rel.startswith(('extension/','plugin/','docs/')) or rel in {'README.md','LICENSE','NOTICE.md','ACKNOWLEDGEMENTS.md','RELEASE_NOTES.md'}, 'Unexpected product path: '+rel
        if rel.endswith('.sh'):assert rel in {'plugin/install.sh','plugin/disable.sh'}, 'Unexpected executable'
    print('OK: licenses, notices, package boundaries and nested components')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('version');p.add_argument('--dist',type=Path)
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    validate(root,a.dist or root/'dist',a.version)
