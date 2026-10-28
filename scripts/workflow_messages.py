"""Customer-facing copy returned at the step where it is needed."""
PDF_GUIDANCE = """**项目已经下载好了**，接下来 Codex 会按项目流程带您配置。

项目还附有一套**给您看的 PDF 图文教程**，包含操作步骤和基本原理。遇到问题先问 Codex；仍不明白，可以让它找到 PDF 对应的章节和页码，再对照图片查看。

**建议把 PDF 单独保存一份。需要我帮您放到“下载”文件夹吗？**文件已在项目里，无需重新下载。"""
GOOGLE_QUESTION = '您有没有能正常登录 Claude、没有被 Claude 封禁的 Google 账号？有的话直接沿用。'
GOOGLE_PURCHASE = """需要买号时，**优先购买美区 Google 老号**，这两个网站都可以选：

- 首选 [出海91](https://chuhai91.cc/)：按我们的选购经验，价格相对贵一点，账号也相对稳一点。
- [GmailBuy](https://gmailbuy.com/)：价格相对便宜一点，按我们的选购经验，被封的可能性也大一点。

看您个人选择。选出海91的话，先用您自己的邮箱注册网站账号，QQ 邮箱也可以；已有网站账号就直接登录。然后进入「Google 谷歌账户 → 谷歌精品老号」，优先选标明“美国 IP 创建／注册”的老号，按当前价格和库存选择。我会按图一步步带您操作，购买后继续看账号资料和登录时的两步验证。"""
GOOGLE_MATERIALS_GUIDANCE = '收到账号资料后，先找到 Google 邮箱、登录密码，以及商家标注的“2FA 密钥”。2FA 密钥是一串用来生成登录验证码的字母和数字。取码网址是 [2FA 取码工具：https://2fa.run/](https://2fa.run/)。等手机网络配置完成、Google 登录页面要求身份验证器验证码时，再按图用密钥生成验证码，并填回手机登录页面。'
GOOGLE_LOGIN_GUIDANCE = '手机网络已经验收完成，接下来在手机上使用准备好的 Google 账号登录 Claude。按当前页面输入账号和密码；Google 要求身份验证器验证码时，再按下面的取码步骤操作。'
GOOGLE_VERIFICATION_GUIDANCE = '取码入口：[2FA 取码工具：https://2fa.run/](https://2fa.run/)。使用商家提供的 2FA 密钥时，在已配置好的 AdsPower 中打开网站，将密钥填入上方“JS实现”区域，点击“点击获取验证码”，再把当前验证码填回手机 Google 页面。使用自己的 Google 账号时，也可以从自己已绑定的身份验证器取得验证码；其他验证方式按当前页面完成。'
GOOGLE_ORDER_IMAGES = ['assets/google-account/01-order-original.png']
GOOGLE_VERIFICATION_IMAGES = ['assets/google-account/02-2fa-original.png', 'assets/google-account/03-google-code-original.png']
GOOGLE_PURCHASE_IMAGES = {
    'register': 'assets/chuhai91/01-register.png',
    'category': 'assets/chuhai91/02-google-aged-category.png',
    'product': 'assets/chuhai91/03-us-ip-product.png',
}
CUSTOMER_STYLE = '客户对话先给明确建议，再给当前操作和预期结果，用简短大白话。沿用项目推荐，避免叠加假设性风险、免责声明和重复提醒；实际异常说明具体原因与处理动作，客户主动问风险时准确回答。按当前步骤展示项目要求的等待、网络恢复和付款提醒。'
TASK_SCOPE = '围绕当前步骤处理问题。先明确现在要做的操作，结合用户的实际目的、项目上下文和授权范围判断并执行；遇到具体限制时说明对应步骤和可行替代方式，在当前阶段内继续完成能做的操作，验收通过后再进入下一步。准确描述用途与结果，保留真实上下文。'
GOOGLE_TIMING = '现在先准备账号资料，等手机网络配置完成后，再使用 Google 账号登录 Claude。'
ANDROID_GUIDANCE = """**安卓的适配程度较低，需要您更多地配合手机操作。**本项目的安卓付款备选是外区 Google Pay。先检查支付资料的国家／地区和可用付款方式；地区不合适时再按 Google 的实际页面处理地区设置。外区 Google 邮箱本身不等于已经具备付款条件。我们先确认这条路线，再配置网络；最终付款页实际显示 Google Pay 时继续。"""
ANDROID_PAYMENT = """安卓 Google Pay 路线的实际交付案例较少。作者收到过账号停用后无法通过此渠道退款的反馈，退款结果以支付渠道处理为准。请您确认接受这条路线，并核对当前付款页是否提供 Google Pay，再继续付款。"""
ACCOUNT_GUIDANCE = 'Google 账号用于登录 Claude；Apple 账号用于 App Store 下载、礼品卡充值和订阅付款。后续在电脑上登录 Claude，沿用手机上使用的同一个 Google 账号。'
BROWSER_GUIDANCE = """**这套流程完成后，您可以用 Claude 桌面版，也可以用 Claude Code。**先分清这三个工具：

- **Claude 桌面版**：就是下载安装到电脑上的 Claude 软件，打开软件就能和 Claude 对话。
- **Claude Code（CLI）**：这里说的是在电脑“终端”里使用的 Claude 编程工具，主要用来帮您写代码、改项目。
- **AdsPower 指纹浏览器**：就是我们现在要配置的浏览器，给 Claude 准备一个独立登录环境。

**AdsPower 什么时候用？**按本教程，电脑浏览器中所有需要登录 Claude 账号的场景，都在这个已配置好的 AdsPower 环境里完成。比如网页登录、邮件里的登录链接，或 Claude 桌面版、Claude Code 弹出的浏览器授权链接，都放到这里打开。登录或授权完成后，回到原来的 Claude 软件或终端继续使用。

**关于 Claude 桌面版，您需要知道这两点：**
- 有人担心，Claude 桌面版可能要求更多电脑权限、读取更多设备信息，从而增加账号被封的风险。
- 我们已经交付的用户中，也有不少人反馈：一直在用 Claude 桌面版，目前使用正常。

这两方面都告诉您，具体用 Claude 桌面版还是 Claude Code，按您的使用需要和接受程度来选。"""
VPS_GUIDANCE = """VPS 就是您租用的一台远程服务器，我们把它配置成自己的魔法节点。您在网站完成购买，Codex 会接着帮您部署，再把电脑和手机连接到这条线路。这里准备的是自己的节点，平时购买的共享梯子套餐另作配置期间的联网工具。

您目前是还没买 VPS、已买但没配置，还是已经有可用的自建节点？已有的可以先核对并复用；没有就跟着下面的图解准备。"""
VPS_PURCHASE_GUIDANCE = '需要购买时，默认按 **DMIT → 搬瓦工 → AKILE** 选：先看 DMIT 洛杉矶 AN5 Premium，缺货看搬瓦工 USCA_9 的 1 GB 档，搬瓦工也缺货再看 AKILE LAXPremium-Mini。默认分别按月付、季付、月付准备；我会在下单前列清本次实际付款总额、覆盖时长和续费金额。'
NETWORK_GUIDANCE = '电脑上的代理客户端负责连接 VPS 节点。TUN 负责接管电脑流量，全局模式让流量走选定的节点；我们会先保留旧 VPN，单独测通新节点，再切换并确认 Codex 能继续回复。'
PHONE_GUIDANCE = '手机主要承担首次登录和订阅付款。我们先给手机配置好网络，再通过 Claude 的 iOS 内购完成订阅，之后回电脑的 Claude 桌面端或 CLI 使用。Apple 负责这笔内购订单，后续需要申请退款，也从 Apple 的入口处理。'
CHECK_GUIDANCE = '配好后，我会带您用 [NetCoffee](https://ip.net.coffee/claude/)、[Ping0](https://ping0.cc/) 和 [Scamalytics](https://scamalytics.com/ip) 这三个网站检查网络。电脑先检查一次，手机配好后再检查一次，确认两台设备都在使用我们配置的目标线路，再继续登录和订阅。'
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
        result['next_action'] = ('按 references/04-recovery.md 核对实际使用范围，执行适用的平台清理或浏览器站点清理。'
                                 '用当前 ticket 提交实际 outcome 和 handled_scope，再按返回的当前阶段继续。'
                                 '首次交付接回设备搭配与阅读版说明 → Google 账号准备 → VPS；恢复交付复用已有结果，只补当前缺项。'
                                 '客户说“先配置电脑”表示操作顺序，后续仍须完成手机网络、手机登录和订阅。')
    if key == 'google':
        messages.append(ACCOUNT_GUIDANCE if device.get('phone') != 'android' else 'Google 账号用于登录 Claude。手机完成登录和订阅后，电脑的 Claude 桌面端或 CLI 也沿用同一个 Google 账号。')
        available = data.get('account_available')
        channel = data.get('purchase_channel')
        result['account_materials_message'] = GOOGLE_MATERIALS_GUIDANCE
        result['account_materials_images'] = GOOGLE_ORDER_IMAGES.copy()
        if available is True:
            messages.append(GOOGLE_MATERIALS_GUIDANCE)
            result['customer_images'] = GOOGLE_ORDER_IMAGES.copy()
            result['next_action'] = ('在当前回复直接展示 customer_message 中的 2FA 取码链接，并将 customer_images 转为当前项目的绝对路径嵌入聊天。'
                                     '解释邮箱、密码及商家标注的密钥用途后，直接提交 materials_explained=true，按返回任务继续；这一步由 Codex 展示完成，无需客户额外确认。')
        else:
            if available is not False:
                messages.append(GOOGLE_QUESTION)
            elif channel == 'gmailbuy':
                messages.append('沿用您选择的 [GmailBuy](https://gmailbuy.com/)，优先购买美区 Google 老号。我会按您当前的商品页核对美区、老号、价格和库存。')
            elif channel == 'chuhai91':
                messages.append('沿用您选择的 [出海91](https://chuhai91.cc/)，按图继续：用自己的邮箱注册网站账号（QQ 邮箱也可以）→ Google 谷歌账户 → 谷歌精品老号 → 选择美国 IP 创建／注册的老号。已完成的步骤接着往下做。')
            else:
                messages.append(GOOGLE_PURCHASE)
            messages.append(GOOGLE_TIMING)
            if available is False and channel != 'gmailbuy':
                result['purchase_images'] = dict(GOOGLE_PURCHASE_IMAGES)
            result['next_action'] = ('先单独确认有没有能正常登录 Claude、没有被 Claude 封禁的 Google 账号；确认可复用后提交 account_origin=self_used 与 account_available=true。账号复用以 Claude 的可用状态为准。Google／Gmail 能登录，但对应的 Claude 账号已被封禁时，记录 account_available=false，继续准备其他可用账号；若后来找回的账号也已被 Claude 封禁，同样按此处理。尚未用过 Claude 的 Google 账号先确认既有情况，实际登录仍留到手机网络验收后，不为回答这个问题提前登录。'
                                     '没有则先明确推荐“优先购买美区 Google 老号”，同时展示出海91与GmailBuy两个可点击链接和选购差别；已有 purchase_channel 时沿用选择。'
                                     '客户选择后记录 purchase_channel=chuhai91 或 gmailbuy。客户问买哪个时按实际页面定位老号分类并核对美区，按当前价格与库存推荐。'
                                     '选择出海91时，按 references/08-google-account.md 的三步图示逐步带做并展示对应本地图片；从 purchase_images 取当前步骤，将路径转为项目绝对路径嵌入聊天。选择 GmailBuy 时按该网站页面带做。'
                                     '注册的是购物网站账号，本流程不引导注册 Google 账号。客户说买好并收到资料时，提交 account_origin=purchased 与 account_available=true，程序将返回资料说明、取码链接和原账号资料图。'
                                     '若先前没有账号、后来找回自己的可用账号，则明确提交 account_origin=self_used 继续复用。实际登录留到手机网络验收后。')
    if key == 'login':
        messages.extend([GOOGLE_LOGIN_GUIDANCE, GOOGLE_VERIFICATION_GUIDANCE])
        result['verification_images'] = GOOGLE_VERIFICATION_IMAGES.copy()
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
        if not device.get('computer'):
            messages.append('您准备配置的电脑是 Mac 还是 Windows？')
        if not device.get('phone'):
            messages.append('我们先配置电脑，随后完成手机网络、手机登录和订阅。后续您准备用 iPhone、iPad 还是安卓手机？')
        if device.get('setup_explained') is True and device.get('pdf_explained') is not True:
            messages.append(PDF_GUIDANCE)
            result['next_action'] = '在对话展示 PDF 用途和另存询问后，提交 pdf_explained=true。未回答另存可记 unanswered，继续配置。'
        result['next_action'] += (' 按实际回答补齐 missing 中的电脑、手机及说明字段；“先配置电脑”只确定顺序，继续确认缺少的手机类型。'
                                  '本阶段完成后按返回任务准备 Google 账号，确认可用后再进入 VPS。')
        if device.get('phone') == 'android' and device.get('android_route_explained') is not True:
            messages.append(ANDROID_GUIDANCE)
    if key in ('browser', 'login'):
        field = 'usage_explained' if key == 'browser' else 'browser_notice_shown'
        if data.get(field) is not True:
            messages.append(BROWSER_GUIDANCE)
    if key == 'browser' and data.get('usage_explained') is not True:
        messages.append(CHECK_GUIDANCE)
    if key == 'browser':
        result['next_action'] += ' 电脑 AdsPower 验收后提交实际结果，接续 phone_proxy → timezone → phone_network，再完成手机登录和订阅。'
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
    if key in ('phone_proxy', 'phone_network') and device.get('phone') in ('iphone', 'ipad'):
        result['manual_guidance'] = {
            'backup_reference': 'references/02-browser-iphone.md#224-windowsiphone保存配置与按目标恢复',
            'dns_reference': 'references/02-browser-iphone.md#225-dns-添加输入加入列表保存回读',
            'action': '按当前设备页面带做，每轮 1～3 个相连动作并说明可见结果。修改前记录原值和恢复目标；节点导入资料与 DNS／分流配置分别保存，复制到剪贴板后还要保存并重新打开核对。DNS 列表界面输入后点绿色＋，看到独立条目及红色－后保存，退出重开回读，再重连复测。当前正常时沿用原值；菜单与教程不同先读取页面。恢复目标冲突时先核对已执行动作，再继续。',
        }
        result['next_action'] += ' 需要保存配置、恢复原值或修改 DNS 时，先读取 manual_guidance 的对应章节；按当前动作逐轮展示，回读保存结果后再做联网复测。'
        if device.get('computer') == 'windows':
            result['communication_instruction'] += (' Windows＋iPhone／iPad 每轮先标明操作设备；电脑展示节点二维码与整理资料，手机执行小火箭、Safari、微信操作。'
                                                      '每轮给 1～3 个相连动作与预期结果。默认在手机本地保存配置；Wi-Fi 上传持续超时就回到手机保存。')
            if key == 'phone_proxy':
                messages.append('**接下来在 iPhone／iPad 上操作。**我会在 Windows 电脑上打开节点二维码，您用手机小火箭扫描；导入后我先帮您核对首页刚新增的那一行，再带您连接。每次完成当前几步，我们看一下页面再继续。')
    if key in ('phone_proxy', 'phone_network') and device.get('phone') in ('iphone', 'ipad'):
        result['application_troubleshooting'] = {
            'reference': 'references/02-browser-iphone.md#223-节点可用只有微信图片打不开',
            'trigger': '目标节点的 HTTPS 与出口检测正常，只有微信图片等单个应用请求异常；或客户反馈最初仅微信异常，后续调整导致整体失联。',
            'action': '整体失联时先恢复最后可用配置并验证 HTTPS 与目标出口，再处理微信分流。使用「配置」模式，核对实际加载的规则，让微信走直连（DIRECT），Claude 相关流量继续走原目标节点；已有正确规则复用，需要补充时只改相关规则并核对匹配优先级。保持节点参数与服务端原样。保存加载后查看实际请求命中，复测微信图片发送／加载与原网络；无改善恢复本次改动，原网络变差立即回到最后可用状态。此情形不触发 TLS 指纹尝试或断线测试。',
        }
        result['troubleshooting'] = {
            'reference': 'references/02-browser-iphone.md#222-断线测试后恢复端口手机仍无法联网',
            'trigger': 'Shadowrocket 在断线测试、改端口或切换配置后，恢复操作完成但实际网页仍打不开。',
            'action': '先读取恢复步骤，回读当前选中节点保存后的原端口和参数；保留 DNS 与微信规则，按实际模式做代理对照，验证新的 IPv4 HTTPS 请求和出口。仍失败再核对连接日志与服务端当前监听。先恢复已知改动，再考虑 TLS 指纹案例。',
            'status': '完整对话末尾客户确认网页与微信图片恢复；断线测试后恢复失败的具体原因未查明，恢复后参数和最新出口待回读。',
        }
        result['next_action'] += ' 微信单项异常或为修微信而越调越坏时，读取 application_troubleshooting；当前整体失联先恢复可用网络，再落实微信直连分流。出现 troubleshooting.trigger 时，先读取对应章节并恢复实际连接；恢复后的 HTTPS 与出口核对完成，再记录断线检查结果并继续验收。'
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
    if key != 'google' and device.get('phone') == 'android':
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
        if result.get('customer_images'):
            result['display_instruction'] += ' 同条回复把 customer_images 转为项目绝对路径并嵌入图片，展示后再提交 materials_explained=true。'
        if key == 'login':
            result['display_instruction'] += ' 当前已进入登录阶段。Google 页面要求身份验证器验证码时，直接展示取码链接，并把 verification_images 转为项目绝对路径嵌入聊天；按实际验证方式继续。'
        if APPLE_PAYMENT_RECHECK in messages:
            result['display_instruction'] += '付款复查提醒在进入当前阶段时展示一次，同一阶段连续操作且账号与等待选择未变时不重复。'
    return result
