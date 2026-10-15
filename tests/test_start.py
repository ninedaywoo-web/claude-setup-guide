import importlib.util, unittest, tempfile, json, hashlib, zipfile, io
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('start_update',Path(__file__).resolve().parents[1]/'scripts/update.py');u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
SHA='a'*40

def release():
    meta={'version':'1.0.20','repository':u.REPO}
    files={'version.json':json.dumps(meta),'SKILL.md':'新规则','references/01-network.md':'搬瓦工',
           'references/02-browser-iphone.md':'浏览器','references/05-ai-walkthrough.md':'带做'}
    manifest={'files':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in files.items()}}
    files['manifest.json']=json.dumps(manifest)
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w') as z:
        for k,v in files.items():z.writestr('repo/'+k,v)
    return meta,manifest,b.getvalue()

class StartTests(unittest.TestCase):
    def run_start(self,dest,source=None,heads=None,manifest_override=None,data_override=None):
        meta,manifest,data=release();heads=iter(heads or [SHA,SHA])
        def request(path,auth,binary=False):
            if path=='git/ref/heads/main':return {'object':{'sha':next(heads)}}
            self.assertTrue(path.startswith('zipball/'));self.assertTrue(binary)
            return data if data_override is None else data_override
        def file_json(name,commit,auth):return meta if name=='version.json' else (manifest if manifest_override is None else manifest_override)
        with patch.object(u,'request',side_effect=request),patch.object(u,'file_json',side_effect=file_json),patch.object(u,'cached_check',side_effect=AssertionError('must not use cache')):
            return u.start_latest(dest,progress_from=source)

    def test_fresh_download_ignores_old_cache_preserves_progress(self):
        with tempfile.TemporaryDirectory() as d:
            old=Path(d)/'old';(old/'.local').mkdir(parents=True)
            (old/'SKILL.md').write_text('旧正文');(old/'.local/progress.md').write_text('已完成网络')
            (old/'.local/update-check.json').write_text('旧缓存');(old/'.local/startup.json').write_text('旧收据')
            dest=Path(d)/'new';result=self.run_start(dest,old)
            self.assertEqual(result['status'],'ready');self.assertEqual(result['commit'],SHA)
            self.assertEqual((dest/'SKILL.md').read_text(),'新规则')
            self.assertEqual((dest/'.local/progress.md').read_text(),'已完成网络')
            self.assertFalse((dest/'.local/update-check.json').exists())
            self.assertEqual((old/'SKILL.md').read_text(),'旧正文')
            self.assertEqual(json.loads((dest/'.local/startup.json').read_text())['directory'],str(dest))

    def test_existing_directory_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(u,'request') as request,self.assertRaises(u.UpdateError):u.start_latest(d)
            request.assert_not_called()

    def test_version_label_cannot_hide_bad_content(self):
        with tempfile.TemporaryDirectory() as d:
            meta,manifest,data=release();b=io.BytesIO()
            with zipfile.ZipFile(io.BytesIO(data)) as src,zipfile.ZipFile(b,'w') as dst:
                for name in src.namelist():dst.writestr(name,'旧正文' if name.endswith('SKILL.md') else src.read(name))
            dest=Path(d)/'new'
            with self.assertRaises(u.UpdateError):self.run_start(dest,data_override=b.getvalue())
            self.assertFalse(dest.exists())

    def test_archive_manifest_must_match_pinned_remote(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'new'
            with self.assertRaises(u.UpdateError):self.run_start(dest,manifest_override={'files':{}})
            self.assertFalse(dest.exists())

    def test_head_moved_downloads_again(self):
        with tempfile.TemporaryDirectory() as d:
            result=self.run_start(Path(d)/'new',heads=[SHA,'b'*40,'b'*40,'b'*40])
            self.assertEqual(result['commit'],'b'*40)

    def test_repeated_head_movement_stops(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'new'
            with self.assertRaises(u.UpdateError):self.run_start(dest,heads=[SHA,'b'*40,SHA,'b'*40,SHA,'b'*40])
            self.assertFalse(dest.exists())

    def test_offline_cli_stops_without_old_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'new'
            with patch.object(u,'request',side_effect=OSError('offline')),patch('sys.argv',['update.py','start','--destination',str(dest)]),patch('sys.stdout',new_callable=io.StringIO) as out:
                self.assertEqual(u.main(),2)
                result=json.loads(out.getvalue());self.assertIn('暂停带做',result['message']);self.assertNotIn('继续使用本地教程',result['message'])
            self.assertFalse(dest.exists())

    def test_progress_symlink_refused(self):
        with tempfile.TemporaryDirectory() as d:
            old=Path(d)/'old';(old/'.local').mkdir(parents=True);(old/'.local/link').symlink_to('/tmp')
            with self.assertRaises(u.UpdateError):self.run_start(Path(d)/'new',old)

if __name__=='__main__':unittest.main()
