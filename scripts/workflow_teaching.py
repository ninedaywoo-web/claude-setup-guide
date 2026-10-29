"""Reusable, read-only teaching cards backed by the original course figures."""
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOOGLE_IMAGES = [f'assets/google-account/{name}-original.png' for name in
                 ('01-order', '02-2fa', '03-google-code')]
POLICY = ('当前操作有对应图解就默认在聊天直接展示，配 1～3 个动作和完成标志；按当前小步骤逐张展示。'
          '用户说不会、找不到、没看懂、再讲一次或图片没显示时，结合当前页面和上下文重新取对应图并拆细说明，'
          '已讲过的标记不抑制本次求助。内容明确就直接讲；无法区分账号、验证码类型或操作设备时只问一个关键问题。'
          '教学只解释当前问题，不提交成功结果、不改变阶段；实际登录、充值和付款仍按当前流程执行。')


def card(title, stages, reference, images=(), instruction='', computer=None, phone=None, seller=None):
    return dict(title=title, stages=stages.split(), reference='references/' + reference,
                images=list(images), instruction=instruction, computer=computer, phone=phone, seller=seller)


def pics(group, *names):
    return ['assets/' + group + '/' + name for name in names]


CARDS = {
    'network_handoff': card('网络交接参考', 'computer_network', '01-network.md', pics('images/network', '01.jpg'), '先说明旧网络与新节点如何交接，再根据当前网络状态操作。'),
    'network_concepts': card('上网和节点的基础概念', 'vps computer_network', '01-network.md', pics('images/network', '02.jpg'), '用户不理解节点或代理时，用这张原理图结合当前设备解释。'),
    'server_ssh': card('SSH 连接参考', 'vps server', '01-network.md', pics('images/network', '09.jpg'), '按当前电脑平台选择终端操作，示例图用于解释 SSH 连接，实际命令从本次服务器资料生成。'),
    'network_basics': card('VPS、节点与两台设备怎样连接', 'vps', '01-network.md', pics('images/network', '03.jpg'),
                          '先用架构图说明电脑和手机连接同一台 VPS，再确认已有服务器还是需要购买。'),
    'chuhai_register': card('注册出海91网站账号', 'google', '08-google-account.md', pics('chuhai91', '01-register.png'),
                           '用本人能收邮件的邮箱注册商家网站，QQ 邮箱也可以；看到登录后的购物页面再继续。', seller='chuhai91'),
    'chuhai_category': card('进入谷歌精品老号分类', 'google', '08-google-account.md', pics('chuhai91', '02-google-aged-category.png'),
                           '已登录商家网站后，按图打开 Google 谷歌账户，再进入谷歌精品老号。', seller='chuhai91'),
    'chuhai_product': card('选择美国 IP 创建的老号', 'google', '08-google-account.md', pics('chuhai91', '03-us-ip-product.png'),
                          '核对商品是否标明美国 IP 创建／注册，并看当前库存、数量与价格。', seller='chuhai91'),
    'gmailbuy': card('GmailBuy 选购', 'google', '08-google-account.md', instruction='沿用 GmailBuy 当前页面，核对美区老号和价格；根据实际页面逐步说明。', seller='gmailbuy'),
    'google_materials': card('看懂账号资料和两步验证码', 'google login', '08-google-account.md', GOOGLE_IMAGES,
                            '按三张原图依次解释邮箱与密码、商家标注的 2FA 密钥、生成当前验证码及回填位置。取码链接：https://2fa.run/ 。现在可先看懂，实际登录按主流程进行。'),
    'google_2fa': card('2FA 密钥取码和回填', 'google login', '08-google-account.md', GOOGLE_IMAGES[1:],
                      '直接给 https://2fa.run/ 。按图找到 JS实现 输入区，由客户填商家标注的密钥，点击获取验证码，再把当前码填回要求身份验证器验证码的 Google 页面。密钥和本次验证码分别解释；快到期就等下一组。'),
    'google_login': card('从手机 Claude 进入 Google 登录', 'login', '08-google-account.md', instruction='打开手机官方 Claude 的 Google 登录入口，输入准备好的账号。看当前验证页面，身份验证器用 google_2fa，短信／恢复邮箱／备用码用 google_other_verification。'),
    'google_other_verification': card('短信、恢复邮箱或备用码验证', 'login', '08-google-account.md', instruction='先辨认页面要求的验证方式，说明去哪里取得对应验证码；这类输入框按实际页面完成。需要更换验证方式时查看页面的“尝试其他方式”。'),
    'vps_dmit': card('DMIT 选购与开通', 'vps', '01-network.md', pics('images/network', '04.jpg', '05.jpg', '06.jpg', '07.jpg', '08-redacted.png'),
                     '按当前小步骤选图：套餐、系统、订单、结算、服务器资料；原图 AN5 与 9.99 美元作界面示例，当前默认已交付套餐为 AS3 Premium 的 LAX.AS3.Pro.TINY，参考价 10.90 美元/月。库存从 cart.php 读取，按 references/18-vps-stock.md 核对及选择后再给付款指引。'),
    'vps_bandwagon': card('搬瓦工注册与购买', 'vps', '09-vps-purchase.md', pics('vps-purchase', 'bandwagon-register-1.png', 'bandwagon-register-2.png', 'bandwagon-register-3.png', 'bandwagon-register-4.png', 'bandwagon-plan.png'),
                         '按客户当前注册或选套餐页面选择对应的一张图，已有账号直接进入选套餐步骤。'),
    'vps_akile': card('AKILE 套餐选择', 'vps', '09-vps-purchase.md', pics('vps-purchase', 'akile-plan.png'), '当前是套餐选购图，注册字段按实际页面逐项说明。'),
    'server_panel': card('服务端面板和节点参数', 'server', '01-network.md', pics('images/network', '10.jpg', '11.jpg', '12.jpg', '13.jpg'),
                        '按面板、创建节点及参数页选图；由 Codex 使用部署工具时说明当前结果，需要客户手动操作再按图带做。'),
    'node_export': card('找到节点导出入口', 'server phone_proxy', '01-network.md', pics('images/network', '14.jpg'),
                        '这张图是服务端导出入口；用户自己的节点二维码由本次部署生成，在电脑打开供手机扫描。'),
    'windows_client': card('Windows v2rayN 界面与连接检查', 'computer_network', '10-windows.md', pics('images/network', '15.jpg', '16.jpg', '17.jpg'),
                           '按当前动作选择主窗口、下载安装或延迟界面图；结合实际版本定位，延迟结果后继续检查 HTTPS 和出口。', computer='windows'),
    'mac_client': card('Mac Karing 配置', 'computer_network', '01-network.md', pics('images/network', '19.jpg', '20.jpg'),
                       '按 Mac Karing 当前页面带做，连接后核对实际出口和系统接管。', computer='mac'),
    'browser_profile': card('新建 AdsPower 环境', 'browser', '02-browser-iphone.md', pics('images/browser-iphone', '01.png'),
                            '按图设置环境名称、SunBrowser 和本机操作系统，Windows 选 Windows，Mac 选 macOS。'),
    'browser_proxy': card('填写 AdsPower 本机代理', 'browser', '02-browser-iphone.md', pics('images/browser-iphone', '02.png'),
                          '在代理信息填已测通的本机 HTTP 入口，测试通过再保存；地址与端口采用本机实测值。'),
    'browser_fingerprint': card('AdsPower 指纹设置', 'browser', '02-browser-iphone.md', pics('images/browser-iphone', '03.png'),
                                '按当前小步说明 WebRTC、定位和硬件真实值，保存后重新打开核对。'),
    'phone_node': card('iPhone 小火箭导入和选中节点', 'phone_proxy', '02-browser-iphone.md', instruction='电脑打开本次生成的节点二维码，手机用小火箭扫描。导入后指出首页新增的那一行，选中后再开启连接；页面截图按实际入口定位。', phone='apple'),
    'phone_config': card('小火箭配置分流参考', 'phone_proxy phone_network', '02-browser-iphone.md', pics('images/browser-iphone', '10.jpg'),
                         '这是既有配置案例和配置列表参考图；按客户实际文件名与规则处理，具体 DNS 添加、保存、回读见本章 2.2.4～2.2.5。', phone='apple'),
    'phone_dns': card('小火箭 DNS 加入列表与保存', 'phone_proxy phone_network', '02-browser-iphone.md', instruction='按 2.2.5：输入网址，点绿色＋，看到独立条目后保存，退出重开核对，再重连复测。根据当前手机截图定位字段。', phone='apple'),
    'phone_backup': card('手机本地保存配置与恢复', 'phone_proxy phone_network', '02-browser-iphone.md', instruction='按 2.2.4 保存原值和本机副本，确认能重新打开；恢复时固定目标，回读保存后的值，再测试网页、出口和微信。', phone='apple'),
    'timezone': card('电脑、手机时区与定位', 'timezone', '02-browser-iphone.md', instruction='按当前电脑和手机平台分别给设置路径，每轮只操作一台设备，完成后回到原页面核对实际值。'),
    'network_check': card('在手机核对出口与检测结果', 'phone_network', '06-before-login.md', instruction='手机浏览器打开 https://ping0.cc/ 核对当前出口，再按章节检查三站、DNS 与 IPv6；先确认手机使用 Wi-Fi 还是蜂窝网络。'),
    'android_phone': card('安卓手机导入与检查', 'phone_proxy timezone phone_network', '11-android-web-pay.md', instruction='按安卓实际页面操作，复用服务器节点；时区、网络及付款使用安卓分支。', phone='android'),
    'apple_register': card('注册美区 Apple 账户', 'phone_proxy payment_preparation', '03-apple.md', pics('images/apple', '01.jpg', '02.jpg'),
                           '客户选择自行注册后，按当前表单展示对应图，填写本人信息并完成验证。', phone='apple'),
    'apple_region': card('查看或调整 Apple 账户地区', 'phone_proxy payment_preparation', '03-apple.md', pics('images/apple', '03.jpg', '04.jpg', '05.jpg', '06.jpg', '07.jpg', '08.jpg'),
                         '先核对现有国家／地区；明确选择改区后再按实际进度展示后续图，原图的地址和支付示例按本人资料处理。', phone='apple'),
    'apple_store': card('在 App Store 登录账户', 'phone_proxy payment_preparation', '03-apple.md', pics('images/apple', '09.jpg'),
                        '本步操作 App Store，手机原有 iCloud 保持原样；完成后核对 App Store 账户，记录首次登录时间。', phone='apple'),
    'gift_official': card('苹果官网购买礼品卡', 'payment_preparation', '03-apple.md', pics('images/apple', '10.jpg', '11.jpg', '12.jpg', '13.jpg'),
                          '按选金额、收件邮箱、账单、邮件交付逐步选图。当前实际付款前核对账户与等待安排。', phone='apple'),
    'gift_alipay': card('支付宝渠道购买礼品卡', 'payment_preparation', '03-apple.md', pics('images/apple', '14.jpg'),
                        '客户选择该渠道后，按当前页面核对地区、金额及交付方式；已有礼品卡接兑换。', phone='apple'),
    'gift_redeem': card('兑换礼品卡到账户余额', 'payment_preparation', '03-apple.md', pics('images/apple', '15.jpg'),
                        'App Store → 头像 → 兑换电子礼品卡或代码；确认账户后由客户输入卡密，兑换后查看余额。', phone='apple'),
    'claude_app': card('认准官方 Claude App', 'app', '03-apple.md', pics('images/apple', '16.jpg'),
                       '按图辨认 Claude 与开发者 Anthropic，下载或打开官方 App，核对连接后再登录。', phone='apple'),
    'claude_subscribe': card('手机订阅与权益确认', 'subscription', '03-apple.md', pics('images/apple', '17.jpg'),
                             '找到升级入口，按实际价格选择 Pro；由客户确认付款，随后核对订单与当前 Claude 账号权益。', phone='apple'),
    'apple_support': card('Apple 购买受限与人工支持', 'phone_proxy payment_preparation subscription', '07-apple-purchase-support.md', pics('images/apple', '18.jpg', '19.jpg'),
                          '遇到购买受限时，按当前官方页面定位问题分类与人工支持入口，保留案件及重试安排。', phone='apple'),
    'apple_refund': card('查看 Apple 退款申请状态', '', '04-recovery.md', pics('images/recovery', '01.jpg'),
                         '用户询问退款时按章节核对真实订单和退款申请状态。', phone='apple'),
    'account_appeal': card('Claude 封禁申诉参考', '', '04-recovery.md', pics('images/recovery', '02.jpg'),
                          '用户询问封禁申诉时按原章节说明实际账号情况和申诉入口。'),
    'cleanup': card('清理旧账号登录残留', 'cleanup', '04-recovery.md', instruction='按当前电脑系统和使用过的应用定位清理范围，用实际检查结果逐项说明。'),
}


