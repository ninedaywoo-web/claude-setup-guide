"""Compact CLI delivery view; full observations stay in the controller."""
from copy import deepcopy


def policy():
    from vps_purchase import TARGETS, POLICY
    from network_server import SERVER_OS, VERSION, XRAY_VERSION, DEFAULT_SNI, MIN_CLIENT_VERSION
    from download_karing import VERSION as KARING_VERSION
    return {'server_system': SERVER_OS, 'vps_targets': TARGETS, 'purchase_instruction': POLICY,
            'software': {'panel': VERSION, 'xray': XRAY_VERSION, 'karing': KARING_VERSION,
                         'sni': DEFAULT_SNI, 'min_client_version': MIN_CLIENT_VERSION}}


READING = {
    'vps': ['references/18-vps-stock.md', 'references/01-network.md：三、购买 VPS 流程（含选系统）'],
    'server': ['references/14-scripted-execution.md：服务器与节点', 'references/01-network.md：四至六节（部署、节点与导出）'],
    'browser': ['references/02-browser-iphone.md：第 1 节'],
    'phone_proxy': ['references/02-browser-iphone.md：2.1、2.2；故障时展开对应小节'],
    'timezone': ['references/02-browser-iphone.md：2.3'],
    'phone_network': ['references/06-before-login.md', 'references/02-browser-iphone.md：3.1'],
}


def compact(result):
    result = deepcopy(result)
    if 'workflow' in result:
        result['workflow'] = compact(result['workflow'])
        capture = result.get('execution', {}).get('result', {})
        # The page body is saved in the receipt; expose its path instead of repeating it.
        if 'capture_method' in capture:
            capture.pop('text', None)
        return result
    if 'stage' not in result:
        return result
    result.pop('progress', None)
    if 'required_fields' in result:
        result['required_fields'] = {key: rule for key, rule in result['required_fields'].items()
                                     if key in result.get('missing', [])}
    result.pop('account_history', None)
    result.pop('previous_observation', None)
    result.pop('communication_instruction', None)
    result.pop('task_scope_instruction', None)
    result.pop('teaching_instruction', None)
    result.pop('image_markdown', None)
    result['teaching_topics'] = [{k: topic[k] for k in ('id', 'title')} for topic in result.get('teaching_topics', [])]
    lesson = result.pop('default_teaching', None)
    if lesson:
        result['current_guide'] = {k: lesson[k] for k in ('topic', 'step', 'total_steps', 'reference')}
    # Keep links, default pictures, warnings and troubleshooting intact in customer_message.
    action = result.get('next_action', '')
    action = action.split(' 按当前操作从 teaching_topics')[0]
    if result.get('purchase_instruction'):
        action = action.replace(result['purchase_instruction'], '')
    result['next_action'] = action.strip()
    result['display_instruction'] = ('首次进入阶段，完整展示 customer_message 的说明、使用信息和提醒；先给明确建议，标明操作设备，配原图、1～3 个动作与完成标志；已讲内容按需复用。'
        '当前小步有图就展示；用户说不会或图没显示时用 guide 重讲，随后接回当前阶段。')
    if result.get('stage') == 'browser':
        result['display_instruction'] += ('本阶段说明须包含 Claude 桌面版、Claude Code 可用，AdsPower 的登录授权用途，'
            '以及桌面端权限方面的担忧和已交付用户正常使用的反馈；按 customer_message 原有表述给到客户。')
    if result.get('verification_images'):
        result['display_instruction'] += '验证页要求身份验证器验证码时，展示取码链接和 verification_images 的原图。'
    result['reading'] = READING.get(result.get('stage'), [result['reference']] if result.get('reference') else [])
    if result.get('stage') == 'computer_network':
        windows = any(t['id'] == 'windows_client' for t in result['teaching_topics'])
        result['reading'] = ['references/14-scripted-execution.md：独立测通与切换后复测',
            'references/10-windows.md：第 2、4～6 节' if windows else
            'references/01-network.md：配置期间先保住 Codex 的网络；七、客户端配置']
    result['details_command'] = 'python3 scripts/workflow.py next --full'
    return result
