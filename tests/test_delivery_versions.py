import hashlib
import io
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import download_karing as k
import network_server as s
from test_network import MemoryPanel, SERVER


class DeliveryTests(unittest.TestCase):
    def test_new_node_uses_stable_defaults_and_checks_minimum_version(self):
        c = s.validate({key:value for key,value in SERVER.items() if key != 'sni'})
        self.assertEqual(c['sni'], 'www.cloudflare.com')
        receipt = {'config':c, 'min_client_version':s.MIN_CLIENT_VERSION}
        panel = MemoryPanel()
        node = s.ensure_node(panel, receipt, lambda r:None)
        reality = node['streamSettings']['realitySettings']
        self.assertEqual(reality['target'], 'www.cloudflare.com:443')
        self.assertEqual(reality['minClientVer'], '1.0.0')
        panel.nodes[0]['streamSettings']['realitySettings']['minClientVer'] = '2.0.0'
        with self.assertRaisesRegex(s.Failure, 'node_config_drift'):
            s.ensure_node(panel, receipt, lambda r:None)

    def test_existing_receipt_keeps_its_target_and_node(self):
        receipt = {'config':dict(SERVER)}
        panel = MemoryPanel()
        s.ensure_node(panel, receipt, lambda r:None)
        s.ensure_node(panel, receipt, lambda r:None)
        self.assertEqual(panel.posts, 1)
        self.assertEqual(receipt['config']['sni'], SERVER['sni'])
        self.assertNotIn('minClientVer', panel.nodes[0]['streamSettings']['realitySettings'])

    def test_export_checks_pinned_runtime_and_preserves_legacy_deployments(self):
        receipt = {'version':s.VERSION, 'config':dict(SERVER), 'xray_version':s.XRAY_VERSION,
                   'min_client_version':s.MIN_CLIENT_VERSION, 'base_path':'fixture',
                   'username':'fixture', 'password':'fixture'}
        panel = MemoryPanel()
        s.ensure_node(panel, receipt, lambda r:None)
        original_call = panel.call

        def call(path, payload=None):
            if path == 'server/status':
                return {'xray':{'state':'running', 'version':'26.10.10'}}
            return original_call(path, payload)

        panel.call = call
        with tempfile.TemporaryDirectory() as tmp, patch.object(s, 'HOME', Path(tmp)), \
             patch.object(s, 'Panel', return_value=panel), \
             patch.object(s, 'panel_listen_verified'), \
             patch.object(s, 'command', side_effect=lambda args: 'active' if args[0]=='systemctl' else '3.10.2'), \
             patch.object(s.socket, 'create_connection'):
            s.save(s.HOME/'receipt.json', receipt)
            with self.assertRaisesRegex(s.Failure, 'xray_version_changed'):
                s.verify(SERVER)
            del receipt['xray_version']
            s.save(s.HOME/'receipt.json', receipt)
            self.assertEqual(s.verify(SERVER)['xray_version'], '26.10.10')

    def panel_archive(self):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w:gz') as archive:
            item = tarfile.TarInfo('x-ui/bin/xray-linux-arm64')
            body = b'bundled-newer-xray'
            item.size = len(body)
            archive.addfile(item, io.BytesIO(body))
        return data.getvalue()

    def xray_archive(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('xray', b'pinned-xray')
        return data.getvalue()

    def test_failed_pinned_download_retries_before_installation_becomes_visible(self):
        panel, xray = self.panel_archive(), self.xray_archive()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); install = root/'x-ui'
            fetched = []
            corrupt = True

            def fetch(url, **kw):
                fetched.append(url)
                if '/XTLS/' in url:
                    self.assertFalse(install.exists())
                    return io.BytesIO(b'broken' if corrupt else xray)
                return io.BytesIO(panel)

            with patch.object(s, 'HOME', root), patch.object(s, 'INSTALL', install), \
                 patch.object(s.platform, 'machine', return_value='aarch64'), \
                 patch.dict(s.ARCHIVES, {'aarch64':('arm64',hashlib.sha256(panel).hexdigest())}), \
                 patch.dict(s.XRAY_ARCHIVES, {'aarch64':('Xray-linux-arm64-v8a.zip',hashlib.sha256(xray).hexdigest())}), \
                 patch.object(s.urllib.request, 'urlopen', side_effect=fetch), \
                 patch.object(s, 'xray_version', return_value=s.XRAY_VERSION):
                with self.assertRaisesRegex(s.Failure, 'xray_checksum_mismatch'):
                    s.install_archive()
                self.assertFalse(install.exists())
                self.assertFalse((root/'.claude-setup-x-ui-stage').exists())
                corrupt = False
                s.install_archive()
            self.assertEqual((install/'bin/xray-linux-arm64').read_bytes(), b'pinned-xray')
            self.assertTrue((install/'bin/xray-linux-arm64').stat().st_mode & 0o111)
            self.assertTrue(any('/v26.7.28/' in url for url in fetched))
            self.assertTrue(all('/latest/' not in url for url in fetched))

    def test_karing_download_validates_and_reuses_fixed_package(self):
        package = b'fixture-dmg'
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(k, 'SHA256', hashlib.sha256(package).hexdigest()), \
             patch.object(k.urllib.request, 'urlopen', return_value=io.BytesIO(package)) as fetch:
            first = k.download(tmp)
            second = k.download(tmp)
            self.assertEqual((first['status'], second['status']), ('downloaded', 'cached'))
            self.assertEqual(Path(first['path']).read_bytes(), package)
            fetch.assert_called_once_with(k.URL, timeout=60)
            self.assertIn('/v1.2.25.2802/', fetch.call_args.args[0])

    def test_karing_bad_download_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/k.FILENAME
            target.write_bytes(b'existing')
            with patch.object(k.urllib.request, 'urlopen', return_value=io.BytesIO(b'broken')):
                with self.assertRaisesRegex(s.Failure, 'karing_checksum_mismatch'):
                    k.download(tmp)
            self.assertEqual(target.read_bytes(), b'existing')
            self.assertEqual(list(Path(tmp).iterdir()), [target])


if __name__ == '__main__':
    unittest.main()
