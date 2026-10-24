"""Update checks at real CLI response boundaries, with isolated remote responses."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import workflow
import login_readiness
import update


class WorkflowUpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'version.json').write_text(json.dumps({'version': '1.0.41'}))
        self.now = 100000
        for target, kwargs in (
            ('update.request', {'return_value': {'object': {'sha': 'a' * 40}}}),
            ('update.file_json', {'return_value': {'version': '1.0.42', 'summary': ['Device settings']}}),
            ('update.time.time', {'side_effect': lambda: self.now}),
        ):
            patcher = patch(target, **kwargs)
            mock = patcher.start()
            self.addCleanup(patcher.stop)
            if target == 'update.request':
                self.remote = mock

    def cli(self, module, *args):
        with patch.object(module, 'ROOT', self.root), patch('sys.argv', ['script', *args]), \
                patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(module.main(), 0, out.getvalue())
            return json.loads(out.getvalue())

    def test_init_next_submit_status_and_legacy_return_notice_with_cache(self):
        with patch.object(update, 'replace_package') as apply:
            first = self.cli(workflow, 'init')
            self.assertEqual(first['update']['status'], 'update_available')
            self.assertIn(first['update']['update_notice'], first['customer_message'])
            self.assertEqual(first['stage'], 'intake')
            for args in [('next',), ('status',), ('init',)]:
                view = self.cli(workflow, *args)
                self.assertTrue(view['update']['cached'])
                self.assertEqual(view['ticket'], first['ticket'])
            legacy = self.cli(login_readiness)
            self.assertIn(legacy['update']['update_notice'], legacy['customer_message'])
            payload = first['submission']
            payload.update(data={'banned_login': 'no'}, source={'kind': 'user', 'reference': 'customer reply'})
            path = self.root / 'reply.json'; path.write_text(json.dumps(payload))
            view = self.cli(workflow, 'submit', '--input', str(path))
            self.assertEqual(view['stage'], 'devices')
            self.assertIn(view['update']['update_notice'], view['customer_message'])
            self.assertEqual(self.remote.call_count, 1)
            apply.assert_not_called()

    def test_expiry_force_and_local_version_change_refresh_check(self):
        self.cli(workflow, 'init')
        self.now += update.CHECK_INTERVAL
        self.assertFalse(self.cli(workflow, 'next')['update']['cached'])
        self.assertEqual(self.remote.call_count, 2)
        update.check(self.root, None, force=True)
        self.assertEqual(self.remote.call_count, 3)
        self.assertTrue(self.cli(workflow, 'next')['update']['cached'])
        (self.root / 'version.json').write_text(json.dumps({'version': '1.0.42'}))
        view = self.cli(workflow, 'next')
        self.assertEqual(view['update']['status'], 'current')
        self.assertIsNone(view['update']['update_notice'])
        self.assertNotIn('v1.0.42', view['customer_message'])
        self.assertEqual(self.remote.call_count, 4)

    def test_offline_check_keeps_current_stage_and_caches_failure(self):
        self.remote.side_effect = OSError('offline')
        first = self.cli(workflow, 'init')
        self.assertEqual(first['stage'], 'intake')
        self.assertEqual(first['update']['status'], 'unavailable')
        self.assertIn('update_display_instruction', first)
        second = self.cli(workflow, 'next')
        self.assertEqual(second['ticket'], first['ticket'])
        self.assertTrue(second['update']['cached'])
        self.assertEqual(self.remote.call_count, 1)

    def test_internal_state_saves_do_not_check_network(self):
        flow = workflow.Workflow(self.root)
        flow.init(); flow.next(); flow.save()
        self.remote.assert_not_called()
        before = flow.path.read_bytes()
        result = update.workflow_output(self.root, {'execution': {'success': True}, 'workflow': flow.next()})
        self.assertEqual(result['execution'], {'success': True})
        self.assertIn('update', result['workflow'])
        self.assertIn(result['workflow']['update']['update_notice'], result['workflow']['customer_message'])
        self.assertEqual(flow.path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
