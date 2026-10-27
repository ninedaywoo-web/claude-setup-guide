"""Customer-facing copy returned at the step where it is needed."""
PDF_GUIDANCE = """**项目已经下载好了**，接下来 Codex 会按项目流程带您配置。

项目还附有一套**给您看的 PDF 图文教程**，包含操作步骤和基本原理。遇到问题先问 Codex；仍不明白，可以让它找到 PDF 对应的章节和页码，再对照图片查看。

**建议把 PDF 单独保存一份。需要我帮您放到“下载”文件夹吗？**文件已在项目里，无需重新下载。"""
GOOGLE_QUESTION = '您有没有自己能正常使用的 Google 账号？有的话直接沿用，后面用它登录 Claude。'
GOOGLE_PURCHASE = '需要买号时，**优先购买美区 Google 老号**。可以在 [出海91](https://chuhai91.cc) 或 [GmailBuy](https://gmailbuy.com/) 选择；先找“Google／谷歌老号”分类，再确认商品标明美区。商家页面和商品名称会变，我会按您当前看到的页面帮您选。购买后再带您看账号资料和登录时的两步验证。'
CUSTOMER_STYLE = '客户对话先给明确建议，再给当前操作和预期结果，用简短大白话。沿用项目推荐，避免叠加假设性风险、免责声明和重复提醒；实际异常说明具体原因与处理动作，客户主动问风险时准确回答。按当前步骤展示项目要求的等待、网络恢复和付款提醒。'
TASK_SCOPE = '围绕当前步骤处理问题。先明确现在要做的操作，结合用户的实际目的、项目上下文和授权范围判断并执行；遇到具体限制时说明对应步骤和可行替代方式，继续完成其他可独立开展的工作。准确描述用途与结果，保留真实上下文。'
GOOGLE_TIMING = '现在先准备账号资料，等手机网络配置完成后，再使用 Google 账号登录 Claude。'
ANDROID_GUIDANCE = """**安卓的适配程度较低，需要您更多地配合手机操作。**本项目的安卓付款备选是外区 Google Pay。先检查支付资料的国家／地区和可用付款方式；地区不合适时再按 Google 的实际页面处理地区设置。外区 Google 邮箱本身不等于已经具备付款条件。我们先确认这条路线，再配置网络；最终付款页实际显示 Google Pay 时继续。"""
ANDROID_PAYMENT = """安卓 Google Pay 路线的实际交付案例较少。作者收到过账号停用后无法通过此渠道退款的反馈，退款结果以支付渠道处理为准。请您确认接受这条路线，并核对当前付款页是否提供 Google Pay，再继续付款。"""
ACCOUNT_GUIDANCE = 'Google 账号用于登录 Claude；Apple 账号用于 App Store 下载、礼品卡充值和订阅付款。后续在电脑上登录 Claude，沿用手机上使用的同一个 Google 账号。'
BROWSER_GUIDANCE = """**AdsPower 指纹浏览器，是给 Claude 准备的独立登录环境。**它把相关登录记录和浏览器设置与日常上网分开。处理网页登录、相关邮件链接或 Claude Code 授权链接时，在这个环境里完成；登录授权完成后，回到电脑的 Claude 桌面端或 CLI 使用。"""
VPS_GUIDANCE = """VPS 就是您租用的一台远程服务器，我们把它配置成自己的魔法节点。您在网站完成购买，Codex 会接着帮您部署，再把电脑和手机连接到这条线路。这里准备的是自己的节点，平时购买的共享梯子套餐另作配置期间的联网工具。

您目前是还没买 VPS、已买但没配置，还是已经有可用的自建节点？已有的可以先核对并复用；没有就跟着下面的图解准备。"""
VPS_PURCHASE_GUIDANCE = '需要购买时，默认按 **DMIT → 搬瓦工 → AKILE** 选：先看 DMIT 洛杉矶 AN5 Premium，缺货看搬瓦工 USCA_9 的 1 GB 档，搬瓦工也缺货再看 AKILE LAXPremium-Mini。默认分别按月付、季付、月付准备；我会在下单前列清本次实际付款总额、覆盖时长和续费金额。'
NETWORK_GUIDANCE = '电脑上的代理客户端负责连接 VPS 节点。TUN 负责接管电脑流量，全局模式让流量走选定的节点；我们会先保留旧 VPN，单独测通新节点，再切换并确认 Codex 能继续回复。'
PHONE_GUIDANCE = '手机主要承担首次登录和订阅付款。我们先给手机配置好网络，再通过 Claude 的 iOS 内购完成订阅，之后回电脑的 Claude 桌面端或 CLI 使用。Apple 负责这笔内购订单，后续需要申请退款，也从 Apple 的入口处理。'
CHECK_GUIDANCE = '这三个网站用来查看当前网络出口和检测分数。电脑先检查一次，手机配好后再检查一次，确认两台设备使用的是我们配置的目标线路，再继续登录和订阅。'
GIFT_GUIDANCE = '礼品卡就是给 Apple 账户充值的卡。接下来的顺序是：购买与 Apple 账户地区对应的礼品卡 → 在 App Store 兑换到账户余额 → 打开 Claude 选择 Pro，用 Apple 余额支付。已有足够余额就直接用；完成后核对订单和会员权益，再回电脑使用。'
APPLE_PURCHASE_GUIDANCE = '需要购买 Apple 账号时，可选 [出海91](https://chuhai91.cc) 或 [新太科技](https://xintaikeji.eu.org/)，这条内购路线选美区账号，按我们的选购经验优先挑使用时间较长的老号。商家页面和套餐经常变动，按地区、使用时间和售后说明选择。新购买的老号也按刚接手账号安排下面的约两天等待。'
APPLE_ACCOUNT_QUESTION = """这套 iPhone 订阅路线使用美区 Apple 账户。您现在有没有可用账户？有的话，是您一直自己使用的账号、新注册的，还是刚购买／刚接手的？卖家称为“老号”的成品号，只要您刚接手，也按新接手账号准备。"""
APPLE_GUIDANCE = """🔴 **新买或新注册的 Apple ID：强烈建议先养约两天，再充值、购买或订阅！**

**先在您自己的手机 App Store／“媒体与购买项目”成功登录一次，从这次登录完成起正常使用约两天，期间暂不充值或订阅，也先不买礼品卡和付费 App。不要登录 iCloud，也不要替换原有 iCloud 账号。**

**根据实际交付反馈，刚拿到账号就立即充值、付款，更容易遇到苹果风控／购买限制。受限后可能需要找苹果人工客服申诉，常见还要等待 72 小时才能重试，很耽误时间；实际时长按本次客服答复。**

约两天是我们的交付经验建议，不是苹果公布的保证。正常使用、留出时间即可，无需专门买东西或反复登录退出。默认按建议等待；如果您明确希望现在继续，我会记录您的选择。"""
APPLE_PAYMENT_RECHECK = """🔴 **付款前再确认一次：新注册或新购买的 Apple ID，强烈建议从本人手机 App Store 首次登录成功起等约两天，再充值、购买或订阅。**立即付款可能遇到苹果风控，后续可能需要人工申诉及等待重试。沿用已记录的首次登录时间和您的等待选择。"""
FINISH_GUIDANCE = """**手机订单和当前账号的 Pro 权益已确认。**手机主要用于登录和订阅，日常在电脑的 Claude 桌面端或 Claude Code／CLI 使用，登录刚才同一个 Google 账号。需要网页登录或授权时，将相关链接放到已配置的 AdsPower 环境完成，再回到桌面端或 CLI。

**使用经验提醒**
- 可以把每五小时额度约用到 70% 作为个人使用节奏建议；这个比例不是平台公布的封号阈值。
- 发送项目或资料前，留意内容里是否包含不必要的精确定位信息，先去掉再分享。
- 作者对生物医药、网络安全等话题的提醒属于个人使用经验。按平台规则正常使用；这些话题本身不代表会导致封号。

遇到问题先问 Codex；仍需人工帮助时，让它整理当前步骤、报错和已尝试的办法，再把诊断说明发给我们。也可以让 Codex 定位 PDF 对应章节和页码。"""


