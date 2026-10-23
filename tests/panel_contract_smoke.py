"""Explicit opt-in test. Run ONLY in an empty disposable Linux container.

Usage: python3 tests/panel_contract_smoke.py /path/to/panel.tar.gz /path/to/xray.zip
Add --connectivity to send an HTTPS request through a real VLESS/REALITY client.
Default mode checks the supplied archive digests and the real panel/runtime locally.
Connectivity mode adds an Xray client and a live HTTPS request through REALITY.
"""
import copy
import http.client
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import network_server as s


def reality_request(receipt):
    identity, server = receipt['identity'], receipt['config']
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    configuration = {
        'inbounds':[{'listen':'127.0.0.1','port':port,'protocol':'http','settings':{}}],
        'outbounds':[{'protocol':'vless','settings':{'vnext':[{
            'address':'127.0.0.1','port':server['port'],
            'users':[{'id':identity['uuid'],'encryption':'none','flow':s.FLOW}]}]},
            'streamSettings':{'network':'tcp','security':'reality','realitySettings':{
                'serverName':server['sni'],'fingerprint':'chrome','publicKey':identity['public_key'],
                'shortId':identity['short_id'],'spiderX':'/'}}}]}
    config = s.HOME/'client.json'
    s.save(config, configuration)
    with tempfile.TemporaryFile() as log:
        client = subprocess.Popen([str(s.xray_binary()), 'run', '-config', str(config)],
                                  stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                try:
                    with socket.create_connection(('127.0.0.1', port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.1)
            connection = http.client.HTTPSConnection('127.0.0.1', port, timeout=30)
            try:
                connection.set_tunnel('www.gstatic.com', 443)
                connection.request('GET', '/generate_204')
                response = connection.getresponse()
                assert response.status == 204 and not response.read()
            finally:
                connection.close()
        finally:
            client.terminate()
            client.wait(timeout=10)


def main():
    assert sys.platform == 'linux' and os.geteuid() == 0
    assert Path('/.dockerenv').exists(), 'Disposable Docker container only'
    assert not s.INSTALL.exists() and not Path('/etc/x-ui').exists(), 'Empty container required'
    archive = Path(sys.argv[1])
    xray_archive = Path(sys.argv[2])
    s.HOME = Path(tempfile.mkdtemp())

    def download(url, **kw):
        return (xray_archive if '/XTLS/Xray-core/' in url else archive).open('rb')

    with patch.object(s.urllib.request, 'urlopen', side_effect=download):
        s.install_archive()
    assert s.command([str(s.INSTALL/'x-ui'), '-v']).strip() == s.VERSION.lstrip('v')
    assert s.xray_version(s.xray_binary()) == s.XRAY_VERSION
    receipt = {'version': s.VERSION, 'xray_version': s.XRAY_VERSION, 'min_client_version': s.MIN_CLIENT_VERSION,
               'config': s.validate({'address': '203.0.113.10', 'port': 18555, 'panel_port': 18899}),
               'base_path': 'local-test', 'username': 'local-test', 'password': 'container-only'}
    s.configure_panel(receipt)
    with tempfile.TemporaryFile() as log:
        proc = subprocess.Popen([str(s.INSTALL/'x-ui')], cwd=s.INSTALL, stdout=log, stderr=subprocess.STDOUT)
        try:
            panel = s.wait_panel(receipt)
            s.panel_listen_verified(18899)
            saved = []

            def persist(r):
                saved.append(copy.deepcopy(r))
                s.save(s.HOME / 'receipt.json', r)

            s.ensure_node(panel, receipt, persist)
            real_command = s.command

            def container_command(args, *a, **kw):
                # This container launches the actual panel directly, without systemd.
                if args == ['systemctl', 'is-active', 'x-ui']:
                    return 'active\n'
                return real_command(args, *a, **kw)

            with patch.object(s, 'command', side_effect=container_command):
                verified = s.verify(receipt['config'])
            assert verified['status'] == 'passed' and verified['uri'] == s.export_uri(receipt)
            identity = copy.deepcopy(receipt['identity'])
            s.ensure_node(panel, receipt, persist)
            assert receipt['identity'] == identity and len(panel.call('inbounds/list')) == 1
            status = panel.call('server/status')
            assert status['xray']['state'] == 'running'
            assert status['xray']['version'] == s.XRAY_VERSION
            node = panel.call('inbounds/list')[0]
            reality = s.object_field(node['streamSettings'])['realitySettings']
            assert reality['minClientVer'] == s.MIN_CLIENT_VERSION
            assert reality['target'] == s.DEFAULT_SNI + ':443'
            assert reality['serverNames'] == [s.DEFAULT_SNI]
            for table in ('tcp', 'tcp6'):
                for line in Path('/proc/net/'+table).read_text().splitlines()[1:]:
                    fields = line.split()
                    assert not (fields[3] == '0A' and int(fields[1].split(':')[1], 16) == 2096), 'Subscription listener unexpectedly open'
            # The generated config is the one actually accepted by the pinned Xray.
            binary = s.INSTALL/'bin'/('xray-linux-'+s.ARCHIVES[s.platform.machine()][0])
            result = subprocess.run([str(binary), 'run', '-test', '-config', 'bin/config.json'], cwd=s.INSTALL, capture_output=True)
            assert result.returncode == 0
            if '--connectivity' in sys.argv:
                reality_request(receipt)
            print(json.dumps({'status':'passed', 'panel_version':s.VERSION, 'xray_version':status['xray']['version'],
                              'archive_checksum':True, 'node_reused':True, 'node_listening':True,
                              'panel_loopback_only':True, 'subscription_disabled':True, 'xray_config_valid':True,
                              'immediate_verify_and_export':True, 'stable_reality_profile':True,
                              'xray_client_reality_https_204':'--connectivity' in sys.argv}))
        finally:
            proc.terminate()
            proc.wait(timeout=10)


if __name__ == '__main__':
    main()
