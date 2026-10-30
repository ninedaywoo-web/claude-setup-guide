"""Require the active controller's execution permit at bundled CLI boundaries."""
import json
import os
from pathlib import Path


PERMITS = {
    'vps:capture': ('vps_capture',),
    'cleanup:audit': ('cleanup_audit',), 'cleanup:apply': ('cleanup_apply',),
    'cleanup:restore': ('cleanup_restore',),
    'download_karing': ('download_karing',),
    'network:preflight': ('server_preflight',), 'network:deploy': ('server_deploy',),
    'network:export': ('server_export',), 'network:probe:proxy': ('probe_proxy',),
    'network:probe:system': ('probe_system',), 'network:scores': ('browser_scores', 'phone_scores'),
}


def check(root, operation):
    path = Path(root) / '.local/workflow/state.json'
    if not path.exists():
        return  # Standalone helpers remain usable in existing installations.
    state = json.loads(path.read_text(encoding='utf-8'))
    execution = state.get('execution') or {}
    token = os.environ.get('CLAUDE_SETUP_WORKFLOW_TOKEN')
    if not token or token != execution.get('token') or execution.get('action') not in PERMITS.get(operation, ()):
        raise ValueError('统一流程已启用；运行 scripts/workflow.py next，再通过 run 执行当前阶段动作。')
