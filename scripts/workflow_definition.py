"""Single stage catalog and completion rules for customer delivery."""
from datetime import datetime, timedelta, timezone
from score_policy import assessment

DEVICE_GUIDANCE = """**这套程序最推荐 Mac＋iPhone，其次是 Windows＋iPhone。**

- **Mac＋iPhone：最适配。**电脑配置由 Codex 协助完成；手机支持镜像时，也可以由 Codex 协助配置，您需要手动操作的部分最少。
- **Windows＋iPhone：也可以使用。**电脑配置由 Codex 协助完成，手机部分需要您手动操作，Codex 会按步骤指导您，遇到问题可以发截图一起排查。
- **Windows＋Android：目前暂不推荐。**安卓的订阅付款流程还没有完成整套交付验证，现阶段优先选择 iPhone／iPad 的订阅路线。

流程先配置电脑，再完成手机网络、手机登录和订阅；日常使用回到电脑。iPad 也能承担登录与内购，具体操作按实际设备继续。账号验证和付款由您本人完成。"""


# Field rules: true/false, text, timestamp, scores, or an explicit choice tuple.
STAGES = [
    ('intake', '确认设备封禁经历', '13-reader-guide.md', {'banned_login': ('yes', 'no', 'unknown')}),
    ('cleanup', '处理适用设备的旧登录残留', '04-recovery.md',
     {'outcome': ('cleaned', 'deferred', 'not_applicable'), 'handled_scope': 'text'}),
    ('devices', '记录设备搭配与准备说明', '13-reader-guide.md',
     {'computer': ('mac', 'windows'), 'phone': ('iphone', 'ipad', 'android'), 'setup_explained': True, 'pdf_explained': True}),
    ('google', '准备 Google 账号：已有复用，没有则购买', '08-google-account.md', {'account_available': True}),
    ('vps', '读取或准备 VPS 与 SSH 访问', '01-network.md',
     {'access_ready': True, 'node_label': 'text', 'node_timezone': 'text'}),
    ('server', '配置并读回服务端节点', '01-network.md',
     {'mode': ('scripted', 'existing'), 'service_running': True, 'node_exported': True,
      'parameters_checked': True}),
    ('computer_network', '完成电脑客户端与新旧网络交接', '01-network.md',
     {'system_proxy_off': True, 'tun_enabled': True, 'global_route': True,
      'http_proxy_ready': True, 'exit_matches': True, 'https_ok': True,
      'old_vpn_released': True, 'codex_reply_received': True, 'disconnect_checked': True}),
    ('browser', '创建、打开并验收 AdsPower 环境', '02-browser-iphone.md',
     {'profile_ref': 'text', 'saved': True, 'opened': True, 'proxy_type': ('http', 'socks5'),
      'proxy_configured': True, 'fingerprint_configured': True, 'location_blocked': True,
      'checked_profile_ref': 'text', 'exit_matches': True, 'https_ok': True,
      'dns_checked': True, 'ipv6_checked': True, 'webrtc_checked': True,
      'disconnect_checked': True, 'scores': 'scores', 'usage_explained': True}),
    ('phone_proxy', '配置手机同一节点和全局代理', '02-browser-iphone.md',
     {'node_label': 'text', 'client': 'text', 'global_route': True, 'vpn_connected': True}),
    ('timezone', '选择时区并展示、完成电脑与手机设置路径', '02-browser-iphone.md',
     {'choice': ('node', 'taipei'), 'target': 'text', 'computer_zone': 'text',
      'phone_zone': 'text', 'browser_zone': 'text', 'paths_shown': True,
      'computer_auto_off': True,
      'phone_auto_off': True, 'phone_location_off': True,
      'browser_location_blocked': True}),
    ('phone_network', '在手机独立验收网络', '06-before-login.md',
     {'node_label': 'text', 'network_type': ('wifi', 'cellular', 'both'), 'exit_matches': True,
      'https_ok': True, 'dns_checked': True, 'ipv6_checked': True, 'routes_checked': True,
      'disconnect_checked': True, 'scores': 'scores'}),
    ('payment_preparation', '核对美区 Apple ID、养号起点与支付准备', '03-apple.md', {}),
    ('app', '保持节点开启，下载官方 Claude 并检查请求路径', '03-apple.md', {}),
    ('login', '使用 Google 账号登录 Claude', '08-google-account.md',
     {'google_login': True, 'signed_in': True, 'account_ref': 'text', 'browser_notice_shown': True}),
    ('subscription', '确认手机订单和 Pro 权益，完成交付', '03-apple.md',
     {'account_ref': 'text', 'channel': ('apple', 'google_pay'),
      'order_confirmed': True, 'pro_visible': True, 'handoff_explained': True}),
]

