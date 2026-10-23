"""CLI workflow in a disposable project; SSH responses use a persisted fixture.

Real panel/API behavior is covered separately by panel_contract_smoke.py.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


SSH_FIXTURE = r'''
import json, os, sys, time
from pathlib import Path
root = Path(os.environ['WORKFLOW_FIXTURE'])
request = json.load(sys.stdin)
action = request['action']
if (root/'fail').exists():
    print('SSH connection lost', file=sys.stderr)
    sys.exit(1)
if (root/'wait').exists():
    (root/'started').touch()
    time.sleep(1)
    sys.exit(1)
with (root/'calls').open('a') as f:
    f.write(action+'\n')
if action == 'deploy':
    receipt = root/'node'
    if not receipt.exists():
        receipt.write_text('vless://fixture-secret')
    print(json.dumps({'status': 'configured'}))
elif action == 'verify':
    print(json.dumps({'status':'passed', 'uri':(root/'node').read_text(),
                      'panel':{'password':'fixture-password'}}))
else:
    print(json.dumps({'status':'passed'}))
'''


@unittest.skipIf(os.name == 'nt', 'POSIX executable fixture for the SSH boundary')
class NetworkWorkflowTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        scripts = self.root/'scripts'
        scripts.mkdir()
        source = Path(__file__).resolve().parents[1]/'scripts'
        for name in ('network.py', 'network_server.py', 'workflow_guard.py', 'score_policy.py'):
            shutil.copy2(source/name, scripts/name)
        self.private = self.root/'.local/network'
        self.private.mkdir(parents=True)
        self.progress = self.root/'.local/progress.md'
        self.progress.write_text('已有客户选择\n', encoding='utf-8')
        self.fixture = self.root/'fixture'
        self.fixture.mkdir()
        executable = self.fixture/'ssh'
        executable.write_text('#!'+sys.executable+'\n'+SSH_FIXTURE)
        executable.chmod(0o700)
        self.env = dict(os.environ, PATH=str(self.fixture)+os.pathsep+os.environ['PATH'],
                        WORKFLOW_FIXTURE=str(self.fixture), PYTHONDONTWRITEBYTECODE='1')
        self.configuration = {'context':'workflow-1',
            'ssh':{'host':'203.0.113.10','user':'root'},
            'server':{'address':'203.0.113.10','port':443,'panel_port':18899,'sni':'www.microsoft.com'}}
        self.write_config()

    def write_config(self):
        (self.private/'input.json').write_text(json.dumps(self.configuration))

    def command(self, *args):
        return [sys.executable, str(self.root/'scripts/network.py'), *args]

    def run_cli(self, *args, code=0):
        r = subprocess.run(self.command(*args), env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(r.returncode, code, r.stdout+r.stderr)
        result = json.loads(r.stdout)
        self.assertNotIn('fixture-secret', r.stdout)
        self.assertNotIn('fixture-password', r.stdout)
        return result

    def test_deploy_export_scores_and_changed_configuration(self):
        self.assertEqual(self.run_cli('preflight')['status'], 'passed')
        self.assertEqual(self.run_cli('deploy')['status'], 'configured')
        first = (self.private/'node.txt').read_bytes()
        self.run_cli('deploy')
        self.run_cli('export')
        self.assertEqual((self.private/'node.txt').read_bytes(), first)
        self.assertEqual((self.fixture/'calls').read_text().splitlines(),
                         ['preflight','deploy','verify','deploy','verify','verify'])
        for environment in ('adspower', 'iphone_wifi', 'iphone_cellular'):
            data = {'context':'workflow-1','environment':environment,
                'observed_at':'2020-01-01T00:00:00+00:00','exit_matches':True,
                'scores':{name:{'value':value,'evidence':'模拟网页观察'} for name,value in
                          [('netcoffee',79),('ping0',35),('scamalytics',None)]}}
            source = self.private/'observations.json'
            source.write_text(json.dumps(data))
            result = self.run_cli('scores','--input',str(source))
            self.assertEqual(result['scores']['netcoffee']['assessment'], 'near_reference')
            self.assertEqual(result['scores']['ping0']['assessment'], 'near_reference')
            self.assertEqual(result['scores']['scamalytics']['assessment'], 'unverified')
            self.assertEqual(result['freshness'], 'recheck_recommended')
        report = self.run_cli('status')
        self.assertEqual(len([k for k in report['steps'] if k.startswith('scores_')]), 3)
        self.configuration['context'] = 'workflow-2'
        self.write_config()
        report = self.run_cli('status')
        self.assertTrue(all(s['status'] == 'stale' for s in report['steps'].values()))
        self.assertTrue(self.progress.read_text().startswith('已有客户选择\n'))
        self.assertEqual(self.progress.read_text().count('<!-- network-execution-report -->'), 1)

    def test_failed_export_then_retry(self):
        self.run_cli('deploy')
        (self.fixture/'fail').touch()
        result = self.run_cli('export', code=1)
        self.assertEqual(result['error'], 'ssh_or_remote_protocol_failed')
        self.assertEqual(self.run_cli('status')['steps']['export']['status'], 'failed')
        (self.fixture/'fail').unlink()
        self.assertEqual(self.run_cli('export')['status'], 'exported')

    def test_killed_process_recovers_and_releases_lock(self):
        (self.fixture/'wait').touch()
        process = subprocess.Popen(self.command('preflight'), env=self.env,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(100):
                if (self.fixture/'started').exists():
                    break
                time.sleep(0.02)
            self.assertTrue((self.fixture/'started').exists())
            self.assertEqual(self.run_cli('status', code=1)['error'], 'execution_busy')
            process.kill()
            process.wait(timeout=5)
            self.assertEqual(self.run_cli('status')['steps']['preflight']['status'], 'interrupted')
            (self.fixture/'wait').unlink()
            self.assertEqual(self.run_cli('preflight')['status'], 'passed')
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()
