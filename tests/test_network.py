import copy
import http.server
import importlib
import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from urllib.parse import urlsplit, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import network as n
import network_server as s

CONFIG = {'context': 'fixture-1', 'probe': {'proxy': 'http://127.0.0.1:12345', 'expected_exit_ipv4': '203.0.113.10'}}
SERVER = {'address': '203.0.113.10', 'port': 18555, 'panel_port': 18899, 'sni': 'www.microsoft.com'}


class MemoryPanel:
    def __init__(self):
        self.nodes = []
        self.posts = 0
        self.ambiguous = False

    def call(self, path, payload=None):
        if path == 'server/getNewX25519Cert':
            return {'privateKey': 'a'*43, 'publicKey': 'b'*43}
        if path == 'inbounds/list':
            return copy.deepcopy(self.nodes)
        if path == 'inbounds/add':
            self.posts += 1
            self.nodes.append(dict(copy.deepcopy(payload), id=1))
            if self.ambiguous:
                raise TimeoutError('secret response')
            return self.nodes[-1]
        raise AssertionError(path)


class ServerTests(unittest.TestCase):
    def test_ambiguous_create_reuses_persisted_identity(self):
        panel = MemoryPanel(); panel.ambiguous = True
        receipt = {'config': SERVER}
        saved = []
        with self.assertRaises(TimeoutError):
            s.ensure_node(panel, receipt, lambda x: saved.append(copy.deepcopy(x)))
        self.assertEqual(len(saved), 1)
        self.assertIn('identity', saved[0])
        resumed = copy.deepcopy(saved[0])
        s.ensure_node(panel, resumed, lambda x: None)
        self.assertEqual(panel.posts, 1)
        self.assertEqual(receipt['identity'], resumed['identity'])
        parsed = urlsplit(s.export_uri(resumed)); params = parse_qs(parsed.query)
        self.assertEqual(parsed.username, resumed['identity']['uuid'])
        self.assertEqual(parsed.port, SERVER['port'])
        self.assertEqual(params['pbk'][0], resumed['identity']['public_key'])
        self.assertEqual(params['flow'], ['xtls-rprx-vision'])
        self.assertNotIn(resumed['identity']['private_key'], s.export_uri(resumed))

    def test_existing_drift_or_collision_is_never_overwritten(self):
        panel = MemoryPanel(); receipt = {'config': SERVER}
        s.ensure_node(panel, receipt, lambda x: None)
        panel.nodes[0]['streamSettings']['realitySettings']['serverNames'] = ['other.example']
        with self.assertRaisesRegex(s.Failure, 'drift'):
            s.ensure_node(panel, receipt, lambda x: None)
        self.assertEqual(panel.posts, 1)
        with self.assertRaisesRegex(s.Failure, 'port_in_use'):
            s.ensure_node(panel, {'config': SERVER}, lambda x: None)
        self.assertEqual(panel.posts, 1)

    def test_string_and_object_api_shapes(self):
        panel = MemoryPanel(); receipt = {'config': SERVER}
        s.ensure_node(panel, receipt, lambda x: None)
        for key in ('settings', 'streamSettings'):
            panel.nodes[0][key] = json.dumps(panel.nodes[0][key])
        s.ensure_node(panel, receipt, lambda x: None)
        self.assertEqual(panel.posts, 1)

    def test_invalid_server_parameters(self):
        self.assertEqual(s.validate(dict(SERVER, port=443))['port'], 443)
        for key, val in [('port', 0), ('port', -1), ('port', True), ('port', 99999), ('panel_port', 18555), ('sni', 'x; reboot'), ('address', '-oProxyCommand=x')]:
            with self.subTest(key=key), self.assertRaises(s.Failure):
                s.validate(dict(SERVER, **{key: val}))