# Technical changes retain commercial/account history. A changed phone rechecks
# its login and entitlement while keeping the previous order as a reuse hint.
INVALIDATES = {
    'cleanup': ('cleanup', 'app', 'login', 'subscription'),
    'intake': ('intake', 'cleanup', 'app', 'login', 'subscription'),
    'devices': ('devices', 'computer_network', 'browser', 'phone_proxy', 'timezone', 'phone_network',
                'payment_preparation', 'app', 'login', 'subscription'),
    'node': ('vps', 'server', 'computer_network', 'browser', 'phone_proxy', 'timezone', 'phone_network', 'app'),
    'handoff': ('computer_network', 'browser', 'phone_proxy', 'timezone', 'phone_network', 'app'),
    'network': ('server', 'computer_network', 'browser', 'phone_proxy', 'timezone', 'phone_network', 'app'),
    'computer': ('computer_network', 'browser', 'timezone'),
    'browser': ('browser', 'timezone'),
    'phone': ('phone_proxy', 'timezone', 'phone_network', 'payment_preparation', 'app', 'login', 'subscription'),
    'timezone': ('timezone',),
    'google': ('google', 'login', 'subscription'),
    'apple': ('payment_preparation',),
}

# Changing these objects starts fresh observations within the current stage.
OBJECT_FIELDS = {'browser': 'profile_ref', 'payment_preparation': 'apple_account_ref', 'phone_proxy': 'apple_account_ref'}

ACTIONS = {
    'cleanup_audit': ('cleanup', ['cleanup.py', '--audit']),
    'cleanup_apply': ('cleanup', ['cleanup.py']),
    'cleanup_restore': ('cleanup', ['cleanup.py']),
    'server_preflight': ('server', ['network.py', 'preflight']),
    'server_deploy': ('server', ['network.py', 'deploy']),
    'server_export': ('server', ['network.py', 'export']),
    'download_karing': ('computer_network', ['download_karing.py']),
    'probe_proxy': ('computer_network', ['network.py', 'probe', '--route', 'proxy']),
    'probe_system': ('computer_network', ['network.py', 'probe', '--route', 'system']),
    'browser_scores': ('browser', ['network.py', 'scores']),
    'phone_scores': ('phone_network', ['network.py', 'scores']),
}


APPLE_ORIGINS = ('self_used', 'newly_registered', 'purchased')


APPLE_OPTIONAL = {'account_origin': APPLE_ORIGINS, 'apple_account_ref': 'text', 'account_type': ('longstanding', 'new'),
                  'store_signed_in': True, 'first_used_at': 'timestamp',
                  'wait_choice': ('wait', 'continue'), 'apple_reminder_shown': True,
                  'purchase_restricted': False, 'support_case': 'text', 'support_retry_at': 'date'}
