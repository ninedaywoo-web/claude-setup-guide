"""Customer-facing copy returned at the step where it is needed."""
PDF_GUIDANCE = """**项目已经下载好了**，接下来 Codex 会按项目流程带您配置。

项目还附有一套**给您看的 PDF 图文教程**，包含操作步骤和基本原理。遇到问题先问 Codex；仍不明白，可以让它找到 PDF 对应的章节和页码，再对照图片查看。

**建议把 PDF 单独保存一份。需要我帮您放到“下载”文件夹吗？**文件已在项目里，无需重新下载。"""
ANDROID_GUIDANCE = """**安卓的适配程度较低，需要您更多地配合手机操作。**本项目的安卓付款备选是外区 Google Pay。先检查支付资料的国家／地区和可用付款方式；地区不合适时再按 Google 的实际页面处理地区设置。外区 Google 邮箱本身不等于已经具备付款条件。我们先确认这条路线，再配置网络；最终付款页实际显示 Google Pay 时继续。"""
ANDROID_PAYMENT = """安卓 Google Pay 路线的实际交付案例较少。作者收到过账号停用后无法通过此渠道退款的反馈，退款结果以支付渠道处理为准。请您确认接受这条路线，并核对当前付款页是否提供 Google Pay，再继续付款。"""
BROWSER_GUIDANCE = """**电脑上请使用已配置好的 AdsPower 打开 Claude。**相关邮件中的链接也放到这个浏览器环境处理。以后如需 Claude Code 网页授权，把弹出的授权链接复制到这个环境中打开。"""
VPS_GUIDANCE = """VPS 就是您租用的一台远程服务器，这里用它搭建自己的魔法节点。购买普通梯子套餐和已经搭建好自己的节点，是两回事。

您目前是还没买 VPS、已买但没配置，还是已经有可用的自建节点？已有的可以先核对并复用；没有就跟着下面的图解准备。"""
APPLE_GUIDANCE = """🔴 **新 Apple ID 提醒**

**先在您自己的手机 App Store 登录成功一次，再预留约两天。**等待从这次登录完成开始计算，建议期间**暂不充值或订阅**。外区账号只用于 App Store／媒体与购买项目，**不要登录 iCloud**。

约两天是我们的交付经验建议。默认按建议等待；如果您明确希望现在继续，也可以告诉我。"""
FINISH_GUIDANCE = """**手机订单和当前账号的 Pro 权益已确认。**手机主要用于登录和订阅，日常请回电脑的 AdsPower，使用刚才同一个 Google 账号。

**使用经验提醒**
- 可以把每五小时额度约用到 70% 作为个人使用节奏建议；这个比例不是平台公布的封号阈值。
- 发送项目或资料前，留意内容里是否包含不必要的精确定位信息，先去掉再分享。
- 作者对生物医药、网络安全等话题的提醒属于个人使用经验。按平台规则正常使用；这些话题本身不代表会导致封号。

遇到问题先问 Codex；仍需人工帮助时，让它整理当前步骤、报错和已尝试的办法，再把诊断说明发给我们。也可以让 Codex 定位 PDF 对应章节和页码。"""