class ProbeTests(unittest.TestCase):
    def request(self, url, proxy):
        return {'code': 204 if url == n.HTTPS_URL else 200, 'transport': 'ok', 'body': '' if url == n.HTTPS_URL else '203.0.113.10\n'}

    def test_exit_and_https_both_required_and_output_redacted(self):
        r = n.probe(CONFIG, 'proxy', self.request)
        self.assertEqual(r['status'], 'passed')
        self.assertEqual(r['vpn_handoff'], 'unverified')
        self.assertNotIn('203.0.113.10', json.dumps(r))
        for response in [dict(code=200, transport='ok', body='203.0.113.11'), dict(code=200, transport='ok', body='<html>captcha</html>'), dict(code=200, transport='curl_28', body='203.0.113.10')]:
            def request(url, proxy):
                return self.request(url, proxy) if url == n.HTTPS_URL else response
            self.assertEqual(n.probe(CONFIG, 'proxy', request)['status'], 'failed')

    def test_fallback_exit_and_disagreement(self):
        def one_failed(url, proxy):
            return {'code': 0, 'transport': 'timeout', 'body': ''} if url == n.EXIT_URLS[0] else self.request(url, proxy)
        self.assertEqual(n.probe(CONFIG, 'proxy', one_failed)['status'], 'passed')
        def disagree(url, proxy):
            return {'code': 200, 'transport': 'ok', 'body': '203.0.113.11'} if url == n.EXIT_URLS[0] else self.request(url, proxy)
        self.assertEqual(n.probe(CONFIG, 'proxy', disagree)['status'], 'failed')

    def test_system_request_does_not_inherit_explicit_proxy(self):
        seen = []
        def request(url, proxy):
            seen.append(proxy); return self.request(url, proxy)
        n.probe(CONFIG, 'system', request)
        self.assertEqual(seen, [None, None, None])

    def test_real_curl_uses_proxy_despite_no_proxy_and_does_not_fallback(self):
        seen = []
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append(self.path)
                self.send_response(200); self.end_headers(); self.wfile.write(b'203.0.113.10')
            def log_message(self, *args): pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
        try:
            proxy = 'http://127.0.0.1:%d' % server.server_port
            with patch.dict(os.environ, {'NO_PROXY': '*', 'ALL_PROXY': 'http://127.0.0.1:1'}):
                r = n.curl_request('http://does-not-exist.invalid/ip', proxy, timeout=2)
            self.assertEqual(r['body'], '203.0.113.10')
            self.assertEqual(seen, ['http://does-not-exist.invalid/ip'])
        finally:
            server.shutdown(); server.server_close(); worker.join()
        r = n.curl_request('http://does-not-exist.invalid/ip', proxy, timeout=1)
        self.assertNotEqual(r['transport'], 'ok')

    def test_real_curl_timeout_is_not_success(self):
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                time.sleep(0.4)
            def log_message(self, *args): pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
        try:
            r = n.curl_request('http://slow.invalid/', 'http://127.0.0.1:%d' % server.server_port, timeout=0.1)
            self.assertEqual(r['transport'], 'curl_28')
        finally:
            server.shutdown(); server.server_close(); worker.join()


class StateTests(unittest.TestCase):
    def test_progress_preserved_context_invalidates_and_running_recovers(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root/'.local').mkdir(); p = root/'.local/progress.md'; p.write_text('existing customer decisions\n')
            state = n.State(root, CONFIG); state.begin('probe_proxy'); state.write_report()
            state = n.State(root, CONFIG)
            self.assertEqual(state.data['steps']['probe_proxy']['status'], 'interrupted')
            state.finish('probe_proxy', {'status': 'passed'})
            state = n.State(root, dict(CONFIG, context='changed')); state.write_report()
            self.assertEqual(state.data['steps']['probe_proxy']['status'], 'stale')
            self.assertTrue(p.read_text().startswith('existing customer decisions\n'))
            self.assertEqual(p.read_text().count('<!-- network-execution-report -->'), 1)
            self.assertEqual(state.report()['steps']['probe_proxy']['status'], 'stale')
            self.assertNotIn('complete', state.report())

    def test_failed_deploy_clears_old_success_and_sanitizes_exception(self):
        with tempfile.TemporaryDirectory() as d:
            state = n.State(Path(d), CONFIG); state.finish('probe_proxy', {'status': 'passed'})
            with patch.object(n, 'remote', side_effect=TimeoutError('secret password')):
                result = n.execute(SimpleNamespace(action='deploy'), CONFIG, state)
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(state.data['steps']['probe_proxy']['status'], 'stale')
            self.assertNotIn('secret password', json.dumps(state.report()))

    def test_corrupt_state_is_not_silently_recreated(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); path = root/'.local/network'; path.mkdir(parents=True); (path/'state.json').write_text('{broken')
            with self.assertRaises(ValueError): n.State(root, CONFIG)
            self.assertEqual((path/'state.json').read_text(), '{broken')

    def test_successful_deploy_uses_new_verify_call_and_keeps_secrets_private(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); state = n.State(root, CONFIG)
            verified = {'status':'passed', 'uri':'vless://private-node-secret', 'panel':{'password':'private-panel-secret'}, 'client_route':'unverified'}
            with patch.object(n, 'remote', side_effect=[{'status':'configured'}, verified]) as remote:
                result = n.execute(SimpleNamespace(action='deploy'), CONFIG, state)
            self.assertEqual([call.args[0] for call in remote.call_args_list], ['deploy', 'verify'])
            self.assertEqual(result['status'], 'configured')
            self.assertNotIn('private-node-secret', json.dumps(state.report()))
            self.assertNotIn('private-panel-secret', json.dumps(state.report()))
            self.assertIn('private-node-secret', (state.folder/'node.txt').read_text())
            self.assertEqual((state.folder/'node.txt').stat().st_mode & 0o777, 0o600)


