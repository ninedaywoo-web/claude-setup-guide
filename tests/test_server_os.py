"""Read real os-release fixtures and exercise the new-deployment boundary."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_workflow as fixtures
import network_server as server
from test_network import SERVER


class ServerSystemTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / 'os-release'

    def release(self, distro, version, name):
        self.path.write_text(f'ID={distro}\nVERSION_ID="{version}"\nPRETTY_NAME="{name}"\n')

    def test_debian_12_from_actual_release_file(self):
        self.release('debian', '12', 'Debian GNU/Linux 12 (bookworm)')
        result = server.check_server_os(False, self.path)
        self.assertEqual(result['id'], 'debian')
        self.assertEqual(result['version_id'], '12')

    def test_ubuntu_and_other_debian_versions_report_actual_system(self):
        for distro, version in [('ubuntu', '22.04'), ('ubuntu', '24.04'), ('debian', '11'), ('debian', '13')]:
            with self.subTest(distro=distro, version=version):
                self.release(distro, version, distro + ' ' + version)
                with self.assertRaises(server.SystemMismatch) as caught:
                    server.check_server_os(False, self.path)
                report = caught.exception.result
                self.assertEqual(report['operating_system']['version_id'], version)
                self.assertEqual(report['expected_system']['name'], 'Debian 12')
                self.assertIn(distro + ' ' + version, report['next_action'])

    def test_existing_managed_ubuntu_is_read_and_retained(self):
        self.release('ubuntu', '22.04', 'Ubuntu 22.04 LTS')
        self.assertEqual(server.check_server_os(True, self.path)['id'], 'ubuntu')

    def test_direct_deploy_stops_before_writes_on_ubuntu(self):
        self.release('ubuntu', '22.04', 'Ubuntu 22.04 LTS')
        read_system = server.check_server_os
        home = self.root / 'deployment'
        with patch.object(server, 'HOME', home), patch.object(server.platform, 'system', return_value='Linux'), \
                patch.object(server, 'check_server_os', side_effect=lambda managed: read_system(managed, self.path)):
            with self.assertRaises(server.SystemMismatch):
                server.deploy(dict(SERVER))
        self.assertFalse(home.exists())


class SystemGuidanceTests(unittest.TestCase):
    setUp = fixtures.WorkflowTests.setUp
    data = fixtures.WorkflowTests.data
    payload = fixtures.WorkflowTests.payload
    advance = fixtures.WorkflowTests.advance
    reach = fixtures.WorkflowTests.reach

    def test_purchase_deployment_and_original_figure_use_same_rule(self):
        self.reach('vps')
        view = self.flow.next()
        self.assertEqual(view['server_system'], server.SERVER_OS)
        self.assertIn('Debian 12', view['customer_message'])
        lesson = self.flow.guide('vps_dmit', 2)
        self.assertIn('Debian 12', lesson['customer_message'])
        self.assertEqual(lesson['customer_images'], ['assets/images/network/05.jpg'])
        self.advance()
        self.assertIn('Debian 12', self.flow.next()['customer_message'])
