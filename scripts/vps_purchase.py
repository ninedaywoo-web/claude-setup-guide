"""Evaluate current official order-page observations for the default VPS route."""
from datetime import datetime
import re
from urllib.parse import urlsplit, parse_qs

TARGETS = {
    'dmit': {'plan': 'LAX.AS3.Pro.TINY', 'network': 'Premium', 'cycle': 'monthly',
             'url': 'https://www.dmit.io/cart.php?region=los-angeles&network=premium&generation=as3'},
    'bandwagon': {'plan': 'USCA_9-1GB', 'network': 'CN2 GIA', 'cycle': 'quarterly',
                 'url': 'https://bandwagonhost.com/order/ecommerce/Los%20Angeles/USCA_9'},
    'akile': {'plan': 'LAXPremium-Mini', 'network': 'Premium', 'cycle': 'monthly',
              'url': 'https://akile.ai/'},
}
DMIT_DESCRIPTION = '洛杉矶 Premium → AS3 → ' + TARGETS['dmit']['plan'] + '，参考价 10.90 美元/月'
PURCHASE_GUIDANCE = ('需要购买时，默认按 **DMIT → 搬瓦工 → AKILE** 选：先从 [DMIT 实际订购目录](https://www.dmit.io/cart.php) 核对已成功交付的'
    + DMIT_DESCRIPTION + '；缺货就核对并推荐有成熟适配经验的搬瓦工 ' + TARGETS['bandwagon']['plan'] +
    '，搬瓦工也缺货再看 AKILE ' + TARGETS['akile']['plan'] + '。默认分别按月付、季付、月付准备；下单前列清实际付款总额、覆盖时长和续费金额。')
POLICY = ('库存从实际订购目录和套餐配置页读取。DMIT 固定从 https://www.dmit.io/cart.php 进入，'
          '默认已交付套餐为 ' + DMIT_DESCRIPTION + '。价格页的 Order Now、搜索摘要及旧图只作说明。'
          '缺货、完整目录中目标未列出分别记录 sold_out、not_listed，继续搬瓦工 ' + TARGETS['bandwagon']['plan'] + '，再到 AKILE ' + TARGETS['akile']['plan'] + '。'
          'Cloudflare 验证、403、超时记 unknown；页面明确要求账户登录才记 login_required。优先复用客户已登录浏览器，'
          '仍无法读取就取得当前目标套餐区域的截图；查不到库存时继续核对下一家，并清楚说明前一家尚未核实。'
          '仅实际进入同一目标套餐配置页且取得计费周期、总额和续费金额，才可输出可购买。'
          '默认 DMIT 缺货后先核对搬瓦工，有货仍首推搬瓦工。另行查到其他 DMIT 套餐确实可买时，'
          '在 dmit_alternatives 记录其独立订购证据，并告诉用户“这个 DMIT 套餐目前没有交付实践；搬瓦工已有成熟适配经验，我们仍推荐搬瓦工”，'
          '展示准确线路、费用和两者库存，让用户选择；收到明确选择后以 source.kind=user 提交 purchase_choice。'
          '没有客户选择就沿默认推荐继续；T1、Eyeball、其他世代和高价档不自动替代目标套餐。')


def default_offer(checks, errors):
    outcomes = []
    for vendor, target in TARGETS.items():
        item = checks.get(vendor)
        result = {'vendor': vendor, **target, 'can_purchase': False, 'checked': outcomes}
        if vendor not in checks:
            return {**result, 'status': 'check_required'}
        reason = errors[vendor]
        if reason:
            return {**result, 'status': 'check_required', 'reason': reason}
        status = item['status']
        outcomes.append({'vendor': vendor, 'status': status})
        if status in ('sold_out', 'not_listed', 'unknown', 'login_required'):
            continue
        return {**result, 'status': 'available', 'can_purchase': True,
                'amount': item['amount'], 'currency': item['currency'],
                'renewal_amount': item['renewal_amount'], 'checked_at': item['checked_at'],
                'order_url': item['url']}
    return {'status': 'no_verified_offer', 'can_purchase': False, 'checked': outcomes}


