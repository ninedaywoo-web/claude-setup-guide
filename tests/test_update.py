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
    self.assertEqual(u.check(p,None)['status'],'current')
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
