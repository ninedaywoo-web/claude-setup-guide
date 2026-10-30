"""Whole-delivery state transitions and CLI execution boundaries, in isolation."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from workflow import Workflow, WorkflowError
from workflow_definition import catalog
from workflow_guard import check


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.now = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)
        self.flow = Workflow(self.root, lambda: self.now)
        self.flow.init()
        self.computer, self.phone = 'mac', 'iphone'
        self.choice = 'node'
        self.account_type = 'longstanding'
        self.first_used_at = self.now - timedelta(hours=49)

    def data(self, key):
        stage = next(s for s in catalog(self.flow.state) if s['id'] == key)
        data = {}
        for name, rule in stage['fields'].items():
            if isinstance(rule, bool):
                data[name] = rule
            elif isinstance(rule, tuple):
                data[name] = rule[0]
            elif rule == 'scores':
                data[name] = {site: {'value': {'netcoffee': 80, 'ping0': 20, 'scamalytics': 5}[site], 'result': 'Observed test page'} for site in ('netcoffee', 'ping0', 'scamalytics')}
            elif rule == 'timestamp':
                data[name] = self.first_used_at.isoformat()
            else:
                data[name] = 'observed-test-value'
        if key == 'intake':
            data['banned_login'] = 'no'
        if key == 'devices':
            data.update(computer=self.computer, phone=self.phone)
            if self.phone == 'android':
                data.update(android_route_explained=True, payment_route_status='available')
        if key == 'google':
            data['account_origin'] = 'self_used'
        if key == 'vps':
            data.update(node_label='node-a', node_timezone='America/Los_Angeles')
        if key == 'server':
            data['mode'] = 'existing'
        if key == 'browser':
            data.update(profile_ref='profile-a', checked_profile_ref='profile-a')
        if key in ('phone_proxy', 'phone_network'):
            data['node_label'] = 'node-a'
        if key == 'timezone':
            zone = 'Asia/Taipei' if self.choice == 'taipei' else 'America/Los_Angeles'
            data.update(choice=self.choice, target=zone, computer_zone=zone, phone_zone=zone, browser_zone=zone)
        if key == 'payment_preparation' and self.phone != 'android':
            data['account_type'] = self.account_type
            if self.account_type == 'new':
                data['first_used_at'] = self.first_used_at.isoformat()
                data['apple_reminder_shown'] = True
        if key in ('login', 'subscription'):
            data['account_ref'] = 'claude-main'
        if key == 'subscription':
            data['channel'] = 'google_pay' if self.phone == 'android' else 'apple'
        return data

    def payload(self, data=None):
        view = self.flow.next()
        return {'stage': view['stage'], 'ticket': view['ticket'],
                'source': {'kind': 'tool', 'reference': 'isolated device page observation'},
                'data': data if data is not None else self.data(view['stage'])}

    def advance(self):
        if self.flow.next()['stage'] == 'computer_network':
            # Stage-transition fixtures supply successful execution results;
            # separate receipt tests exercise missing and failed probes.
            good = lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(
                {'status': 'passed', 'exit_matches': True, 'https_204': True}))
            self.flow.run('probe_proxy', runner=good)
            self.flow.run('probe_system', runner=good)
            if self.flow.next()['stage'] != 'computer_network':
                return self.flow.next()
        return self.flow.submit(self.payload())

    def reach(self, target):
        for _ in range(20):
            if self.flow.next()['stage'] == target:
                return
            self.assertNotEqual(self.flow.next()['status'], 'waiting')
            self.advance()
        self.fail('stage was not reached: ' + str(target))

    def test_full_mac_iphone_delivery_exact_order(self):
        actual = []
        while self.flow.next()['stage']:
            actual.append(self.flow.next()['stage'])
            self.advance()
        self.assertEqual(actual, ['intake', 'devices', 'google', 'vps', 'server', 'computer_network',
                                 'browser', 'phone_proxy', 'timezone', 'phone_network',
                                 'payment_preparation', 'app', 'login', 'subscription'])
        self.assertEqual(self.flow.next()['status'], 'complete')
        self.assertIsNone(self.flow.next()['stage'])

    def test_fresh_session_starts_with_ban_history_not_timezone(self):
        self.assertEqual(self.flow.next()['stage'], 'intake')
        self.assertNotIn('choice', self.flow.next()['required_fields'])

    def test_cleanup_branch_is_selected_by_intake(self):
        self.flow.submit(self.payload({'banned_login': 'yes'}))
        self.assertEqual(self.flow.next()['stage'], 'cleanup')
        self.advance()
        self.assertEqual(self.flow.next()['stage'], 'devices')

    def test_device_guidance_survives_partial_input_and_resume(self):
        self.reach('devices')
        self.flow.submit(self.payload({'computer': 'windows', 'phone': 'iphone'}))
        resumed = Workflow(self.root, lambda: self.now)
        view = resumed.next()
        self.assertEqual(view['stage'], 'devices')
        self.assertEqual(view['missing'], ['pdf_explained', 'setup_explained'])
        for combination in ('Mac＋iPhone', 'Windows＋iPhone', 'Windows＋Android'):
            self.assertIn(combination, view['customer_message'])
        self.assertIn('手动操作', view['customer_message'])
        self.assertIn('整套交付验证', view['customer_message'])
        next_view = self.flow.submit(self.payload({'setup_explained': True}))
        self.assertEqual(next_view['stage'], 'devices')
        self.assertIn('PDF', next_view['customer_message'])
        self.flow.submit(self.payload({'pdf_explained': True}))
        self.assertEqual(self.flow.next()['stage'], 'google')

    def test_device_guidance_is_not_repeated_after_display(self):
        self.reach('devices')
        view = self.flow.submit(self.payload({'setup_explained': True}))
        self.assertEqual(view['stage'], 'devices')
        self.assertIn('PDF', view['customer_message'])
        self.flow.submit(self.payload({'computer': 'mac', 'phone': 'iphone'}))
        view = self.flow.invalidate('devices', '客户换成 Windows 和 Android')
        self.assertEqual(view['stage'], 'devices')
        self.assertIn('customer_message', view)

    def test_future_submission_rejected_at_every_stage(self):
        while self.flow.next()['stage']:
            payload = self.payload()
            payload['stage'] = 'phone_proxy' if payload['stage'] != 'phone_proxy' else 'subscription'
            before = deepcopy(self.flow.state)
            with self.assertRaises(WorkflowError):
                self.flow.submit(payload)
            self.assertEqual(self.flow.state, before)
            self.advance()

    def test_passed_flag_cannot_replace_observations(self):
        with self.assertRaisesRegex(WorkflowError, 'unknown_observation'):
            self.flow.submit(self.payload({'status': 'passed'}))
        self.assertEqual(self.flow.next()['stage'], 'intake')

    def test_browser_missing_each_fact_cannot_reach_phone(self):
        self.reach('browser')
        data = self.data('browser')
        baseline = deepcopy(self.flow.state)
        for field in data:
            with self.subTest(field=field):
                self.flow.state = deepcopy(baseline)
                incomplete = {k: v for k, v in data.items() if k != field}
                self.flow.submit(self.payload(incomplete))
                self.assertEqual(self.flow.next()['stage'], 'browser')
                self.assertIn(field, self.flow.next()['missing'])
        self.flow.state = baseline
        self.advance()
        self.assertEqual(self.flow.next()['stage'], 'phone_proxy')

    def test_browser_measurements_must_name_saved_profile(self):
        self.reach('browser')
        data = self.data('browser'); data['checked_profile_ref'] = 'default-browser'
        self.flow.submit(self.payload(data))
        self.assertEqual(self.flow.next()['stage'], 'browser')
        self.assertIn('checked_profile_ref', self.flow.next()['missing'])

    def test_partial_observations_resume_without_repeating_finished_fields(self):
        self.reach('computer_network')
        self.flow.submit(self.payload({'tun_enabled': True}))
        self.flow = Workflow(self.root, lambda: self.now)
        self.flow.sync()
        self.assertNotIn('tun_enabled', self.flow.next()['missing'])
        data = self.data('computer_network'); del data['tun_enabled']
        self.flow.submit(self.payload(data))
        self.advance()
        self.assertEqual(self.flow.next()['stage'], 'browser')

    def test_duplicate_submission_idempotent_and_stale_ticket_rejected(self):
        payload = self.payload(); self.flow.submit(payload)
        revision = self.flow.state['revision']
        self.flow.submit(payload)
        self.assertEqual(self.flow.state['revision'], revision)
        payload['data']['banned_login'] = 'yes'
        with self.assertRaisesRegex(WorkflowError, 'ticket_already_used'):
            self.flow.submit(payload)

    def test_new_apple_account_wait_preserved_across_restart(self):
        self.account_type = 'new'; self.first_used_at = self.now - timedelta(hours=12)
        self.reach('payment_preparation'); self.advance()
        self.assertEqual(self.flow.next()['status'], 'waiting')
        resume = self.flow.next()['resume_at']
        self.flow = Workflow(self.root, lambda: self.now)
        self.flow.sync()
        self.assertEqual(self.flow.next()['resume_at'], resume)
        self.now += timedelta(hours=36)
        self.assertEqual(self.flow.next()['stage'], 'app')

    def test_wait_requires_actual_first_use_not_generic_ready(self):
        self.reach('payment_preparation')
        data = self.data('payment_preparation'); data['account_type'] = 'new'
        self.flow.submit(self.payload(data))
        self.assertIn('first_used_at', self.flow.next()['missing'])

    def test_phone_order_and_current_account_entitlement_both_required(self):
        self.reach('subscription')
        data = self.data('subscription'); data.update(order_confirmed=True, pro_visible=False)
        self.flow.submit(self.payload(data))
        self.assertEqual(self.flow.next()['stage'], 'subscription')
        self.flow.submit(self.payload({'pro_visible': True, 'account_ref': 'another-account'}))
        self.assertEqual(self.flow.next()['stage'], 'subscription')
        self.flow.submit(self.payload({'account_ref': 'claude-main'}))
        self.assertEqual(self.flow.next()['status'], 'complete')

    def test_windows_android_branch_has_no_apple_requirements(self):
        self.computer, self.phone, self.choice = 'windows', 'android', 'taipei'
        self.reach('timezone')
        self.assertIn('computer_location_off', self.flow.next()['required_fields'])
        self.assertNotIn('computer_timezone_location_off', self.flow.next()['required_fields'])
        self.advance(); self.reach('payment_preparation')
        self.assertNotIn('account_type', self.flow.next()['required_fields'])
        self.advance(); self.assertIn('official_site_open', self.flow.next()['required_fields'])
        self.reach(None)
        self.assertEqual(self.flow.next()['status'], 'complete')

    def test_ipad_taipei_and_single_device_mismatch(self):
        self.phone, self.choice = 'ipad', 'taipei'
        self.reach('timezone')
        data = self.data('timezone'); data['computer_zone'] = 'America/Los_Angeles'
        self.flow.submit(self.payload(data))
        self.assertEqual(self.flow.next()['missing'], ['computer_zone'])
        self.flow.submit(self.payload({'computer_zone': 'Asia/Taipei'}))
        self.assertEqual(self.flow.next()['stage'], 'phone_network')

    def test_network_generation_invalidates_checks_retains_paid_order(self):
        self.reach(None)
        network = self.root / '.local/network'; network.mkdir()
        (network / 'state.json').write_text(json.dumps({'generation': 1}))
        self.flow.sync()
        self.assertEqual(self.flow.next()['stage'], 'computer_network')
        self.assertNotIn('browser', self.flow.state['records'])
        self.assertTrue(self.flow.state['records']['subscription']['data']['order_confirmed'])
        self.reach(None)
        self.assertEqual(sum(x['event'] == 'observed' and x.get('stage') == 'subscription'
                             for x in self.flow.state['history']), 1)

    def test_config_change_without_generation_also_invalidates(self):
        self.reach('login')
        folder = self.root / '.local/network'; folder.mkdir()
        (folder / 'input.json').write_text('{"context":"changed-node"}')
        self.flow.sync()
        self.assertEqual(self.flow.next()['stage'], 'server')

    def test_formatting_only_config_edit_preserves_completed_checks(self):
        folder = self.root / '.local/network'; folder.mkdir()
        config = folder / 'input.json'; config.write_text('{"context":"same"}')
        self.flow.sync(); self.reach('login')
        config.write_text('{\n  "context": "same"\n}')
        self.flow.sync()
        self.assertEqual(self.flow.next()['stage'], 'login')

    def test_timezone_change_does_not_reset_account_age_or_order(self):
        self.account_type = 'new'; self.reach(None)
        original = deepcopy(self.flow.state['records']['payment_preparation'])
        self.flow.invalidate('timezone', 'customer chose Taipei')
        self.assertEqual(self.flow.next()['stage'], 'timezone')
        self.choice = 'taipei'; self.advance()
        self.assertEqual(self.flow.next()['status'], 'complete')
        self.assertEqual(self.flow.state['records']['payment_preparation'], original)

    def test_phone_change_returns_existing_payment_hint(self):
        self.reach(None)
        self.flow.invalidate('phone', 'same platform, replacement phone')
        self.reach('subscription')
        self.assertIn('已有付款记录', self.flow.next()['next_action'])
        self.assertTrue(self.flow.next()['previous_observation']['order_confirmed'])

    def test_legacy_text_not_automatically_marked_complete(self):
        path = self.root / '.local/progress.md'
        path.write_text('所有步骤已完成\n', encoding='utf-8')
        self.flow.init()
        self.assertEqual(self.flow.next()['stage'], 'intake')
        self.assertTrue(path.read_text().startswith('所有步骤已完成'))

    def test_scripted_server_requires_execution_receipt(self):
        self.reach('server')
        data = self.data('server'); data['mode'] = 'scripted'
        self.flow.submit(self.payload(data))
        self.assertEqual(self.flow.next()['stage'], 'server')
        self.assertIn('server_readback', self.flow.next()['missing'])

    def test_failed_probe_cannot_be_overridden_with_true_flags(self):
        self.reach('computer_network')
        folder = self.root / '.local/network'; folder.mkdir()
        (folder / 'input.json').write_text('{"probe": {}}')
        self.flow.state['network_signature'] = self.flow.signature()
        self.flow.save()
        runner = lambda *a, **k: SimpleNamespace(returncode=1, stdout='{"status":"failed"}')
        self.flow.run('probe_system', runner=runner)
        self.flow.submit(self.payload(self.data('computer_network')))
        self.assertEqual(self.flow.next()['stage'], 'computer_network')
        self.assertIn('probe_system', self.flow.next()['missing'])
        good = lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(
            {'status': 'passed', 'exit_matches': True, 'https_204': True}))
        self.flow.run('probe_system', runner=good)
        self.flow.run('probe_proxy', runner=good)
        self.assertEqual(self.flow.next()['stage'], 'browser')

    def test_device_platform_change_rebuilds_android_branch(self):
        self.reach(None)
        self.flow.invalidate('devices', 'switch from Mac/iPhone to Windows/Android')
        self.assertEqual(self.flow.next()['stage'], 'devices')
        self.computer, self.phone = 'windows', 'android'
        self.advance()
        self.assertEqual(self.flow.next()['stage'], 'computer_network')
        self.reach('payment_preparation')
        self.assertIn('payment_method_available', self.flow.next()['required_fields'])

    def test_next_template_only_contains_remaining_fields(self):
        self.reach('computer_network')
        self.flow.submit(self.payload({'tun_enabled': True}))
        self.assertNotIn('tun_enabled', self.flow.next()['submission']['data'])

    def test_execution_permission_and_failed_run_do_not_advance(self):
        with self.assertRaisesRegex(WorkflowError, 'action_out_of_stage'):
            self.flow.run('server_deploy')
        self.reach('server')
        def fail(command, **kwargs):
            with patch.dict('os.environ', kwargs['env']):
                check(self.root, 'network:deploy')
                with self.assertRaises(ValueError):
                    check(self.root, 'download_karing')
            return SimpleNamespace(returncode=1, stdout='{"status":"failed"}')
        self.flow.run('server_deploy', runner=fail)
        self.assertEqual(self.flow.next()['stage'], 'server')
        self.assertIsNone(self.flow.state['execution'])
        with self.assertRaises(ValueError):
            check(self.root, 'network:deploy')

    def test_real_adapter_result_completes_only_server(self):
        self.reach('server')
        runner = lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(
            {'status': 'configured', 'node_file': '.local/network/node.txt'}))
        self.flow.run('server_deploy', runner=runner)
        self.assertEqual(self.flow.next()['stage'], 'computer_network')
        self.assertNotIn('browser', self.flow.state['records'])

    def test_probe_receipt_fills_only_measured_fields(self):
        self.reach('computer_network')
        runner = lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(
            {'status': 'passed', 'exit_matches': True, 'https_204': True}))
        self.flow.run('probe_proxy', runner=runner)
        self.assertEqual(self.flow.next()['observed'], {'http_proxy_ready': True})
        self.flow.run('probe_system', runner=runner)
        self.assertIn('codex_reply_received', self.flow.next()['missing'])
        self.assertEqual(self.flow.next()['stage'], 'computer_network')

    def test_interrupted_execution_resumes_same_stage(self):
        self.reach('server')
        self.flow.state['execution'] = {'action': 'server_deploy', 'token': 'stale'}
        self.flow.save()
        self.flow = Workflow(self.root, lambda: self.now); self.flow.sync()
        self.assertIsNone(self.flow.state['execution'])
        self.assertEqual(self.flow.next()['stage'], 'server')
        self.assertEqual(self.flow.state['history'][-1]['event'], 'interrupted')

    def test_windows_stage_does_not_offer_mac_download(self):
        self.computer = 'windows'
        self.reach('computer_network')
        self.assertNotIn('download_karing', self.flow.next()['allowed_actions'])
        with self.assertRaisesRegex(WorkflowError, 'action_out_of_stage'):
            self.flow.run('download_karing')

    def test_cleanup_scope_is_forwarded_without_auto_confirm(self):
        self.flow.submit(self.payload({'banned_login': 'yes'}))
        path = self.root/'options.json'; path.write_text('{"scope":["cache","account"]}')
        calls = []
        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return SimpleNamespace(returncode=0)
        with patch('workflow.sys.platform', 'win32'):
            self.flow.run('cleanup_apply', path, runner=runner)
        self.assertEqual(calls[0][0][-3:], ['--scope','cache','account'])
        self.assertFalse(calls[0][1]['capture_output'])
        self.assertNotIn('input', calls[0][1])
        self.assertEqual(self.flow.next()['stage'], 'cleanup')

    def test_windows_restore_batch_uses_existing_confirmation_flow(self):
        self.flow.submit(self.payload({'banned_login': 'yes'}))
        path = self.root/'restore.json'; path.write_text('{"backup_directory":"C:/Users/Test/ClaudeBackups/windows-cleanup/batch"}')
        calls = []
        def runner(command, **kwargs):
            calls.append(command)
            return SimpleNamespace(returncode=0)
        with patch('workflow.sys.platform', 'win32'):
            self.flow.run('cleanup_restore', path, runner=runner)
        self.assertEqual(calls[0][-2], '--restore')
        self.assertEqual(self.flow.next()['stage'], 'cleanup')

    def test_run_exception_revokes_permit(self):
        self.reach('server')
        def interrupted(*args, **kwargs):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.flow.run('server_deploy', runner=interrupted)
        self.assertIsNone(self.flow.state['execution'])

    def test_invalidated_stage_requires_new_probe_receipts(self):
        folder = self.root / '.local/network'; folder.mkdir()
        (folder / 'input.json').write_text('{"probe": {}}')
        self.flow.sync(); self.reach('computer_network')
        good = lambda *a, **kw: SimpleNamespace(returncode=0, stdout=json.dumps(
            {'status': 'passed', 'exit_matches': True, 'https_204': True}))
        self.flow.run('probe_proxy', runner=good); self.flow.run('probe_system', runner=good)
        self.advance()
        baseline = deepcopy(self.flow.state)
        for scope in ('computer', 'devices', 'network'):
            with self.subTest(scope=scope):
                self.flow.state = deepcopy(baseline)
                self.flow.invalidate(scope, 'configuration changed without editing network JSON')
                self.reach('computer_network'); self.flow.submit(self.payload())
                self.assertEqual(self.flow.next()['stage'], 'computer_network')
                self.assertEqual(self.flow.next()['missing'], ['probe_proxy', 'probe_system'])
                self.flow.run('probe_proxy', runner=good)
                self.assertEqual(self.flow.next()['missing'], ['probe_system'])
                self.flow.run('probe_system', runner=good)
                self.assertEqual(self.flow.next()['stage'], 'browser')

    def test_changed_browser_object_restarts_its_observations(self):
        self.reach('browser')
        data = self.data('browser'); data.pop('scores')
        self.flow.submit(self.payload(data))
        self.flow.submit(self.payload({'profile_ref': 'profile-b', 'checked_profile_ref': 'profile-b',
                                       'scores': self.data('browser')['scores']}))
        self.assertEqual(self.flow.next()['stage'], 'browser')
        for field in ('proxy_configured', 'dns_checked', 'ipv6_checked', 'https_ok'):
            self.assertIn(field, self.flow.next()['missing'])
        self.assertNotIn('https_ok', self.flow.next()['observed'])
        data.update(profile_ref='profile-b', checked_profile_ref='profile-b')
        self.flow.submit(self.payload(data))
        self.assertEqual(self.flow.next()['stage'], 'phone_proxy')

    def test_network_recheck_requires_new_server_readback(self):
        self.reach('server')
        good = lambda *a, **kw: SimpleNamespace(returncode=0, stdout=json.dumps(
            {'status': 'configured', 'node_file': '.local/network/node.txt'}))
        self.flow.run('server_deploy', runner=good)
        self.flow.invalidate('network', 'server service was stopped')
        data = self.data('server'); data['mode'] = 'scripted'
        self.flow.submit(self.payload(data))
        self.assertEqual(self.flow.next()['missing'], ['server_readback'])
        self.flow.run('server_deploy', runner=good)
        self.assertEqual(self.flow.next()['stage'], 'computer_network')

    def test_replacement_phone_rechecks_store_and_reuses_same_account_age(self):
        self.account_type = 'new'; self.reach(None)
        original = deepcopy(self.flow.state['records']['payment_preparation']['data'])
        self.flow.invalidate('phone', 'replacement iPhone')
        self.reach('payment_preparation')
        self.assertNotIn('store_signed_in', self.flow.next()['observed'])
        self.flow.submit(self.payload({'apple_account_ref': original['apple_account_ref']}))
        self.assertEqual(self.flow.next()['observed']['first_used_at'], original['first_used_at'])
        self.assertIn('store_signed_in', self.flow.next()['missing'])
        data = self.data('payment_preparation'); data.pop('account_type'); data.pop('first_used_at')
        self.flow.submit(self.payload(data))
        self.assertEqual(self.flow.next()['stage'], 'app')
        self.reach('subscription')
        self.assertIn('已有付款记录', self.flow.next()['next_action'])

    def test_replacement_phone_with_different_apple_account_starts_own_wait(self):
        self.account_type = 'new'; self.reach(None)
        self.flow.invalidate('phone', 'replacement iPhone with another Apple account')
        self.reach('payment_preparation')
        data = self.data('payment_preparation')
        data.update(apple_account_ref='apple-b', first_used_at=self.now.isoformat())
        self.flow.submit(self.payload(data))
        self.assertEqual(self.flow.next()['status'], 'waiting')
        self.assertEqual(self.flow.next()['resume_at'], (self.now + timedelta(hours=48)).isoformat())

    def test_apple_account_change_during_partial_stage_clears_old_store_facts(self):
        self.reach('payment_preparation')
        data = self.data('payment_preparation'); data.pop('payment_ready')
        self.flow.submit(self.payload(data))
        self.flow.submit(self.payload({'apple_account_ref': 'apple-b', 'payment_ready': True}))
        self.assertEqual(self.flow.next()['stage'], 'payment_preparation')
        self.assertIn('store_signed_in', self.flow.next()['missing'])
        self.assertIn('account_type', self.flow.next()['missing'])

    def test_correct_new_account_to_longstanding_leaves_wait(self):
        self.account_type = 'new'; self.first_used_at = self.now
        self.reach('payment_preparation'); self.advance()
        self.assertEqual(self.flow.next()['status'], 'waiting')
        self.flow.submit(self.payload({'account_type': 'longstanding'}))
        self.assertEqual(self.flow.next()['stage'], 'app')
        self.assertNotIn('first_used_at', self.flow.state['records']['payment_preparation']['data'])

    def test_correct_longstanding_account_to_new_requires_start_time(self):
        self.reach('payment_preparation')
        data = self.data('payment_preparation'); data['payment_ready'] = False
        self.flow.submit(self.payload(data))
        self.flow.submit(self.payload({'account_type': 'new', 'payment_ready': True}))
        self.assertEqual(self.flow.next()['missing'], ['apple_reminder_shown', 'first_used_at'])
        self.flow.submit(self.payload({'first_used_at': self.now.isoformat(), 'apple_reminder_shown': True}))
        self.assertEqual(self.flow.next()['status'], 'waiting')


class WorkflowCLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        source = Path(__file__).resolve().parents[1] / 'scripts'
        shutil.copytree(source, self.root / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))

    def cli(self, script, *args, code=0):
        result = subprocess.run([sys.executable, str(self.root/'scripts'/script), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_cli_init_resume_and_legacy_checker_use_one_stage(self):
        first = self.cli('workflow.py', 'init')
        self.assertEqual(first['stage'], 'intake')
        self.assertEqual(self.cli('workflow.py', 'next')['ticket'], first['ticket'])
        self.assertEqual(self.cli('login_readiness.py')['stage'], 'intake')
        payload = first['submission']; payload.update(data={'banned_login': 'no'}, source={'kind': 'user', 'reference': 'customer explicitly said no'})
        path = self.root/'observation.json'; path.write_text(json.dumps(payload))
        self.assertEqual(self.cli('workflow.py', 'submit', '--input', str(path))['stage'], 'devices')
        self.assertEqual(self.cli('workflow.py', 'init')['stage'], 'devices')

    def test_direct_network_and_download_commands_use_controller(self):
        self.cli('workflow.py', 'init')
        result = self.cli('network.py', 'deploy', code=1)
        self.assertEqual(result['status'], 'failed')
        result = self.cli('download_karing.py', code=1)
        self.assertEqual(result['status'], 'failed')
        self.assertFalse((self.root/'.local/downloads').exists())

    def test_controller_invokes_real_network_cli_with_fake_ssh_boundary(self):
        # Real workflow -> permission guard -> network CLI -> isolated SSH fixture.
        from test_network_workflow import SSH_FIXTURE
        flow_test = WorkflowTests(methodName='test_full_mac_iphone_delivery_exact_order')
        flow_test.setUp()
        self.addCleanup(flow_test.doCleanups)
        flow_test.root = self.root
        flow_test.flow = Workflow(self.root, lambda: flow_test.now)
        flow_test.flow.init(); flow_test.reach('server')
        private = self.root / '.local/network'; private.mkdir()
        (private/'input.json').write_text(json.dumps({'context':'integration',
            'ssh':{'host':'203.0.113.10','user':'root'},
            'server':{'address':'203.0.113.10','port':443,'panel_port':18899,'sni':'www.cloudflare.com'}}))
        fixture = self.root/'fixture'; fixture.mkdir()
        executable = fixture/'ssh'; executable.write_text('#!'+sys.executable+'\n'+SSH_FIXTURE); executable.chmod(0o700)
        import os
        with patch.dict(os.environ, {'PATH':str(fixture)+os.pathsep+os.environ['PATH'], 'WORKFLOW_FIXTURE':str(fixture)}):
            result = self.cli('workflow.py', 'run', '--action', 'server_deploy')
        self.assertTrue(result['execution']['success'])
        self.assertEqual(result['workflow']['stage'], 'computer_network')
        self.assertEqual((fixture/'calls').read_text().splitlines(), ['deploy', 'verify'])
        self.assertTrue((private/'node.txt').exists())
        self.assertNotIn('fixture-secret', json.dumps(result))
        self.assertEqual(self.cli('workflow.py','next')['stage'], 'computer_network')

    def test_live_lock_returns_busy_without_a_traceback(self):
        from network import lock
        self.cli('workflow.py', 'init')
        with lock(self.root/'.local/workflow'):
            result = self.cli('workflow.py','next',code=2)
        self.assertEqual(result['error'], 'execution_busy')

    def test_direct_platform_cleanup_uses_controller_before_reading_home(self):
        self.cli('workflow.py', 'init')
        result = self.cli('cleanup_windows.py', '--audit', code=1)
        self.assertIn('统一流程已启用', result['error'])
        script = self.root/'scripts/vendor/mac_cleanup/claude_cleanup.py'
        result = subprocess.run([sys.executable, str(script), '--audit'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('统一流程已启用', result.stderr)
        self.assertEqual(result.stdout, '')

    def test_early_script_action_rejected_without_network(self):
        self.cli('workflow.py', 'init')
        result = self.cli('workflow.py', 'run', '--action', 'server_deploy', code=2)
        self.assertIn('action_out_of_stage', result['error'])


if __name__ == '__main__':
    unittest.main()