def evaluate(checks, now, *, alternatives=None, choice=None, captures=None):
    """Validate page observations once, then apply the agreed recommendation order."""
    checks = checks if isinstance(checks, dict) else {}
    errors = {vendor: (capture_error(vendor, checks[vendor], captures) or check_observation(vendor, checks[vendor], now)) for vendor in TARGETS if vendor in checks}
    result = default_offer(checks, errors)
    result['alternatives'] = []
    verified = {x['vendor']: x['status'] for x in result['checked']}
    # Other DMIT plans are compared only after the default is actually unavailable.
    if verified.get('dmit') in ('sold_out', 'not_listed'):
        for item in alternatives if isinstance(alternatives, list) else []:
            if not isinstance(item, dict) or item.get('status') != 'available':
                continue
            plan = item.get('plan', '')
            match = re.fullmatch(r'LAX\.(AS3|AN4|AN5)\.(Pro|EB|T1)\.[A-Za-z0-9_-]+', plan) if isinstance(plan, str) else None
            if not match or plan == TARGETS['dmit']['plan']:
                continue
            target = {'plan': plan, 'network': {'Pro': 'Premium', 'EB': 'Eyeball', 'T1': 'Tier 1'}[match[2]], 'cycle': 'monthly'}
            if capture_error('dmit', item, captures) is None and check_observation('dmit', item, now, target=target) is None:
                result['alternatives'].append({k: item[k] for k in ('plan', 'network', 'cycle', 'amount', 'currency', 'renewal_amount', 'url')})
    result['recommended_plan'] = result.get('plan') if result['can_purchase'] else None
    if result['alternatives'] and choice is None and result['recommended_plan']:
        return {**result, 'status': 'awaiting_choice', 'can_purchase': False}
    if choice is None or choice == result['recommended_plan']:
        return result
    selected = next((a for a in result['alternatives'] if a['plan'] == choice), None)
    if selected and 'bandwagon' in verified:
        return {**result, **selected, 'vendor': 'dmit', 'status': 'customer_selected',
                'can_purchase': True, 'order_url': selected['url']}
    return {**result, 'status': 'choice_needs_recheck', 'can_purchase': False}


def capture_error(vendor, item, captures):
    # Pure policy tests may omit captures; the delivery controller always supplies receipts.
    if captures is None:
        return None
    if not isinstance(item, dict):
        return 'page_observation_required'
    receipt_id = item.get('receipt_id')
    capture = captures.get(receipt_id) if isinstance(receipt_id, str) else None
    if not capture or capture.get('vendor') != vendor:
        return 'page_capture_required'
    if item.get('url') != capture['url'] or item.get('checked_at') != capture['checked_at']:
        return 'capture_url_or_time_mismatch'
    normalize = lambda value: re.sub(r'\s+', '', value).lower()
    quote = item.get('evidence')
    if not isinstance(quote, str) or not quote.strip() or normalize(quote) not in normalize(capture['text']):
        return 'quote_not_in_captured_page'
    if item.get('status') == 'not_listed' and isinstance(item.get('plan'), str) and normalize(item['plan']) in normalize(capture['text']):
        return 'target_present_in_captured_catalog'
    page = capture['page']
    if item.get('page') != page:
        return 'captured_page_type_mismatch'
    if item.get('status') == 'available':
        if any(x in capture['text'].lower() for x in ('out of stock', 'sold out', '缺货', '缺貨', '售罄')):
            return 'conflicting_stock_evidence'
        billing = item.get('billing_evidence', '')
        if not isinstance(billing, str) or not billing or normalize(billing) not in normalize(capture['text']):
            return 'billing_quote_required'
        amounts = re.findall(r'\d+(?:\.\d+)?', billing)
        if any(str(item.get(k)) not in amounts and not any(float(x) == item.get(k) for x in amounts) for k in ('amount', 'renewal_amount')):
            return 'billing_amount_not_in_page'
        cycles = {'monthly': ('monthly', '月付', '每月', '/month'), 'quarterly': ('quarterly', '季付', '三个月', '3 months')}
        if not any(x in billing.lower() for x in cycles.get(item.get('cycle'), ())):
            return 'billing_cycle_not_in_page'
        currencies = {'USD': ('usd', 'us$', '$'), 'CNY': ('cny', 'rmb', '¥', '￥', '元')}
        if not any(x in billing.lower() for x in currencies.get(item.get('currency'), ())):
            return 'billing_currency_not_in_page'
    return None


