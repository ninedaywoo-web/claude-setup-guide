import importlib.util, io, json, subprocess, tempfile, unittest, urllib.error
from pathlib import Path
from unittest.mock import patch, MagicMock
from test_start import release, SHA

spec=importlib.util.spec_from_file_location('download_update',Path(__file__).resolve().parents[1]/'scripts/update.py')
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)

class DownloadTests(unittest.TestCase):
    def test_api_unavailable_full_start_uses_pinned_official_fallbacks(self):
        meta,manifest,archive=release();seen=[]
        def fetch(url,headers=None,binary=False):
            seen.append((url,headers,binary))
            if url.startswith('https://api.github.com/'):
                raise urllib.error.HTTPError(url,403,'limited',{},None)
            self.assertIsNone(headers)
            if url==f'https://codeload.github.com/{u.REPO}/zip/{SHA}':
                self.assertTrue(binary);return archive
            base=f'https://raw.githubusercontent.com/{u.REPO}/{SHA}/'
            if url==base+'version.json':return json.dumps(meta).encode()
            if url==base+'manifest.json':return json.dumps(manifest).encode()
            self.fail('Unexpected endpoint: '+url)
        result=subprocess.CompletedProcess([],0,SHA+'\trefs/heads/main\n','')
        with tempfile.TemporaryDirectory() as d,patch.object(u,'fetch_bytes',side_effect=fetch),patch.object(u.shutil,'which',return_value='/git'),patch.object(u.subprocess,'run',return_value=result) as git:
            dest=Path(d)/'package';r=u.start_latest(dest,auth='test-secret')
            self.assertEqual(r['status'],'ready');self.assertEqual(r['commit'],SHA)
            self.assertEqual((dest/'SKILL.md').read_text(),'新规则')
            self.assertEqual(git.call_count,2)
            self.assertEqual(git.call_args.kwargs['env']['GIT_TERMINAL_PROMPT'],'0')
            self.assertNotIn('test-secret',str(git.call_args))
        self.assertTrue(any('codeload.github.com' in x[0] for x in seen))

    def test_fallback_does_not_mask_invalid_archive(self):
        def fetch(url,headers=None,binary=False):
            if 'api.github.com' in url:raise TimeoutError()
            return b'not a zip'
        with patch.object(u,'fetch_bytes',side_effect=fetch):
            data=u.request('zipball/'+SHA,None,binary=True)
        with tempfile.TemporaryDirectory() as d,self.assertRaises(u.zipfile.BadZipFile):
            u.extract_archive(data,Path(d))

    def test_download_failure_reports_stage_without_secret_or_manual_handoff(self):
        with patch.object(u,'fetch_bytes',side_effect=urllib.error.URLError('sensitive proxy detail')):
            with self.assertRaises(u.UpdateError) as raised:u.request('zipball/'+SHA,None,binary=True)
        message=str(raised.exception)
        self.assertIn('完整包下载',message);self.assertIn('备用通道',message)
        self.assertNotIn('sensitive proxy detail',message)
        self.assertIn('无需默认让用户点击',message)

    def test_transient_retry_and_archive_timeout(self):
        response=MagicMock();response.__enter__.return_value.read.return_value=b'zip'
        opener=MagicMock();opener.open.side_effect=[TimeoutError(),response]
        with patch.object(u.urllib.request,'build_opener',return_value=opener):
            self.assertEqual(u.fetch_bytes('https://codeload.github.com/test',binary=True),b'zip')
        self.assertEqual(opener.open.call_count,2)
        self.assertEqual(opener.open.call_args.kwargs['timeout'],60)

    def test_size_limit_is_not_retried_as_network_error(self):
        response=MagicMock();response.__enter__.return_value.read.return_value=b'12345'
        opener=MagicMock();opener.open.return_value=response
        with patch.object(u,'LIMIT',4),patch.object(u.urllib.request,'build_opener',return_value=opener),self.assertRaises(u.UpdateError):
            u.fetch_bytes('https://codeload.github.com/test',binary=True)
        self.assertEqual(opener.open.call_count,1)

    def test_write_permission_error_is_not_reported_as_github_access(self):
        with patch.object(u,'start_latest',side_effect=PermissionError('private path')),patch('sys.argv',['update.py','start','--destination','unused']),patch('sys.stdout',new_callable=io.StringIO) as out:
            self.assertEqual(u.main(),2)
            result=json.loads(out.getvalue())
        self.assertIn('本机文件读写权限不足',result['message'])
        self.assertNotIn('private path',result['message'])

if __name__=='__main__':unittest.main()