def customer_output(result, state, now):
    from workflow_definition import APPLE_OPTIONAL, OPTIONAL_FIELDS, facts, apple_wait, timestamp
    result['communication_instruction'] = CUSTOMER_STYLE
    result['task_scope_instruction'] = TASK_SCOPE
    key = result.get('stage')
    device = facts(state, 'devices')
    data = facts(state, key)
    messages = []
    if key == 'intake':
        result['customer_message'] = '先确认一件事：您准备使用的电脑或手机，之前有没有登录过被 Claude 封禁的账号？'
    if key == 'cleanup':
        messages.append('如果您的设备是 iPhone，且还装着此前使用的 Claude App，建议删除后重新下载，您可以自行安排。电脑按实际系统处理适用的登录残留。')
    if key == 'google':
        messages.append(ACCOUNT_GUIDANCE if device.get('phone') != 'android' else 'Google 账号用于登录 Claude。手机完成登录和订阅后，电脑的 Claude 桌面端或 CLI 也沿用同一个 Google 账号。')
        if data.get('account_available') is not False:
            messages.append(GOOGLE_QUESTION)
        messages.extend([GOOGLE_PURCHASE, GOOGLE_TIMING])
        result['next_action'] = ('在对话展示账号准备说明：已有可用 Google 账号就复用；没有则先明确推荐“优先购买美区 Google 老号”，再提供购买渠道。'
                                 '客户问买哪个时主动按实际页面定位老号分类并核对美区，看到商品信息就直接推荐符合条件的选项；缺信息只补商品名称或商品页截图。'
                                 '按 references/08-google-account.md 指导账号资料和两步验证。本流程不引导注册 Google 账号。'
                                 '确认账号已备妥后提交 account_available=true；实际登录留到手机网络验收后。')
    if key == 'vps':
        messages.extend([VPS_GUIDANCE, VPS_PURCHASE_GUIDANCE])
        result['next_action'] = ('VPS 选型直接按默认洛杉矶机房与目标套餐推进，不询问用户主要在哪个国家或地区使用、所在地、城市或运营商。'
                                 'node_timezone 从所选节点机房城市取得，已有 VPS 读取实际节点资料；用户主动提出特殊需求时按其需求调整。'
                                 '先核对已有 VPS 并复用；需要购买时按 DMIT → 搬瓦工 → AKILE 核对目标套餐，前一家缺货再看下一家。'
                                 '默认付款周期为 DMIT 月付、搬瓦工季付、AKILE 月付，按当前结账页说明实际扣款总额、覆盖时长和续费金额；'
                                 '年付或多年预付只在用户明确要求时比较。三家都缺货则确认等待或在这三家内比较其他同线路套餐。'
                                 '已有客户选择按其要求继续；准备好 VPS 与 SSH 访问后提交本阶段观察。')
    if key == 'computer_network':
        messages.append(NETWORK_GUIDANCE)
        if device.get('computer') == 'windows':
            result['troubleshooting'] = {
                'reference': 'references/10-windows.md#61-http-测通tun-后反复连接-vps',
                'trigger': '本机 HTTP 代理已测通，开启 TUN 后断网、测速一直测试中，或反复出现 accepted tcp:<VPS_IP>:443 [socks -> proxy]。',
                'action': '优先按 6.1 节检查节点自身连接的防回环规则、实际核心进程与物理网卡出口；先保留恢复方式，按当前版本做精确调整，每步复测。',
                'status': '客户反馈案例，疑似回环；尚未收到修复结果。',
            }
            result['next_action'] += '。出现 troubleshooting.trigger 中的现象时，立即读取其 reference 并执行排查；依据实测结果提交网络观察。'

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
    if key == 'browser' and data.get('usage_explained') is not True:
        messages.append(CHECK_GUIDANCE)
    if key == 'phone_proxy':
        messages.append(PHONE_GUIDANCE if device.get('phone') != 'android' else '接下来把手机连接到电脑使用的同一条节点线路，验收后在手机浏览器登录和订阅。完成后回电脑的 Claude 桌面端或 CLI 使用。')
    if key == 'phone_network':
        messages.append(CHECK_GUIDANCE)
        if device.get('computer') == 'windows' and device.get('phone') in ('iphone', 'ipad'):
            messages.append('**接下来请您在 iPhone／iPad 上验收网络。**Windows 无法使用 Apple 原生手机镜像，这一步由您在手机操作，我根据您反馈的页面和结果逐项核对。')
        else:
            messages.append('**接下来在手机上独立验收网络。**有可用的手机操作工具时我会协助完成；需要您手动操作时，按下面步骤反馈结果。')
        messages.append('**先核对实际出口：**保持手机目标节点连接，在手机浏览器打开 [Ping0](https://ping0.cc/)，查看当前公网出口 IP。将它与电脑已验收的 AdsPower 出口、VPS 目标线路对照；核对实际地址与线路，同一个 Wi-Fi、相同节点名称或相同城市都不能代替出口核对。')
        messages.append('**再在这台手机上完成三个检测：**\n'
                        '- [NetCoffee](https://ip.net.coffee/claude/)：记录分数，参考约 80 分或更高。\n'
                        '- [Ping0](https://ping0.cc/)：记录风险值，参考低于 30、优先低于 25。\n'
                        '- [Scamalytics](https://scamalytics.com/ip)：查询刚才手机实际出口 IP，记录风险值，参考低于 10。')
        messages.append('**请先反馈手机 Ping0 页面截图，并说明现在用的是 Wi-Fi 还是蜂窝网络。**接着逐站提供另外两个检测页面，或清楚告知各站实际分数、检测时间及出口对照结果。截图遮住账号、密码和节点链接；完整 IP 对照留在本机，进度仅保存脱敏结果。手机结果独立记录，电脑分数不代填。')
        messages.append('三个网站拿到实际结果、出口核对完成后，再补齐手机 DNS、IPv6、排除路由和断线检查。检测打不开或没出分时，先处理当前问题；只显示 VPN 已连接还不算验收完成。切换 Wi-Fi／蜂窝网络后，使用前补检新网络。')
        result['next_action'] = ('在客户对话展示手机验收步骤和三站链接，先取得手机 Ping0 页面及网络类型，再逐站收集结果。'
                                 '将手机实际出口与电脑 AdsPower、目标 VPS 对照；依据手机页面或用户明确反馈提交，source.reference 写明实际反馈来源。'
                                 '三站均取得数值、实际出口一致且其余检查完成后继续；缺项留在手机验收。')
    if key in ('browser', 'phone_network'):
        bands = result.get('score_advice', {})
        if 'unverified' in bands.values():
            messages.append('还有检测网站未取得分数，请先补齐实际检测结果；未验证不能记为通过。')
        if 'recheck_recommended' in bands.values():
            messages.append('三站结果有明显偏离。先复查实际出口和检测结果；复查后继续或由您明确选择继续，我会记录处理结果。这些分数是参考值。')
    if key == 'phone_proxy' and device.get('phone') != 'android':
        messages.append('先确认您是否已有可用的小火箭。有就直接使用，无需重复购买；没有且需要用新 Apple ID 购买，先在 App Store 登录并查看新号等待安排。')
    if key == 'timezone':
        result['next_action'] = ('在客户对话展示当前电脑和手机的时区、定位设置步骤。已有时区选择直接沿用；'
                                 '尚未选择先确认跟随节点或台北，再完成设置、核对电脑／手机／AdsPower 一致，按实际结果提交。')
        if data.get('choice') in ('node', 'taipei'):
            target = 'Asia/Taipei' if data['choice'] == 'taipei' else facts(state, 'vps').get('node_timezone', '节点所在城市')
            messages.append('**接下来统一电脑、手机和浏览器的时区，并按设备设置定位权限。**沿用您已选的时区：' + target + '，AdsPower 也采用相同时区。')
        else:
            messages.append('**接下来统一电脑、手机和浏览器的时区，并按设备设置定位权限。**推荐跟随 VPS 节点所在城市；想保留东八区作息也可以选台北。您选哪一种？电脑、手机和 AdsPower 会统一按这个选择设置。')
        if device.get('computer') == 'windows':
            messages.append('**Windows 电脑：**打开「设置 → 时间和语言 → 日期和时间」，关闭「自动设置时区」，手动选择刚才确定的时区，保留「自动设置时间」，按所选地区处理夏令时。然后打开 Windows 11 的「设置 → 隐私和安全性 → 位置」（Windows 10 为「设置 → 隐私 → 位置」），关闭设备定位服务。')
        else:
            messages.append('**Mac 电脑：**打开「系统设置 → 通用 → 日期与时间」，关闭自动设置时区，选择确定的城市，保留自动设置日期与时间。再到「隐私与安全性 → 定位服务 → 系统服务 → 详细信息」关闭「设定时区」。Mac 的定位服务总开关保持原有状态；Claude 网页的位置权限设为禁止，核对 AdsPower 地理位置为「禁止」。')
        if device.get('phone') == 'android':
            messages.append('**安卓手机：**在设置中搜索「日期和时间」，关闭「自动设置时区／使用网络提供的时区」，手动选择确定的地区与时区，保留自动设置日期和时间。如果页面另有「使用位置信息设置时区」，也将它关闭。再在设置中搜索「位置／定位服务」，关闭「使用位置信息」总开关。不同品牌菜单名称不同，Codex 会按您的实际系统版本指导操作。')
        else:
            messages.append('**iPhone／iPad：**打开「设置 → 通用 → 日期与时间」，关闭「自动设置」，选择确定的时区城市。再到「隐私与安全性 → 定位服务 → 系统服务」关闭「设定时区」，返回关闭定位服务总开关。')
        messages.append('设置后返回页面核对实际时区和定位开关，并核对 AdsPower 的时区与地理位置「禁止」。系统语言可以保留中文；关闭定位会影响地图等依赖位置的功能。')
    apple_stage = key in ('phone_proxy', 'payment_preparation') and device.get('phone') != 'android'
    if apple_stage:
        result['account_history'] = state.get('apple_accounts', {})
        if key == 'payment_preparation':
            result['early_account_observation'] = facts(state, 'phone_proxy').get('apple_account_ref')
        preparing = key == 'payment_preparation' or data.get('client_available') is False or data.get('account_type') is not None
        if preparing and not data.get('account_origin'):
            messages.extend([APPLE_ACCOUNT_QUESTION, APPLE_PURCHASE_GUIDANCE])
            result['next_action'] = ('先在对话确认 Apple 账号来源，再安排充值或购买；记录 account_origin：self_used 为本人原先在用，'
                                     'newly_registered 为新注册，purchased 为新购买／新接手。后两者统一按新号处理，展示醒目提醒后再记录 apple_reminder_shown。')
        if data.get('account_type') == 'new' and data.get('apple_reminder_shown') is not True:
            messages.append(APPLE_GUIDANCE)
        elif preparing and data.get('account_type') == 'new':
            messages.append(APPLE_PAYMENT_RECHECK)
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
    if key == 'subscription' and device.get('phone') != 'android' and data.get('order_confirmed') is not True and data.get('purchase_restricted') is not True:
        if facts(state, 'payment_preparation').get('account_type') == 'new':
            messages.append(APPLE_PAYMENT_RECHECK)
    if key == 'payment_preparation' and device.get('phone') != 'android':
        if result.get('status') not in ('waiting', 'needs_support'):
            messages.append('先确认 Apple 账号和等待安排，准备好后按下面流程充值和订阅。' + GIFT_GUIDANCE)
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
        result['display_instruction'] = '把 customer_message 直接展示在客户对话中；相应说明完成后再记录展示字段。首次进入当前阶段时先展示用途解释，再带做当前操作；同一阶段连续操作复用已讲过的解释，客户追问时再展开。遵循 communication_instruction，先建议后动作，简短说明。'
        if APPLE_PAYMENT_RECHECK in messages:
            result['display_instruction'] += '付款复查提醒在进入当前阶段时展示一次，同一阶段连续操作且账号与等待选择未变时不重复。'
    return result