def check_observation(vendor, item, now, *, target=None):
    if not isinstance(item, dict):
        return 'page_observation_required'
    target = target or TARGETS[vendor]
    if item.get('plan') != target['plan'] or item.get('network') != target['network']:
        return 'target_mismatch'
    try:
        u = urlsplit(item.get('url', ''))
        host = {'dmit': ('dmit.io', 'www.dmit.io'), 'bandwagon': ('bandwagonhost.com', 'www.bandwagonhost.com'),
                'akile': ('akile.ai', 'www.akile.ai')}[vendor]
        if u.scheme != 'https' or u.hostname not in host or u.username or u.password:
            return 'official_order_url_required'
        if vendor == 'dmit' and u.path != '/cart.php':
            return 'official_order_url_required'
        if vendor == 'dmit':
            query = parse_qs(u.query)
            generation = target['plan'].split('.')[1].lower()
            network = {'Premium': 'premium', 'Eyeball': 'eyeball', 'Tier 1': 'tier-1'}[target['network']]
            for key, expected in (('region', 'los-angeles'), ('network', network), ('generation', generation)):
                if key in query and query[key] != [expected]:
                    return 'target_mismatch'
        if vendor == 'bandwagon' and not u.path.startswith(('/order/', '/cart.php')):
            return 'official_order_url_required'
        at = datetime.fromisoformat(item['checked_at'].replace('Z', '+00:00'))
        if at.tzinfo is None or at > now:
            return 'observation_time_required'
    except (KeyError, TypeError, ValueError, AttributeError):
        return 'observation_time_required'
    if not isinstance(item.get('evidence'), str) or not item['evidence'].strip():
        return 'page_evidence_required'
    status = item.get('status')
    page = item.get('page')
    text = re.sub(r'\s+', '', item['evidence']).lower()
    identity = ('usca_9', '1gb') if vendor == 'bandwagon' else (target['plan'].lower(),)
    plan_matches = all(token in text for token in identity)
    if status in ('unknown', 'login_required'):
        return None if page in ('challenge', 'error', 'login') and (status != 'login_required' or page == 'login') else 'page_status_mismatch'
    if status == 'not_listed':
        return None if page == 'catalog' and item.get('catalog_complete') is True else 'complete_catalog_required'
    if status == 'sold_out':
        return None if page in ('catalog', 'configuration') and plan_matches and any(x in item['evidence'].lower() for x in ('缺貨', '缺货', '售罄', 'out of stock', 'sold out')) else 'stock_label_required'
    if status != 'available' or page != 'configuration':
        return 'configuration_required'
    if not plan_matches:
        return 'plan_evidence_required'
    if any(x in item['evidence'].lower() for x in ('缺貨', '缺货', '售罄', 'out of stock', 'sold out')):
        return 'conflicting_stock_evidence'
    if item.get('cycle') != target['cycle']:
        return 'billing_cycle_mismatch'
    for key in ('amount', 'renewal_amount'):
        value = item.get(key)
        if type(value) not in (int, float) or not 0 < value < 100000:
            return 'payment_total_required'
    if item.get('currency') != ('CNY' if vendor == 'akile' else 'USD'):
        return 'currency_mismatch'
    return None
