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
        ('computer_timezone_matches_exit', '电脑手动时区对应 VPS 出口，并返回设置页复查'),
    ]
    if computer == 'mac':
        checks += [
            ('computer_timezone_location_off', 'Mac 系统服务“设定时区”关闭或随定位总开关停用'),
            ('computer_location_off', 'Mac 关闭定位服务总开关'),
        ]
    checks += [
        ('phone_timezone_auto_off', '手机关闭日期与时间中的“自动设置”'),
        ('phone_timezone_matches_exit', '手机手动时区对应 VPS 出口，并返回设置页复查'),
        ('phone_timezone_location_off', '手机系统服务“设定时区”关闭或随定位总开关停用'),
        ('phone_location_off', '手机关闭定位服务总开关'),
        ('browser_timezone_matches_exit', 'AdsPower 实际时区对应 VPS 出口'),
        ('browser_geolocation_denied', 'AdsPower 地理位置设为“禁止”'),
        ('phone_network', '完成手机登录前网络验收'),
    ]
    return checks


def template(computer, phone):
    return {'computer': computer, 'phone': phone,
            'checks': {key: {'status': 'pending', 'result': ''}
                       for key, _ in requirements(computer, phone)}}


def evaluate(record):
    required = requirements(record.get('computer'), record.get('phone'))
    checks = record.get('checks', {})
    if not isinstance(checks, dict):
        raise ValueError('checks 应为逐项检查记录。')
    pending = []
    for key, action in required:
        item = checks.get(key, {})
        if not isinstance(item, dict) or item.get('status') != 'passed':
            pending.append({'id': key, 'action': action})
    return {'status': 'needs_setup' if pending else 'ready',
            'scope': 'pre_login_environment',
            'pending': pending,
            'next_action': pending[0]['action'] if pending else
            '复用 Apple 账户与支付准备，进入手机 Google 登录和 Pro 订阅；已登录则继续订阅。'}


def main():
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
