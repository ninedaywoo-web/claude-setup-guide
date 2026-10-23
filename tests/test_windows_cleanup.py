import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import cleanup_windows as w


class WindowsCleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve(); self.roaming = self.home/'AppData/Roaming'; self.local = self.home/'AppData/Local'
        (self.home/'.claude/cache').mkdir(parents=True)
        (self.home/'.claude/cache/a').write_text('cache')
        (self.home/'.claude/skills').mkdir(); (self.home/'.claude/skills/keep').write_text('skill')
        (self.home/'.claude.json').write_text(json.dumps({'userID': 'old-id', 'oauthAccount': {'secret': 'token'}, 'projects': {'mine': {}}, 'mcpServers': {'keep': True}}))
        (self.home/'.claude/.credentials.json').write_text(json.dumps({'claudeAiOauth': {'secret': 'token'}, 'pluginSecrets': {'keep': 'yes'}, 'mcpOAuth': 'keep'}))
        self.batch = self.home/'backup'

    def plan(self, *scopes):
        return w.plan(self.home, self.roaming, self.local, scopes)

    def apply(self, p):
        return w.apply(p, self.batch, check=lambda: None, secure=lambda p: None)

    def test_selected_cleanup_preserves_assets_and_restores_exact_bytes(self):
        before = {p: p.read_bytes() for p in [self.home/'.claude.json', self.home/'.claude/.credentials.json']}
        result = self.apply(self.plan('cache', 'account', 'credentials'))
        self.assertEqual(result['status'], 'completed')
        self.assertFalse((self.home/'.claude/cache').exists())
        self.assertEqual((self.home/'.claude/skills/keep').read_text(), 'skill')
        self.assertEqual(json.loads((self.home/'.claude.json').read_text()), {'projects': {'mine': {}}, 'mcpServers': {'keep': True}})
        self.assertEqual(json.loads((self.home/'.claude/.credentials.json').read_text()), {'pluginSecrets': {'keep': 'yes'}, 'mcpOAuth': 'keep'})
        w.restore(self.batch, check=lambda:None)
        w.restore(self.batch, check=lambda:None)
        for p, content in before.items(): self.assertEqual(p.read_bytes(), content)
        self.assertEqual((self.home/'.claude/cache/a').read_text(), 'cache')

    def test_changed_plan_fails_before_backup(self):
        p = self.plan('account'); (self.home/'.claude.json').write_text('{"new":"data"}')
        with self.assertRaisesRegex(w.Failure, 'rescan'): self.apply(p)
        self.assertFalse(self.batch.exists())

    def test_backup_failure_never_mutates_original(self):
        p = self.plan('cache', 'account')
        with patch.object(w, 'copy', side_effect=OSError('full disk')):
            with self.assertRaises(OSError): self.apply(p)
        self.assertTrue((self.home/'.claude/cache/a').exists())
        self.assertIn('userID', json.loads((self.home/'.claude.json').read_text()))

    def test_partial_apply_can_restore(self):
        p = self.plan('cache', 'account')
        original = w.transform
        calls = 0
        def fail(text, scope):
            raise OSError('interrupted before edit')
        with patch.object(w, 'transform', side_effect=fail):
            with self.assertRaises(OSError): self.apply(p)
        self.assertFalse((self.home/'.claude/cache').exists())
        w.restore(self.batch, check=lambda:None)
        self.assertEqual((self.home/'.claude/cache/a').read_text(), 'cache')

    def test_restore_refuses_new_user_data(self):
        self.apply(self.plan('account'))
        (self.home/'.claude.json').write_text('{"new":"keep me"}')
        with self.assertRaisesRegex(w.Failure, 'new_data'): w.restore(self.batch, check=lambda:None)
        self.assertEqual((self.home/'.claude.json').read_text(), '{"new":"keep me"}')

    def test_interrupted_directory_restore_can_retry(self):
        (self.home/'.claude/cache/b').write_text('second file')
        self.apply(self.plan('cache'))
        def interrupted(source, target):
            target.mkdir(); shutil.copy2(source/'a', target/'a')
            raise OSError('interrupted during directory copy')
        with patch.object(w, 'copy', side_effect=interrupted):
            with self.assertRaises(OSError): w.restore(self.batch, check=lambda:None)
        self.assertFalse((self.home/'.claude/cache').exists())
        w.restore(self.batch, check=lambda:None)
        self.assertEqual((self.home/'.claude/cache/a').read_text(), 'cache')
        self.assertEqual((self.home/'.claude/cache/b').read_text(), 'second file')
        self.assertEqual(json.loads((self.batch/'manifest.json').read_text())['status'], 'restored')

    def test_restore_corrupt_staging_never_publishes_partial_directory(self):
        self.apply(self.plan('cache'))
        def corrupt(source, target):
            target.mkdir(); (target/'a').write_text('bad copy')
        with patch.object(w, 'copy', side_effect=corrupt):
            with self.assertRaisesRegex(w.Failure, 'restore_verification_failed'):
                w.restore(self.batch, check=lambda:None)
        self.assertFalse((self.home/'.claude/cache').exists())
        w.restore(self.batch, check=lambda:None)
        self.assertEqual((self.home/'.claude/cache/a').read_text(), 'cache')

    def test_restore_keeps_new_data_created_during_staging(self):
        self.apply(self.plan('cache'))
        original = w.copy
        def concurrent_write(source, target):
            original(source, target)
            dest = self.home/'.claude/cache'; dest.mkdir(); (dest/'new').write_text('keep')
        with patch.object(w, 'copy', side_effect=concurrent_write):
            with self.assertRaisesRegex(w.Failure, 'new_data_refuse_restore'):
                w.restore(self.batch, check=lambda:None)
        self.assertEqual((self.home/'.claude/cache/new').read_text(), 'keep')

    def test_restore_retries_after_publish_before_journal_save(self):
        self.apply(self.plan('cache'))
        original = w.save
        def interrupted(path, data):
            if data.get('restore_completed'): raise OSError('interrupted after rename')
            original(path, data)
        with patch.object(w, 'save', side_effect=interrupted):
            with self.assertRaises(OSError): w.restore(self.batch, check=lambda:None)
        w.restore(self.batch, check=lambda:None)
        self.assertEqual((self.home/'.claude/cache/a').read_text(), 'cache')

    def test_links_and_nested_links_are_refused(self):
        (self.home/'.claude/cache/link').symlink_to(self.home/'.claude/skills', target_is_directory=True)
        with self.assertRaisesRegex(w.Failure, 'linked'): self.plan('cache')

    def test_unknown_target_and_malformed_json_fail_closed(self):
        p = self.plan('account'); p['entries'][0]['path'] = str(self.home/'.claude/skills/keep')
        with self.assertRaises(w.Failure): self.apply(p)
        (self.home/'.claude.json').write_text('{bad')
        with self.assertRaises(ValueError): self.plan('account')

    def test_scopes_do_not_expand_or_overlap(self):
        root = self.roaming/'Claude/Service Worker/CacheStorage'; root.mkdir(parents=True); (root/'a').write_text('a')
        p = self.plan('cache', 'desktop')
        paths = [e['path'] for e in p['entries']]
        self.assertIn(str(root.parent), paths); self.assertNotIn(str(root), paths)
        self.assertNotIn(str(self.home/'.claude.json'), paths)

    def test_restore_entrypoint_with_chinese_paths_and_legacy_windows_encoding(self):
        home = self.home/'客户目录'
        cache = home/'.claude/cache'
        cache.mkdir(parents=True)
        (cache/'记录.txt').write_text('恢复内容', encoding='utf-8')
        roaming, local = home/'AppData/Roaming', home/'AppData/Local'
        batch = home/'ClaudeBackups/windows-cleanup/test-batch'
        p = w.plan(home, roaming, local, ['cache'])
        w.apply(p, batch, check=lambda:None, secure=lambda p:None)
        original_read = Path.read_text

        def windows_read(path, encoding=None, errors=None):
            return original_read(path, encoding=encoding or 'cp1252', errors=errors)

        output = io.StringIO()
        with patch.object(sys, 'platform', 'win32'), \
             patch.object(Path, 'home', return_value=home), \
             patch.object(Path, 'read_text', windows_read), \
             patch.dict(os.environ, {'APPDATA':str(roaming), 'LOCALAPPDATA':str(local)}), \
             patch.object(sys, 'argv', ['cleanup.py', '--restore', str(batch)]), \
             patch.object(sys.stdin, 'isatty', return_value=True), \
             patch('builtins.input', return_value='CONFIRM'), \
             patch.object(w.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)), \
             contextlib.redirect_stdout(output):
            self.assertEqual(w.main(), 0, output.getvalue())
        self.assertEqual((cache/'记录.txt').read_text(encoding='utf-8'), '恢复内容')


if __name__ == '__main__': unittest.main()