def customer_output(result, state, now):
    from workflow_definition import APPLE_OPTIONAL, OPTIONAL_FIELDS, facts, apple_wait, timestamp
    key = result.get('stage')
    device = facts(state, 'devices')
    data = facts(state, key)
    messages = []
    if key == 'intake':
        result['customer_message'] = '先确认一件事：您准备使用的电脑或手机，之前有没有登录过被 Claude 封禁的账号？'
    if key == 'cleanup':
        messages.append('如果您的设备是 iPhone，且还装着此前使用的 Claude App，建议删除后重新下载，您可以自行安排。电脑按实际系统处理适用的登录残留。')
    if key == 'vps':
        messages.append(VPS_GUIDANCE)
    if key == 'devices':
        if device.get('setup_explained') is True and device.get('pdf_explained') is not True:
            messages.append(PDF_GUIDANCE)
            result['next_action'] = '在对话展示 PDF 用途和另存询问后，提交 pdf_explained=true。未回答另存可记 unanswered，继续配置。'
        if device.get('phone') == 'android' and device.get('android_route_explained') is not True:
            messages.append(ANDROID_GUIDANCE)
    if key in ('browser', 'login'):
        field = 'usage_explained' if key == 'browser' else 'browser_notice_shown'
        if data.get(field) is not True:
            messages.append(BROWSER_GUIDANCE)
    if key in ('browser', 'phone_network'):
        bands = result.get('score_advice', {})
        if 'recheck_recommended' in bands.values():
            messages.append('三站结果有明显偏离。先复查实际出口和检测结果；复查后继续或由您明确选择继续，我会记录处理结果。这些分数是参考值。')
    if key == 'phone_proxy' and device.get('phone') != 'android':
        messages.append('先确认您是否已有可用的小火箭。有就直接使用，无需重复购买；没有且需要用新 Apple ID 购买，先在 App Store 登录并查看新号等待安排。')
    if key == 'timezone':
        result['next_action'] = '沿用已选时区，展示当前设备的设置入口，再核对电脑、手机和 AdsPower 一致。'
        if device.get('computer') == 'windows' or device.get('phone') == 'android':
            messages.append('Windows／安卓的固定图解步骤正在补充。Codex 会按您实际系统版本查找时区和定位入口，或带您在系统设置中搜索；找到并展示实际路径后再记录完成。')
    apple_stage = key in ('phone_proxy', 'payment_preparation') and device.get('phone') != 'android'
    if apple_stage:
        result['account_history'] = state.get('apple_accounts', {})
        if key == 'payment_preparation':
            result['early_account_observation'] = facts(state, 'phone_proxy').get('apple_account_ref')
        if data.get('account_type') == 'new' and data.get('apple_reminder_shown') is not True:
            messages.append(APPLE_GUIDANCE)
        until = apple_wait(data, now) if data.get('purchase_restricted') is not True else None
        if until:
            result.update(status='waiting', resume_at=until,
                          next_action='先展示建议继续时间，再安排付款准备；保留首次登录起点。客户明确选择现在继续时提交 wait_choice=continue。', allowed_actions=[])
            messages.append('建议继续时间：' + until + '。起点是您在自己手机 App Store 首次登录完成的时间。')
    if key in ('phone_proxy', 'payment_preparation', 'subscription') and device.get('phone') != 'android':
        if data.get('purchase_restricted') is True:
            result.update(status='needs_support', reference='references/07-apple-purchase-support.md',
                          next_action='立即切到 Apple 人工支持申诉流程，由 Codex 打开支持页面并协助操作，记录客服案件和实际重试安排。', allowed_actions=[])
            result.pop('resume_at', None)
            retry = data.get('support_retry_at')
            if retry:
                try:
                    if timestamp(retry) > now:
                        result.update(status='waiting', resume_at=retry)
                except (ValueError, TypeError, AttributeError):
                    pass
            messages.append('购买受限先按人工支持流程处理。客服给出的重试安排单独记录，不用新号约两天的建议代替客服安排。')
    if key == 'payment_preparation' and device.get('phone') == 'android':
        messages.append(ANDROID_PAYMENT)
    if key == 'subscription' and data.get('order_confirmed') is True and data.get('pro_visible') is True and data.get('purchase_restricted') is not True:
        if data.get('handoff_explained') is not True:
            messages.append(FINISH_GUIDANCE)
            result['next_action'] = '订阅已确认；在对话展示使用提示和经验，再提交 handoff_explained=true 完成交付。'
    if key is None:
        messages.append(FINISH_GUIDANCE)
    optional = dict(OPTIONAL_FIELDS.get(key, {}))
    if device.get('phone') == 'android':
        optional = {k: v for k, v in optional.items() if k not in APPLE_OPTIONAL and k != 'client_available'}
    if optional:
        result['optional_fields'] = optional
        for name in result.get('missing', []):
            if name in optional:
                result['submission']['data'][name] = None
    if messages:
        existing = result.get('customer_message')
        result['customer_message'] = '\n\n'.join(([existing] if existing else []) + messages)
        result['display_instruction'] = '把 customer_message 直接展示在客户对话中；相应说明完成后再记录展示字段。'
    return result
