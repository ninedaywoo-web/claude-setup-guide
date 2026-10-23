import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/login_readiness.py'
spec = importlib.util.spec_from_file_location('login_readiness', SCRIPT)
flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flow)


class LoginReadinessTests(unittest.TestCase):
    def completed(self, computer='mac', phone='iphone'):
        record = flow.template(computer, phone)
        record.update(timezone_choice='node', target_timezone='America/Los_Angeles')
        for key, item in record['checks'].items():
            item.update(status='passed', result='Observed in isolated fixture')
            if key.endswith('_timezone_matches_choice'):
                item['timezone'] = record['target_timezone']
        return record

    def test_network_only_returns_device_settings(self):
        record = flow.template('mac', 'iphone')
        record.update(timezone_choice='node', target_timezone='America/Los_Angeles')
        for key in ('computer_network', 'browser_network', 'phone_proxy', 'phone_network'):
            record['checks'][key]['status'] = 'passed'
        result = flow.evaluate(record)
        self.assertEqual(result['status'], 'needs_setup')
        self.assertEqual(result['pending'][0]['id'], 'computer_timezone_auto_off')
        self.assertIn('phone_location_off', [x['id'] for x in result['pending']])

    def test_each_required_setting_is_independent(self):
        for key in self.completed()['checks']:
            with self.subTest(key=key):
                record = self.completed()
                del record['checks'][key]
                result = flow.evaluate(record)
                self.assertEqual(result['status'], 'needs_setup')
                self.assertEqual([x['id'] for x in result['pending']], [key])

    def test_resuming_only_requests_missing_phone_location(self):
        record = self.completed()
        record['checks']['phone_location_off']['status'] = 'pending'
        result = flow.evaluate(record)
        self.assertEqual(len(result['pending']), 1)
        self.assertEqual(result['pending'][0]['id'], 'phone_location_off')

    def test_complete_proceeds_without_confirmation(self):
        result = flow.evaluate(self.completed())
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(result['pending'], [])
        self.assertIn('Pro', result['next_action'])

    def test_windows_ipad_has_phone_settings_without_mac_fields(self):
        record = self.completed('windows', 'ipad')
        self.assertNotIn('computer_location_off', record['checks'])
        self.assertIn('phone_location_off', record['checks'])
        self.assertEqual(flow.evaluate(record)['status'], 'ready')

    def test_restored_location_requires_setup_again(self):
        record = self.completed()
        record['checks']['phone_location_off']['status'] = 'restored'
        self.assertEqual(flow.evaluate(record)['status'], 'needs_setup')

    def test_old_summary_does_not_complete_individual_settings(self):
        result = flow.evaluate({'computer': 'mac', 'phone': 'iphone', 'network': 'passed'})
        self.assertEqual(result['status'], 'needs_setup')
        self.assertEqual(len(result['pending']), 15)

    def test_taipei_choice_is_ready_on_all_devices(self):
        record = self.completed()
        record.update(timezone_choice='taipei', target_timezone='Asia/Taipei')
        for key, item in record['checks'].items():
            if key.endswith('_timezone_matches_choice'):
                item['timezone'] = 'Asia/Taipei'
        self.assertEqual(flow.evaluate(record)['status'], 'ready')

    def test_taipei_choice_requires_each_device_to_follow_it(self):
        for device in ('computer', 'phone', 'browser'):
            with self.subTest(device=device):
                record = self.completed()
                record.update(timezone_choice='taipei', target_timezone='Asia/Taipei')
                for key, item in record['checks'].items():
                    if key.endswith('_timezone_matches_choice'):
                        item['timezone'] = 'Asia/Taipei'
                key = device + '_timezone_matches_choice'
                record['checks'][key]['timezone'] = 'America/Los_Angeles'
                result = flow.evaluate(record)
                self.assertEqual([item['id'] for item in result['pending']], [key])

    def test_choice_is_requested_once_and_then_reused(self):
        record = self.completed()
        del record['timezone_choice']
        self.assertEqual(flow.evaluate(record)['pending'][0]['id'], 'timezone_choice')
        record['timezone_choice'] = 'node'
        self.assertEqual(flow.evaluate(record)['status'], 'ready')

    def test_taipei_cannot_use_shanghai_as_target(self):
        record = self.completed()
        record.update(timezone_choice='taipei', target_timezone='Asia/Shanghai')
        for key, item in record['checks'].items():
            if key.endswith('_timezone_matches_choice'):
                item['timezone'] = 'Asia/Shanghai'
        self.assertEqual(flow.evaluate(record)['pending'][0]['id'], 'target_timezone')

    def test_invalid_input_is_actionable(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'input.json'
            for content in ('{', '[]', '{"computer":"mac","phone":"iphone","checks":[]}'):
                path.write_text(content)
                run = subprocess.run([sys.executable, str(SCRIPT), '--input', str(path)],
                                     capture_output=True, text=True)
                self.assertEqual(run.returncode, 2)
                self.assertIn('input_needed', run.stdout)
                self.assertEqual(run.stderr, '')


if __name__ == '__main__':
    unittest.main()