class ScoreTests(unittest.TestCase):
    def data(self):
        return {'context': 'fixture-1', 'environment': 'adspower', 'observed_at': n.now(), 'exit_matches': True,
                'scores': {k: {'value': v, 'evidence': 'screenshot.png'} for k,v in [('netcoffee', 79), ('ping0', 35), ('scamalytics', None)]}}

    def test_tolerance_missing_result_and_recheck_are_distinct(self):
        r = n.scores(self.data(), 'fixture-1')
        self.assertEqual(r['scores']['netcoffee']['assessment'], 'near_reference')
        self.assertEqual(r['scores']['ping0']['assessment'], 'near_reference')
        self.assertEqual(r['scores']['scamalytics']['assessment'], 'unverified')
        data = self.data(); data['scores']['ping0']['value'] = 75
        self.assertEqual(n.scores(data, 'fixture-1')['scores']['ping0']['assessment'], 'recheck_recommended')
        self.assertTrue(r['advisory_only'])

    def test_invalid_observations_rejected_old_results_still_reported(self):
        old = n.scores(dict(self.data(), observed_at='2020-01-01T00:00:00+00:00'), 'fixture-1')
        self.assertEqual(old['status'], 'recorded')
        self.assertEqual(old['scores']['netcoffee']['value'], 79)
        self.assertEqual(old['freshness'], 'recheck_recommended')
        for change in [{'context': 'other'}, {'observed_at': '2999-01-01T00:00:00+00:00'}, {'observed_at': '2020-01-01T00:00:00'}]:
            with self.assertRaises(s.Failure): n.scores(dict(self.data(), **change), 'fixture-1')
        for value in [float('nan'), 101, True]:
            data = self.data(); data['scores']['ping0']['value'] = value
            with self.assertRaises(s.Failure): n.scores(data, 'fixture-1')

    def test_environments_remain_separate_and_failed_refresh_cannot_keep_success(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve(); state = n.State(root, CONFIG)
            source = root/'.local/scores.json'
            args = SimpleNamespace(action='scores', input=str(source))
            data = self.data()
            for item in data['scores'].values():
                item['evidence'] = '当前浏览器页面直接观察，未保存截图'
            source.write_text(json.dumps(data))
            self.assertEqual(n.execute(args, CONFIG, state)['status'], 'recorded')
            data['environment'] = 'iphone_wifi'; source.write_text(json.dumps(data))
            self.assertEqual(n.execute(args, CONFIG, state)['status'], 'recorded')
            self.assertEqual(state.data['steps']['scores_adspower']['status'], 'recorded')
            data['scores']['netcoffee']['evidence'] = ''
            source.write_text(json.dumps(data))
            self.assertEqual(n.execute(args, CONFIG, state)['status'], 'failed')
            self.assertEqual(state.data['steps']['scores_iphone_wifi']['status'], 'failed')
            self.assertEqual(state.data['steps']['scores_adspower']['status'], 'recorded')


if __name__ == '__main__':
    unittest.main()