OPTIONAL_FIELDS = {
    'google': {'account_origin': ('self_used', 'purchased'),
               'purchase_channel': ('chuhai91', 'gmailbuy'), 'materials_explained': True},
    'devices': {'pdf_save_choice': ('yes', 'no', 'unanswered'), 'pdf_saved_path': 'text'},
    'phone_proxy': {**APPLE_OPTIONAL, 'client_available': True},
    'payment_preparation': {**APPLE_OPTIONAL, 'route_accepted': True},
    'browser': {'score_review': ('rechecked', 'continue'), 'score_review_note': 'text'},
    'phone_network': {'score_review': ('rechecked', 'continue'), 'score_review_note': 'text'},
    'subscription': {'purchase_restricted': False, 'support_case': 'text', 'support_retry_at': 'date'},
}


def apple_wait(data, now):
    if data.get('account_type') != 'new' or data.get('store_signed_in') is not True:
        return None
    try:
        first = timestamp(data['first_used_at'])
        if first > now:
            return None
        until = first + timedelta(hours=48)
        return until.isoformat() if now < until and data.get('wait_choice') != 'continue' else None
    except (ValueError, TypeError, KeyError):
        return None


def facts(state, stage):
    return state.get('records', {}).get(stage, {}).get('data', {})


def catalog(state):
    device = facts(state, 'devices')
    android = device.get('phone') == 'android'
    result = []
    for key, title, reference, fields in STAGES:
        if key == 'cleanup' and facts(state, 'intake').get('banned_login') != 'yes':
            continue
        fields = dict(fields)
        if key == 'google' and facts(state, key).get('account_origin') == 'purchased':
            fields['materials_explained'] = True
        if key == 'devices' and android:
            fields.update(android_route_explained=True, payment_route_status=('available', 'needs_setup', 'unknown'))
        if android and key in ('phone_proxy', 'timezone'):
            reference = '11-android-web-pay.md'
        if key == 'timezone':
            if device.get('computer') == 'mac':
                fields['computer_timezone_location_off'] = True
            else:
                fields['computer_location_off'] = True
            if not android:
                fields['phone_timezone_location_off'] = True
        if key == 'phone_proxy' and not android and facts(state, key).get('client_available') is False:
            fields.update(account_origin=APPLE_ORIGINS, account_type=('longstanding', 'new'))
        if key == 'payment_preparation':
            if android:
                title, reference = '确认 Android 官网支付准备', '11-android-web-pay.md'
                fields = {'payment_method_available': True, 'route_explained': True, 'route_accepted': True}
            else:
                fields = {'account_origin': APPLE_ORIGINS, 'apple_account_ref': 'text', 'region': ('US',), 'store_signed_in': True,
                          'account_type': ('longstanding', 'new'), 'purchase_restricted': False,
                          'payment_ready': True}
                if facts(state, key).get('account_type') == 'new':
                    fields['first_used_at'] = 'timestamp'
        if key == 'app':
            fields = {'official_site_open': True} if android else {'official_app_installed': True}
            fields.update(vpn_connected=True, route_checked=True)
            if android:
                title, reference = '在手机打开 Claude 官网并检查请求路径', '11-android-web-pay.md'
        if android and key == 'subscription':
            reference = '11-android-web-pay.md'
            fields['google_pay_displayed'] = True
        if key == 'phone_proxy' and not android:
            fields['client_available'] = True
        result.append({'id': key, 'title': title, 'reference': 'references/' + reference, 'fields': fields})
    return result


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('时间须包含时区偏移')
    return result


