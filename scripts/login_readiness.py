#!/usr/bin/env python3
"""Choose the next pre-login action from observed device setup results."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def requirements(computer, phone):
    if computer not in ('mac', 'windows') or phone not in ('iphone', 'ipad'):
        raise ValueError('本脚本用于 Mac／Windows + iPhone／iPad；其他设备按对应专章继续。')
    checks = [
        ('computer_network', '完成电脑网络验收'),
        ('browser_network', '完成 AdsPower 网络验收'),
        ('phone_proxy', '手机导入同一节点，开启全局代理与 VPN'),
        ('computer_timezone_auto_off', '电脑关闭自动设置时区'),
        ('computer_location_off', '电脑关闭定位服务总开关'),
        ('computer_timezone_matches_choice', '电脑手动时区符合所选时区（节点城市或台北），并返回设置页复查'),
    ]
    if computer == 'mac':
        checks += [
            ('computer_timezone_location_off', 'Mac 系统服务“设定时区”关闭或随定位总开关停用'),
        ]
    checks += [
        ('phone_timezone_auto_off', '手机关闭日期与时间中的“自动设置”'),
        ('phone_timezone_matches_choice', '手机手动时区符合所选时区（节点城市或台北），并返回设置页复查'),
        ('phone_timezone_location_off', '手机系统服务“设定时区”关闭或随定位总开关停用'),
        ('phone_location_off', '手机关闭定位服务总开关'),
        ('browser_timezone_matches_choice', 'AdsPower 实际时区符合所选时区（节点城市或台北）'),
        ('browser_geolocation_denied', 'AdsPower 地理位置设为“禁止”'),
        ('phone_network', '完成手机登录前网络验收'),
    ]
    return checks


def template(computer, phone):
    checks = {}
    for key, _ in requirements(computer, phone):
        checks[key] = {'status': 'pending', 'result': ''}
        if key.endswith('_timezone_matches_choice'):
            checks[key]['timezone'] = ''
    return {'computer': computer, 'phone': phone,
            'timezone_choice': '', 'target_timezone': '', 'checks': checks}


def evaluate(record):
    required = requirements(record.get('computer'), record.get('phone'))
    checks = record.get('checks', {})
    if not isinstance(checks, dict):
        raise ValueError('checks 应为逐项检查记录。')
    pending = []
    choice = record.get('timezone_choice')
    target = record.get('target_timezone')
    if choice not in ('node', 'taipei'):
        pending.append({'id': 'timezone_choice',
                        'action': '询问一次时区选择：跟随节点（程序和作者推荐）／台北；电脑和手机都设置。'})
    elif not isinstance(target, str) or not target.strip() or (choice == 'taipei' and target != 'Asia/Taipei'):
        pending.append({'id': 'target_timezone',
                        'action': '记录所选城市的 IANA 时区；台北使用 Asia/Taipei，节点方案读取实际节点城市。'})
    for key, action in required:
        item = checks.get(key, {})
        complete = isinstance(item, dict) and item.get('status') == 'passed'
        if complete and key.endswith('_timezone_matches_choice'):
            complete = bool(target) and item.get('timezone') == target
        if not complete:
            pending.append({'id': key, 'action': action})
    return {'status': 'needs_setup' if pending else 'ready',
            'scope': 'pre_login_environment',
            'pending': pending,
            'next_action': pending[0]['action'] if pending else
            '核对美区 Apple ID 和养号完成记录；就绪后保持手机节点开启，下载 Claude，Google 登录并订阅 Pro。订单和手机权益确认后结束交付。'}


def main():
    if (ROOT / '.local/workflow/state.json').exists():
        from network import lock
        from workflow import Workflow
        with lock(ROOT / '.local/workflow'):
            workflow = Workflow(ROOT)
            workflow.sync()
            result = workflow.next()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / '.local/login-readiness.json')
    parser.add_argument('--template', action='store_true')
    parser.add_argument('--computer', choices=('mac', 'windows'), default='mac')
    parser.add_argument('--phone', choices=('iphone', 'ipad'), default='iphone')
    args = parser.parse_args()
    try:
        if args.template:
            result = template(args.computer, args.phone)
        else:
            record = json.loads(args.input.read_text(encoding='utf-8'))
            if not isinstance(record, dict):
                raise ValueError('输入应为设备及逐项检查记录。')
            result = evaluate(record)
    except (OSError, ValueError) as exc:
        print(json.dumps({'status': 'input_needed', 'detail': str(exc),
                          'next_action': '读取已有进度，按 --template 的字段补齐本次检查记录。'},
                         ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
