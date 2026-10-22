"""Explicit opt-in test. Run ONLY in an empty disposable Linux container.

Usage: python3 tests/panel_contract_smoke.py /path/to/official-release.tar.gz
The network is unnecessary; the helper checks the pinned archive digest.
This does not test systemd, SSH, a real VPS, or client REALITY connectivity.
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import network_server as s


def main():
    assert sys.platform == 'linux' and os.geteuid() == 0
    assert Path('/.dockerenv').exists(), 'Disposable Docker container only'
    assert not s.INSTALL.exists() and not Path('/etc/x-ui').exists(), 'Empty container required'
    archive = Path(sys.argv[1])
    s.HOME = Path(tempfile.mkdtemp())
    with patch.object(s.urllib.request, 'urlopen', side_effect=lambda *a, **kw: archive.open('rb')):
        s.install_archive()
    assert s.command([str(s.INSTALL/'x-ui'), '-v']).strip() == s.VERSION.lstrip('v')
    receipt = {'version': s.VERSION, 'config': {'address': '203.0.113.10', 'port': 18555, 'panel_port': 18899, 'sni': 'www.microsoft.com'},
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
            for table in ('tcp', 'tcp6'):
                for line in Path('/proc/net/'+table).read_text().splitlines()[1:]:
                    fields = line.split()
                    assert not (fields[3] == '0A' and int(fields[1].split(':')[1], 16) == 2096), 'Subscription listener unexpectedly open'
            # The generated config is the one actually accepted by bundled Xray.
            binary = s.INSTALL/'bin'/('xray-linux-'+s.ARCHIVES[s.platform.machine()][0])
            result = subprocess.run([str(binary), 'run', '-test', '-config', 'bin/config.json'], cwd=s.INSTALL, capture_output=True)
            assert result.returncode == 0
            print(json.dumps({'status':'passed', 'panel_version':s.VERSION, 'xray_version':status['xray']['version'],
                              'archive_checksum':True, 'node_reused':True, 'node_listening':True,
                              'panel_loopback_only':True, 'subscription_disabled':True, 'xray_config_valid':True,
                              'immediate_verify_and_export':True}))
        finally:
            proc.terminate()
            proc.wait(timeout=10)


if __name__ == '__main__':
    main()