def validation(stage, data, state, now):
    # Derive dynamic fields from the proposed account type, not only saved facts.
    fields = dict(stage['fields'])
    if stage['id'] == 'timezone' and facts(state, 'devices').get('computer') == 'mac':
        # Prior Mac observations can contain the retired global-location field.
        data = {key: value for key, value in data.items() if key != 'computer_location_off'}
    if stage['id'] == 'google':
        fields.pop('materials_explained', None)
        if data.get('account_origin') == 'purchased':
            fields['materials_explained'] = True
    if stage['id'] == 'devices':
        if data.get('phone') == 'android':
            fields.update(android_route_explained=True, payment_route_status=('available', 'needs_setup', 'unknown'))
        else:
            fields.pop('android_route_explained', None)
            fields.pop('payment_route_status', None)
    apple_stage = stage['id'] in ('payment_preparation', 'phone_proxy') and facts(state, 'devices').get('phone') != 'android'
    if apple_stage:
        if stage['id'] == 'phone_proxy':
            fields.pop('account_origin', None)
            fields.pop('account_type', None)
        if stage['id'] == 'payment_preparation' or data.get('client_available') is False or data.get('account_type') is not None:
            fields.update(account_origin=APPLE_ORIGINS, account_type=('longstanding', 'new'))
        fields.pop('first_used_at', None)
        if data.get('account_type') == 'new':
            fields.update(first_used_at='timestamp', apple_account_ref='text', store_signed_in=True, apple_reminder_shown=True)
    optional = OPTIONAL_FIELDS.get(stage['id'], {})
    # Apple fields never leak into the Android route.
    if stage['id'] != 'google' and facts(state, 'devices').get('phone') == 'android':
        optional = {k: v for k, v in optional.items() if k not in APPLE_OPTIONAL and k != 'client_available'}
    for key, rule in optional.items():
        if key in data:
            fields.setdefault(key, rule)
    issues = []
    for name, rule in fields.items():
        value = data.get(name)
        valid = False
        if isinstance(rule, bool):
            valid = value is rule
        elif isinstance(rule, tuple):
            valid = value in rule
        elif rule == 'text':
            valid = isinstance(value, str) and bool(value.strip())
        elif rule in ('timestamp', 'date'):
            try:
                valid = isinstance(value, str) and (rule == 'date' or timestamp(value) <= now)
                if valid:
                    timestamp(value)
            except (ValueError, TypeError):
                pass
        elif rule == 'scores':
            valid = isinstance(value, dict) and set(value) == {'netcoffee', 'ping0', 'scamalytics'}
            if valid:
                for observation in value.values():
                    if not isinstance(observation, dict):
                        valid = False
                        break
                    score = observation.get('value')
                    valid &= assessment('netcoffee', score) not in ('invalid', 'unverified')
                    valid &= isinstance(observation.get('result'), str) and bool(observation['result'].strip())
        if not valid:
            issues.append(name)
    key = stage['id']
    if key == 'browser' and data.get('checked_profile_ref') != data.get('profile_ref'):
        issues.append('checked_profile_ref')
    if key in ('phone_proxy', 'phone_network') and data.get('node_label') != facts(state, 'vps').get('node_label'):
        issues.append('node_label')
    if key == 'timezone':
        target = 'Asia/Taipei' if data.get('choice') == 'taipei' else facts(state, 'vps').get('node_timezone')
        for name in ('target', 'computer_zone', 'phone_zone', 'browser_zone'):
            if data.get(name) != target:
                issues.append(name)
    if key == 'subscription':
        if data.get('account_ref') != facts(state, 'login').get('account_ref'):
            issues.append('account_ref')
        channel = 'google_pay' if facts(state, 'devices').get('phone') == 'android' else 'apple'
        if data.get('channel') != channel:
            issues.append('channel')
    unknown = set(data) - set(fields)
    issues.extend('unknown:' + name for name in sorted(unknown))
    result = {'valid': not issues, 'missing': sorted(set(issues))}
    if apple_stage:
        until = apple_wait(data, now)
        if until:
            result['waiting_until'] = until
    if key in ('browser', 'phone_network') and isinstance(data.get('scores'), dict):
        bands = {name: assessment(name, obj.get('value')) for name, obj in data['scores'].items()
                 if isinstance(obj, dict) and name in ('netcoffee', 'ping0', 'scamalytics')}
        result['score_advice'] = bands
        if 'recheck_recommended' in bands.values():
            if data.get('score_review') not in ('rechecked', 'continue'):
                result['missing'].append('score_review')
            if not isinstance(data.get('score_review_note'), str) or not data['score_review_note'].strip():
                result['missing'].append('score_review_note')
            result['valid'] = not result['missing']
    return result