def eligible(topic, state):
    from workflow_definition import facts
    item = CARDS[topic]
    device, account = facts(state, 'devices'), facts(state, 'google')
    if item['computer'] and device.get('computer') != item['computer']:
        return False
    if item['phone'] == 'apple' and device.get('phone') not in ('iphone', 'ipad'):
        return False
    if item['phone'] == 'android' and device.get('phone') != 'android':
        return False
    if item['seller'] and account.get('purchase_channel') != item['seller']:
        return False
    return True


def guide(topic, state, stage, step=None):
    if not isinstance(topic, str) or topic not in CARDS:
        raise ValueError('unknown_teaching_topic')
    if not eligible(topic, state):
        raise ValueError('teaching_topic_not_for_current_device_or_seller')
    item = deepcopy(CARDS[topic])
    images = item['images']
    if step is None and len(images) > 1 and topic not in ('google_materials', 'google_2fa'):
        step = 1
    if step is not None:
        if step < 1 or step > len(images):
            raise ValueError('teaching_step_out_of_range')
        images = images[step-1:step]
    missing = [p for p in images if not (ROOT / p).is_file()]
    available = [p for p in images if p not in missing]
    markup = [f'![{item["title"]}](<{(ROOT / p).as_posix()}>)' for p in available]
    pdf_files = {
        '01-network.md': '01-纯净魔法从零部署.pdf', '10-windows.md': '01-纯净魔法从零部署.pdf',
        '02-browser-iphone.md': '02-指纹浏览器与 iPhone 网络配置.pdf',
        '03-apple.md': '03-Apple 账号、礼品卡与内购.pdf',
        '04-recovery.md': '04-退款、封号申诉与旧账号清理.pdf',
        '06-before-login.md': '05-注册与登录前自检.pdf',
        '07-apple-purchase-support.md': '06-Apple 购买受限与人工支持.pdf',
        '08-google-account.md': '07-Google 账号准备与两步验证.pdf',
        '09-vps-purchase.md': '08-VPS 注册与购买图解.pdf',
    }
    pdf_name = pdf_files.get(Path(item['reference']).name)
    pdf = ROOT / 'assets/reading' / pdf_name if pdf_name else None
    fallback = f'[打开对应图文 PDF](<{pdf.as_posix()}>)' if pdf and pdf.is_file() else ''
    message = item['instruction'] + ('\n\n' + '\n\n'.join(markup) if markup else '')
    if missing:
        message += '\n\n图片暂未能读取。' + (fallback or '先根据当前页面逐步说明。')
    return {'status': 'teaching', 'stage': stage, 'topic': topic, 'title': item['title'],
            'reference': item['reference'], 'customer_message': message, 'fallback_document': fallback,
            'customer_images': available,
            'image_markdown': markup,
            'missing_images': missing, 'step': step, 'total_steps': len(item['images']),
            'progress_unchanged': True,
            'display_instruction': POLICY + ' 将当前小步骤的 image_markdown 直接嵌入聊天；多步主题用 --step 选择当前页。'
            '缺图或显示失败时给出可打开的原文件／对应 PDF，继续用当前页面拆细指导；原图示例不覆盖现场值。',
            'resume_instruction': '讲解结束后回到原阶段，只提交实际完成的观察；已有等待与付款安排继续沿用。'}


