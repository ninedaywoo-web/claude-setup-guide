#!/usr/bin/env python3
"""Local delivery controller: ordered observations, execution and recovery."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

from network import lock, private_file
from network_server import Failure
from workflow_messages import customer_output
from workflow_definition import ACTIONS, DEVICE_GUIDANCE, INVALIDATES, OBJECT_FIELDS, catalog, facts, validation

ROOT = Path(__file__).resolve().parents[1]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


class WorkflowError(ValueError):
    pass


class Workflow:
    def __init__(self, root, clock=None):
        self.root = Path(root)
        self.folder = self.root / '.local/workflow'
        self.path = self.folder / 'state.json'
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.state = read(self.path) if self.path.exists() else None
        if self.state is not None and self.state.get('schema') != 1:
            raise WorkflowError('workflow_schema_unsupported')

    def signature(self):
        config = self.root / '.local/network/input.json'
        state = self.root / '.local/network/state.json'
        # Include configuration content and the helper generation, never credentials.
        configuration = read(config) if config.exists() else {}
        server_config = {key: value for key, value in configuration.items() if key != 'probe'}
        return {'config': digest(configuration) if config.exists() else None,
                'server': digest(server_config) if server_config else None,
                'generation': read(state).get('generation') if state.exists() else None}

    def init(self):
        if self.state is None:
            version = self.root / 'version.json'
            self.state = {'schema': 1, 'session': str(uuid.uuid4()), 'revision': 0,
                          'project_version': read(version)['version'] if version.exists() else 'local',
                          'records': {}, 'history': [], 'submissions': {}, 'receipts': [],
                          'stage_generations': {}, 'apple_accounts': {},
                          'network_signature': self.signature(), 'execution': None}
            self.save()
            legacy = self.root / '.local/progress.md'
            marker = '<!-- unified-workflow -->'
            content = legacy.read_text(encoding='utf-8') if legacy.exists() else ''
            if marker not in content:
                private_file(legacy, content + '\n\n' + marker + '\n当前阶段与下一步见 [统一流程进度](workflow/progress.md)。本文件保留历史观察与说明。\n')
        return self.next()

    def require_state(self):
        if self.state is None:
            raise WorkflowError('先运行 python3 scripts/workflow.py init')

    def append(self, event, **details):
        self.state['history'].append({'event': event, 'at': self.clock().isoformat(), **details})
        self.state['revision'] += 1

    def invalidate(self, scope, reason):
        self.require_state()
        if scope not in INVALIDATES or not isinstance(reason, str) or not reason.strip():
            raise WorkflowError('提供有效变更范围和具体原因')
        previous = {key: self.state['records'].pop(key) for key in INVALIDATES[scope]
                    if key in self.state['records']}
        generations = self.state.setdefault('stage_generations', {})
        for key in INVALIDATES[scope]:
            generations[key] = generations.get(key, 0) + 1
        self.append('changed', scope=scope, reason=reason, previous=previous)
        self.state['execution'] = None
        self.state['network_signature'] = self.signature()
        self.save()
        return self.next()

    def sync(self):
        self.require_state()
        changed = self.signature()
        old = self.state['network_signature']
        if 'server' not in old and changed['config'] == old['config']:
            # An unchanged legacy config lets us migrate its server receipts in place.
            old['server'] = changed['server']
            for receipt in self.state['receipts']:
                signature = receipt.get('network_signature', {})
                if signature.get('config') == old['config']:
                    signature['server'] = changed['server']
            self.save()
        if changed != self.state['network_signature']:
            old = self.state['network_signature']
            server_changed = (changed['server'] != old['server']) if 'server' in old else (changed['config'] != old['config'])
            scope = 'network' if server_changed else 'handoff'
            self.invalidate(scope, '网络配置或检测代次变化，复查受影响步骤')
        if self.state.get('execution'):
            # CLI holds the workflow lock during execution. Reacquiring it means
            # the old controller stopped; never repeat a payment or UI mutation.
            operation = self.state['execution']
            self.state['execution'] = None
            self.append('interrupted', action=operation['action'])
            self.save()

    def checked(self, stage, data):
        result = validation(stage, data, self.state, self.clock())
        missing = list(result.get('missing', []))
        required = []
        if stage['id'] == 'server' and data.get('mode') == 'scripted':
            required = [('server_readback', ('server_deploy', 'server_export'))]
        config_path = self.root / '.local/network/input.json'
        if stage['id'] == 'computer_network' and config_path.exists() and 'probe' in read(config_path):
            required = [('probe_proxy', ('probe_proxy',)), ('probe_system', ('probe_system',))]
        for name, actions in required:
            receipt = next((item for item in reversed(self.state['receipts'])
                            if item['action'] in actions
                            and item.get('stage_generation', 0) == self.state.get('stage_generations', {}).get(stage['id'], 0)
                            and (item.get('network_signature', {}).get('server', item.get('network_signature', {}).get('config')) == self.state['network_signature'].get('server', self.state['network_signature']['config'])
                                 if stage['id'] == 'server' else item.get('network_signature') == self.state['network_signature'])), None)
            valid = bool(receipt and receipt['success'])
            if valid:
                output = receipt['result']
                valid = (output.get('status') in ('configured', 'exported') and bool(output.get('node_file'))) if name == 'server_readback' else (
                    output.get('status') == 'passed' and output.get('exit_matches') is True and output.get('https_204') is True)
            if not valid:
                missing.append(name)
        if missing:
            return {**result, 'valid': False, 'missing': sorted(set(missing))}
        return result

    def projection(self):
        self.require_state()
        current = None
        progress = []
        for stage in catalog(self.state):
            record = self.state['records'].get(stage['id'])
            checked = self.checked(stage, record['data'] if record else {})
            status = ('waiting' if checked.get('waiting_until') else 'complete') if checked['valid'] else 'pending'
            if current is not None and status == 'complete':
                status = 'retained'
            progress.append({'stage': stage['id'], 'status': status})
            if current is None and status != 'complete':
                current = (stage, checked)
        if current is None:
            return customer_output({'status': 'complete', 'stage': None, 'next_action': '手机订单与当前账号 Pro 权益已确认，交付完成。',
                    'progress': progress}, self.state, self.clock())
        stage, checked = current
        ticket = digest([self.state['session'], self.state['revision'], stage['id']])
        previous = None
        for event in reversed(self.state['history']):
            if stage['id'] in event.get('previous', {}):
                previous = event['previous'][stage['id']]['data']
                break
        fields = dict(stage['fields'])
        example = {}
        for key, rule in fields.items():
            if key not in checked.get('missing', []):
                continue
            if rule == 'scores':
                example[key] = {site: {'value': None, 'result': ''} for site in ('netcoffee', 'ping0', 'scamalytics')}
            else:
                example[key] = None
        result = {'status': 'waiting' if checked.get('waiting_until') else 'active',
                  'stage': stage['id'], 'next_action': stage['title'], 'reference': stage['reference'],
                  'ticket': ticket, 'required_fields': fields, 'missing': checked.get('missing', []),
                  'observed': facts(self.state, stage['id']), 'previous_observation': previous,
                  'submission': {'stage': stage['id'], 'ticket': ticket,
                                 'source': {'kind': 'tool', 'reference': ''}, 'data': example},
                  'allowed_actions': [key for key, (owner, _) in ACTIONS.items()
                                      if owner == stage['id']
                                      and (key != 'download_karing' or facts(self.state, 'devices').get('computer') == 'mac')
                                      and (key != 'cleanup_restore' or sys.platform == 'win32')],
                  'progress': progress}
        if 'score_advice' in checked:
            result['score_advice'] = checked['score_advice']
        if stage['id'] == 'devices' and facts(self.state, 'devices').get('setup_explained') is not True:
            result['customer_message'] = DEVICE_GUIDANCE
            result['next_action'] = ('确认电脑和手机类型后，在对话中展示 customer_message 的设备搭配说明；'
                                     '展示后提交 setup_explained=true，再继续阅读版介绍和账号准备。')
        if stage['id'] == 'payment_preparation' and facts(self.state, 'devices').get('phone') != 'android':
            result['conditional_fields'] = {'account_type=new': {'first_used_at': 'timestamp'}}
            result['account_history'] = self.state.get('apple_accounts', {})
        if checked.get('waiting_until'):
            result.update(resume_at=checked['waiting_until'], next_action='保留已记录的首次使用时间，到期运行 next 后继续。', allowed_actions=[])
        if stage['id'] == 'subscription' and previous and previous.get('order_confirmed'):
            result['next_action'] = '已有付款记录；核对当前账号订单与权益，先恢复权益，避免重复付款。'
        return customer_output(result, self.state, self.clock())

    def next(self):
        return self.projection()

    def save(self):
        private_file(self.path, json.dumps(self.state, ensure_ascii=False, indent=2) + '\n')
        view = self.projection()
        lines = ['# 统一流程进度', '', '状态：' + view['status'], '下一步：' + view['next_action'], '']
        lines += ['- ' + item['stage'] + '：' + item['status'] for item in view['progress']]
        private_file(self.folder / 'progress.md', '\n'.join(lines) + '\n')

    def submit(self, payload):
        self.require_state()
        if not isinstance(payload, dict) or set(payload) != {'stage', 'ticket', 'source', 'data'}:
            raise WorkflowError('提交 stage、ticket、source 和 data 的具体观察')
        if not isinstance(payload['ticket'], str) or not isinstance(payload['stage'], str):
            raise WorkflowError('stage 和 ticket 使用当前 next 返回的字符串')
        previous = self.state['submissions'].get(payload['ticket'])
        if previous:
            if previous == digest(payload):
                return self.next()
            raise WorkflowError('ticket_already_used')
        view = self.next()
        if payload['stage'] != view['stage'] or payload['ticket'] != view.get('ticket'):
            raise WorkflowError('stage_or_ticket_mismatch: ' + str(view['stage']))
        source, data = payload['source'], payload['data']
        if not isinstance(source, dict) or set(source) != {'kind', 'reference'} or source.get('kind') not in ('tool', 'user', 'legacy') or not isinstance(source.get('reference'), str) or not source['reference'].strip():
            raise WorkflowError('记录当前工具页面、回执或用户具体反馈的来源')
        if not isinstance(data, dict) or not data:
            raise WorkflowError('提供本阶段的实际观察字段')
        stage = next(s for s in catalog(self.state) if s['id'] == view['stage'])
        existing = facts(self.state, view['stage'])
        object_field = OBJECT_FIELDS.get(view['stage'])
        if object_field in data and object_field in existing and data[object_field] != existing[object_field]:
            existing = {}
        if data.get('wait_choice') == 'continue' and source['kind'] != 'user':
            raise WorkflowError('立即继续需记录客户明确选择，source.kind=user')
        if data.get('score_review') == 'continue' and source['kind'] != 'user':
            raise WorkflowError('继续使用偏离结果需记录客户选择，source.kind=user')
        if view['stage'] in ('browser', 'phone_network') and 'scores' in data and data['scores'] != existing.get('scores'):
            existing = {k: v for k, v in existing.items() if k not in ('score_review', 'score_review_note')}
        if view['stage'] == 'devices' and any(k in data and k in existing and data[k] != existing[k] for k in ('computer', 'phone')):
            existing = {k: v for k, v in existing.items() if k not in ('setup_explained', 'android_route_explained', 'payment_route_status')}
        merged = {**existing, **data}
        if view['stage'] == 'devices' and merged.get('phone') != 'android':
            merged.pop('android_route_explained', None)
            merged.pop('payment_route_status', None)
        if view['stage'] in ('payment_preparation', 'phone_proxy') and facts(self.state, 'devices').get('phone') != 'android':
            account_ref = merged.get('apple_account_ref')
            history = self.state.get('apple_accounts', {}).get(account_ref, {}) if isinstance(account_ref, str) else {}
            merged = {**history, **merged}
            if merged.get('account_type') == 'longstanding':
                merged.pop('first_used_at', None)
        checked = self.checked(stage, merged)
        if any(name.startswith('unknown:') for name in checked.get('missing', [])):
            raise WorkflowError('unknown_observation_fields')
        record = self.state['records'].setdefault(view['stage'], {'data': {}, 'observations': []})
        record['data'] = merged
        record['observations'].append({'source': source, 'data': data, 'at': self.clock().isoformat()})
        if view['stage'] in ('payment_preparation', 'phone_proxy') and isinstance(merged.get('apple_account_ref'), str) and merged['apple_account_ref'].strip():
            if merged.get('store_signed_in') is True and 'first_used_at' not in checked.get('missing', []):
                self.state.setdefault('apple_accounts', {})[merged['apple_account_ref']] = {
                    key: merged[key] for key in ('account_type', 'first_used_at', 'apple_reminder_shown', 'wait_choice',
                                                 'purchase_restricted', 'support_case', 'support_retry_at') if key in merged}
            elif isinstance(merged.get('purchase_restricted'), bool):
                account = self.state.setdefault('apple_accounts', {}).setdefault(merged['apple_account_ref'], {})
                account.update({key: merged[key] for key in ('purchase_restricted', 'support_case', 'support_retry_at') if key in merged})
        self.state['submissions'][payload['ticket']] = digest(payload)
        self.append('observed', stage=view['stage'], valid=checked['valid'])
        self.save()
        return self.next()

    def run(self, action, input_path=None, runner=None):
        view = self.next()
        if action not in view.get('allowed_actions', []):
            raise WorkflowError('action_out_of_stage: ' + str(view['stage']))
        _, args = ACTIONS[action]
        args = list(args)
        if action == 'cleanup_apply':
            args.append('--apply')
        if action == 'cleanup_restore':
            if input_path is None:
                raise WorkflowError('提供 Windows 恢复批次的 backup_directory 输入')
            options = read(Path(input_path))
            if not isinstance(options, dict) or set(options) != {'backup_directory'} or not isinstance(options['backup_directory'], str) or not options['backup_directory'].strip():
                raise WorkflowError('提供实际 backup_directory')
            args += ['--restore', options['backup_directory']]
        elif action.startswith('cleanup_') and input_path is not None:
            options = read(Path(input_path))
            scopes = options.get('scope') if isinstance(options, dict) else None
            if not isinstance(options, dict) or set(options) != {'scope'} or not isinstance(scopes, list) or not scopes or any(s not in ('cache', 'account', 'credentials', 'desktop') for s in scopes):
                raise WorkflowError('填写 Windows 清理 scope 列表')
            if facts(self.state, 'devices').get('computer') != 'windows' and sys.platform != 'win32':
                raise WorkflowError('Mac 清理范围在原交互清单选择')
            args += ['--scope', *scopes]
        if action.endswith('_scores'):
            if input_path is None:
                raise WorkflowError('scores_input_required')
            path = Path(input_path).resolve()
            if (self.root / '.local').resolve() not in path.parents:
                raise WorkflowError('scores_input_must_be_private')
            environment = read(path).get('environment')
            phone = facts(self.state, 'devices').get('phone')
            environments = ('android_wifi', 'android_cellular') if phone == 'android' else ('iphone_wifi', 'iphone_cellular')
            allowed = ('adspower',) if action == 'browser_scores' else environments
            if environment not in allowed:
                raise WorkflowError('score_environment_mismatch')
            args += ['--input', str(path)]
        token = str(uuid.uuid4())
        self.state['execution'] = {'action': action, 'token': token, 'pid': os.getpid()}
        self.save()
        command = [sys.executable, str(self.root / 'scripts' / args[0]), *args[1:]]
        env = dict(os.environ, CLAUDE_SETUP_WORKFLOW_TOKEN=token)
        interactive = action.startswith('cleanup_')
        try:
            output = (runner or subprocess.run)(command, env=env, text=True, capture_output=not interactive)
            if interactive:
                result = {'status': 'finished' if output.returncode == 0 else 'failed', 'exit_code': output.returncode}
            else:
                try:
                    result = json.loads(output.stdout)
                except (ValueError, TypeError):
                    result = {'status': 'failed', 'error': 'script_output_unavailable'}
            success = output.returncode == 0 and result.get('status') not in ('failed', 'interrupted')
        except BaseException:
            self.state['execution'] = None
            self.state['network_signature'] = self.signature()
            self.append('interrupted', action=action)
            self.save()
            raise
        self.state['execution'] = None
        self.state['network_signature'] = self.signature()
        receipt = {'id': str(uuid.uuid4()), 'action': action, 'at': self.clock().isoformat(),
                   'success': success, 'result': result,
                   'stage_generation': self.state.get('stage_generations', {}).get(ACTIONS[action][0], 0),
                   'network_signature': deepcopy(self.state['network_signature'])}
        self.state['receipts'].append(receipt)
        self.append('executed', action=action, success=success)
        self.save()
        if success and action in ('server_deploy', 'server_export'):
            expected = 'configured' if action == 'server_deploy' else 'exported'
            if result.get('status') == expected and result.get('node_file') and self.next()['stage'] == 'server':
                view = self.next()
                self.submit({'stage': 'server', 'ticket': view['ticket'],
                             'source': {'kind': 'tool', 'reference': 'workflow receipt ' + receipt['id']},
                             'data': {'mode': 'scripted', 'service_running': True, 'node_exported': True, 'parameters_checked': True}})
        elif success and action in ('probe_proxy', 'probe_system'):
            if result.get('status') == 'passed' and result.get('exit_matches') is True and result.get('https_204') is True and self.next()['stage'] == 'computer_network':
                view = self.next()
                data = {'http_proxy_ready': True} if action == 'probe_proxy' else {'exit_matches': True, 'https_ok': True}
                self.submit({'stage': 'computer_network', 'ticket': view['ticket'],
                             'source': {'kind': 'tool', 'reference': 'workflow receipt ' + receipt['id']}, 'data': data})
        return {'execution': receipt, 'workflow': self.next()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('init', 'next', 'status', 'submit', 'run', 'change'))
    parser.add_argument('--input', type=Path)
    parser.add_argument('--action', dest='script_action', choices=tuple(ACTIONS))
    parser.add_argument('--scope', choices=tuple(INVALIDATES))
    parser.add_argument('--reason')
    args = parser.parse_args()
    try:
        with lock(ROOT / '.local/workflow'):
            workflow = Workflow(ROOT)
            if args.action == 'init':
                workflow.init()
            workflow.sync()
            if args.action == 'submit':
                if args.input is None:
                    raise WorkflowError('submission_input_required')
                result = workflow.submit(read(args.input))
            elif args.action == 'run':
                result = workflow.run(args.script_action, args.input)
            elif args.action == 'change':
                result = workflow.invalidate(args.scope, args.reason)
            else:
                result = workflow.next()
                workflow.save()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(args.action == 'run' and not result['execution']['success'])
    except (ValueError, OSError, KeyError, Failure) as exc:
        print(json.dumps({'status': 'needs_action', 'error': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
