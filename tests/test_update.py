import importlib.util,unittest,tempfile,json,hashlib,zipfile,io
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('update',Path(__file__).resolve().parents[1]/'scripts/update.py');u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
def package(p,text):
 p.mkdir(exist_ok=True);(p/'SKILL.md').write_text(text)
 (p/'version.json').write_text(json.dumps({'version':text,'repository':u.REPO}))
 (p/'manifest.json').write_text(json.dumps({'files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in p.iterdir() if f.name!='manifest.json'}}))
class UpdateTests(unittest.TestCase):
 def test_check_new_and_same(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);package(p,'1.0.0')
   with patch.object(u,'request',return_value={'object':{'sha':'a'*40}}),patch.object(u,'file_json',return_value={'version':'1.1.0','summary':['新增']}):
    self.assertEqual(u.check(p,None)['status'],'update_available')
   with patch.object(u,'request',return_value={'object':{'sha':'a'*40}}),patch.object(u,'file_json',return_value={'version':'1.0.0'}):
    self.assertEqual(u.check(p,None,force=True)['status'],'current')
 def test_version_order_and_no_downgrade(self):
  for local,remote,status in [('1.0.9','1.0.10','update_available'),('1.0.10','1.0.9','local_ahead'),('1.0.9','1.0.9','current')]:
   with self.subTest(local=local,remote=remote):
    result=u.version_result(local,{'version':remote},'a'*40)
    self.assertEqual(result['status'],status)
    if status=='update_available':
     self.assertEqual(result['update_notice'],'已有最新更新（v1.0.10），建议更新。')
     self.assertTrue(result['apply_command'].endswith('a'*40))
    else:
     self.assertIsNone(result['update_notice']);self.assertIsNone(result['apply_command'])
 def test_cache_reused_until_24_hours_then_refreshed(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);package(p,'1.0.0')
   with patch.object(u,'request',return_value={'object':{'sha':'a'*40}}) as request,patch.object(u,'file_json',return_value={'version':'1.1.0','summary':['新增']}):
    fresh=u.check(p,None,now=100000)
    cached=u.check(p,None,now=100000+u.CHECK_INTERVAL-1)
    self.assertFalse(fresh['cached']);self.assertTrue(cached['cached'])
    self.assertEqual(request.call_count,1)
    self.assertEqual(cached['update_notice'],fresh['update_notice'])
    self.assertEqual(cached['checked_at'],fresh['checked_at'])
    expired=u.check(p,None,now=100000+u.CHECK_INTERVAL)
    self.assertFalse(expired['cached']);self.assertEqual(request.call_count,2)
 def test_force_refresh_and_rebuild_cached_command(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);package(p,'1.0.0')
   with patch.object(u,'request',return_value={'object':{'sha':'a'*40}}) as request,patch.object(u,'file_json',return_value={'version':'1.1.0'}):
    u.check(p,None,now=100000)
    record=json.loads((p/u.CACHE_PATH).read_text())
    record['result']['apply_command']='do not execute this cached command'
    record['result']['update_notice']='untrusted cached notice'
    (p/u.CACHE_PATH).write_text(json.dumps(record))
    cached=u.check(p,None,now=100001)
    self.assertEqual(cached['apply_command'],'python3 scripts/update.py apply --commit '+'a'*40)
    self.assertEqual(cached['update_notice'],'已有最新更新（v1.1.0），建议更新。')
    self.assertEqual(request.call_count,1)
    self.assertFalse(u.check(p,None,force=True,now=100002)['cached'])
    self.assertEqual(request.call_count,2)
 def test_failed_check_cached_without_false_current_or_secret(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);package(p,'1.0.0')
   with patch.object(u,'request',side_effect=OSError('private-error-details')) as request:
    fresh=u.check(p,None,now=100000)
    cached=u.check(p,None,now=100001)
    self.assertEqual(fresh['status'],'unavailable');self.assertEqual(cached['status'],'unavailable')
    self.assertTrue(cached['cached']);self.assertEqual(request.call_count,1)
    self.assertIsNone(cached['update_notice']);self.assertIsNone(cached['apply_command'])
    self.assertNotIn('private-error-details',json.dumps(fresh))
    self.assertIn('--force',fresh['message'])
    u.check(p,None,force=True,now=100002);self.assertEqual(request.call_count,2)
 def test_invalid_cache_refetched(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);package(p,'1.0.0')
   with patch.object(u,'request',return_value={'object':{'sha':'a'*40}}),patch.object(u,'file_json',return_value={'version':'1.1.0'}):
    u.check(p,None,now=100000)
   original=json.loads((p/u.CACHE_PATH).read_text())
   invalid=[]
   for key,value in [('repository','wrong/repo'),('schema',999),('checked_at',100002),('checked_at',float('nan'))]:
    record=json.loads(json.dumps(original));record[key]=value;invalid.append(json.dumps(record))
   record=json.loads(json.dumps(original));record['result']['commit']='not-a-commit';invalid.append(json.dumps(record))
   invalid.append('invalid json')
   for value in invalid:
    with self.subTest(cache=value):
     (p/u.CACHE_PATH).write_text(value)
     with patch.object(u,'request',return_value={'object':{'sha':'b'*40}}) as request,patch.object(u,'file_json',return_value={'version':'1.2.0'}):
      result=u.check(p,None,now=100001)
      self.assertFalse(result['cached']);self.assertEqual(request.call_count,1)
      self.assertEqual(result['remote_version'],'1.2.0')
 def test_update_preserves_progress_and_invalidates_old_cache(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'old';q=Path(d)/'new';package(p,'1.0.0');package(q,'1.1.0')
   with patch.object(u,'request',return_value={'object':{'sha':'a'*40}}),patch.object(u,'file_json',return_value={'version':'1.1.0'}):
    u.check(p,None,now=100000)
   (p/'.local/progress.md').write_text('进度')
   u.replace_package(p,q)
   with patch.object(u,'request',return_value={'object':{'sha':'a'*40}}) as request,patch.object(u,'file_json',return_value={'version':'1.1.0'}):
    result=u.check(p,None,now=100001)
    self.assertFalse(result['cached']);self.assertEqual(result['status'],'current')
    self.assertIsNone(result['update_notice']);self.assertEqual(request.call_count,1)
   self.assertEqual((p/'.local/progress.md').read_text(),'进度')
 def test_cache_write_failure_does_not_hide_network_result(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);package(p,'1.0.0')
   with patch.object(u,'request',return_value={'object':{'sha':'a'*40}}),patch.object(u,'file_json',return_value={'version':'1.1.0'}),patch.object(Path,'mkdir',side_effect=OSError('read only')):
    result=u.check(p,None,now=100000)
   self.assertEqual(result['status'],'update_available');self.assertFalse(result['cache_saved'])
 def test_invalid_remote_sha_never_generates_apply_command(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);package(p,'1.0.0')
   with patch.object(u,'request',return_value={'object':{'sha':'bad-sha'}}),patch.object(u,'file_json',return_value={'version':'1.1.0'}):
    result=u.check(p,None,now=100000)
   self.assertEqual(result['status'],'not_updated');self.assertIsNone(result['apply_command'])
 def test_progress_and_backup(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'old';q=Path(d)/'new';package(p,'1');package(q,'2');(p/'.local').mkdir();(p/'.local/progress.md').write_text('进度')
   backup=u.replace_package(p,q)
   self.assertEqual((p/'.local/progress.md').read_text(),'进度');self.assertEqual((backup/'SKILL.md').read_text(),'1');self.assertEqual((p/'SKILL.md').read_text(),'2')
 def test_local_edit_refused(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'old';q=Path(d)/'new';package(p,'1');package(q,'2');(p/'SKILL.md').write_text('客户修改')
   with self.assertRaises(u.UpdateError):u.replace_package(p,q)
   self.assertEqual((p/'SKILL.md').read_text(),'客户修改')
 def test_rollback(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'old';q=Path(d)/'new';package(p,'1');package(q,'2');original=Path.rename
   def rename(a,b):
    if a==q:raise OSError('模拟更新失败')
    return original(a,b)
   with patch.object(Path,'rename',rename):
    with self.assertRaises(OSError):u.replace_package(p,q)
   self.assertEqual((p/'SKILL.md').read_text(),'1')
 def test_bad_zip_and_valid_zip(self):
  with tempfile.TemporaryDirectory() as d:
   b=io.BytesIO()
   with zipfile.ZipFile(b,'w') as z:z.writestr('repo/../../escape','x')
   with self.assertRaises(u.UpdateError):u.extract_archive(b.getvalue(),Path(d))
   p=Path(d)/'src';package(p,'1');b=io.BytesIO()
   with zipfile.ZipFile(b,'w') as z:
    for f in p.iterdir():z.write(f,'repo/'+f.name)
   q=Path(d)/'dest';q.mkdir();u.extract_archive(b.getvalue(),q);self.assertEqual((q/'SKILL.md').read_text(),'1')
 def test_unavailable_leaves_local(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);package(p,'1')
   with patch.object(u,'ROOT',p),patch.object(u,'token',return_value=None),patch.object(u,'request',side_effect=OSError('offline')),patch('sys.argv',['update.py','check']),patch('sys.stdout',new_callable=io.StringIO) as out:
    self.assertEqual(u.main(),2);self.assertEqual(json.loads(out.getvalue())['status'],'unavailable')
   self.assertEqual((p/'SKILL.md').read_text(),'1')
if __name__=='__main__':unittest.main()