def attach(result, state):
    from workflow_definition import facts
    stage, data = result.get('stage'), facts(state, result.get('stage'))
    result['teaching_instruction'] = POLICY
    result['help_command'] = 'python3 scripts/workflow.py guide --topic <主题ID> [--step <图片序号>]'
    result['help_catalog_command'] = 'python3 scripts/workflow.py guide'
    result['teaching_topics'] = [dict(id=k, title=v['title'], reference=v['reference'],
                                     images=v['images'], when=v['instruction'])
                                for k,v in CARDS.items() if stage in v['stages'] and eligible(k,state)]
    default = None
    if result.get('status') == 'needs_support' or data.get('purchase_restricted') is True:
        default = 'apple_support' if eligible('apple_support', state) else None
    elif result.get('status') != 'waiting':
        if stage == 'google' and data.get('account_origin') == 'purchased' and data.get('account_available') is True:
            default = 'google_materials'
        elif stage == 'google' and data.get('account_available') is False:
            default = {'chuhai91':'chuhai_register', 'gmailbuy':'gmailbuy'}.get(data.get('purchase_channel'))
        elif stage == 'browser':
            default = ('browser_profile' if not data.get('profile_ref') else
                       'browser_proxy' if not data.get('proxy_configured') else
                       'browser_fingerprint' if not data.get('fingerprint_configured') else None)
        elif stage == 'phone_proxy' and data.get('client_available') is False:
            default = 'apple_store' if data.get('account_origin') and eligible('apple_store',state) else None
        elif stage == 'payment_preparation' and eligible('apple_store',state) and data.get('store_signed_in') is not True:
            default = 'apple_store'
        elif stage == 'subscription':
            default = 'claude_subscribe' if data.get('order_confirmed') is not True and eligible('claude_subscribe',state) else None
        else:
            default = {'cleanup':'cleanup', 'vps':'network_basics', 'server':'server_panel',
                       'computer_network':'windows_client' if facts(state,'devices').get('computer')=='windows' else 'mac_client',
                       'phone_proxy':'phone_node' if eligible('phone_node',state) else 'android_phone',
                       'timezone':'timezone' if facts(state,'devices').get('phone')!='android' else 'android_phone',
                       'phone_network':'network_check', 'app':'claude_app' if eligible('claude_app',state) else 'android_phone',
                       'login':'google_login'}.get(stage)
    selected = data.get('teaching_topic')
    if (isinstance(selected, str) and selected in CARDS and stage in CARDS[selected]['stages'] and eligible(selected,state)
            and result.get('status') not in ('waiting', 'needs_support')
            and data.get('purchase_restricted') is not True
            and not (stage == 'subscription' and data.get('order_confirmed') is True)):
        default = selected
    if default and eligible(default,state):
        # A multi-page process starts with the relevant first page. Account material
        # explanation is one three-page lesson; it does not initiate account login.
        step = None if default == 'google_materials' or not CARDS[default]['images'] else 1
        if default == selected and data.get('teaching_step') is not None:
            step = data['teaching_step']
        result['default_teaching'] = guide(default,state,stage,step)
        result['customer_images'] = result['default_teaching']['customer_images'].copy()
        result['image_markdown'] = result['default_teaching']['image_markdown'].copy()
        result['missing_images'] = result['default_teaching']['missing_images'].copy()
        if not result.get('customer_message'):
            result['customer_message'] = result['default_teaching']['customer_message']
        elif result['default_teaching']['image_markdown']:
            result['customer_message'] += '\n\n' + '\n\n'.join(result['default_teaching']['image_markdown'])
        if result['default_teaching']['missing_images'] and result['default_teaching']['fallback_document']:
            result['customer_message'] += '\n\n图片暂未能读取，' + result['default_teaching']['fallback_document']
    result['display_instruction'] = result.get('display_instruction','') + ' ' + POLICY + ' 已到后续小步时，先用 guide 对应页替换阶段起点参考图，本轮只展示当前操作的图。'
    result['next_action'] += (' 按当前操作从 teaching_topics 选择对应图解并默认展示；default_teaching 是阶段起点参考，已有后续进度直接取对应小步。'
                              '确认当前小步后可提交 teaching_topic 与 teaching_step 保存位置；操作推进时更新这两个字段。用户说不会时用 guide 重新取图，已有展示标记不抑制重讲；主题不明确时结合上下文，只补问缺少的一点。')
    return result
