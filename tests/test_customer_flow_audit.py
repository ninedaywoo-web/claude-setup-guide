"""Adversarial paths for the agreed 22 delivery corrections."""
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import test_workflow as fixtures
from workflow import Workflow, WorkflowError
from workflow_teaching import GOOGLE_IMAGES
from workflow_definition import catalog


class CustomerFlowAudit(fixtures.WorkflowTests):
    # Reuse the isolated state machine fixture, not live devices/accounts.
    def test_browser_cleanup_then_computer_first_still_prepares_phone_and_google(self):
        self.flow.submit(self.payload({'banned_login': 'yes'}))
        self.assertIn('Google 账号准备 → VPS', self.flow.next()['next_action'])
        self.flow.submit(self.payload({'outcome': 'cleaned',
            'handled_scope': 'Customer confirmed Claude site data cleared in Chrome and Firefox'}))
        self.assertEqual(self.flow.next()['stage'], 'devices')
        self.flow.submit(self.payload({'computer': 'windows'}))
        self.flow = Workflow(self.root, lambda: self.now)
        view = self.flow.next()
        self.assertEqual(view['stage'], 'devices')
        self.assertIn('phone', view['missing'])
        self.assertIn('iPhone、iPad 还是安卓手机', view['customer_message'])
        self.assertIn('手机网络、手机登录和订阅', view['customer_message'])
        premature = self.payload(self.data('vps'))
        premature['stage'] = 'vps'
        with self.assertRaises(WorkflowError):
            self.flow.submit(premature)
        self.flow.submit(self.payload({'setup_explained': True, 'pdf_explained': True}))
        self.assertIn('iPhone、iPad 还是安卓手机', self.flow.next()['customer_message'])
        self.flow.submit(self.payload({'phone': 'iphone'}))
        self.assertEqual(self.flow.next()['stage'], 'google')
        self.assertIn('您有没有能正常登录 Claude、没有被 Claude 封禁的 Google 账号', self.flow.next()['customer_message'])
        self.flow.submit(self.payload({'account_available': False}))
        self.assertEqual(self.flow.next()['stage'], 'google')
        self.flow.submit(self.payload({'account_available': True}))
        if self.flow.next()['stage'] == 'google':
            self.assertIn('materials_explained', self.flow.next()['missing'])
            self.flow.submit(self.payload({'materials_explained': True, 'materials_images_shown': GOOGLE_IMAGES.copy()}))
        self.assertEqual(self.flow.next()['stage'], 'vps')

    def test_cleanup_outcomes_keep_phone_network_login_and_subscription_in_delivery(self):
        for computer, phone, outcome in (('mac', 'iphone', 'cleaned'),
                ('windows', 'iphone', 'deferred'), ('mac', 'ipad', 'not_applicable'),
                ('windows', 'android', 'cleaned')):
            with self.subTest(computer=computer, phone=phone, outcome=outcome):
                case = fixtures.WorkflowTests()
                case.setUp()
                try:
                    case.computer, case.phone = computer, phone
                    case.flow.submit(case.payload({'banned_login': 'yes'}))
                    case.flow.submit(case.payload({'outcome': outcome, 'handled_scope': 'Actual cleanup scope recorded'}))
                    case.reach('browser')
                    self.assertIn('phone_proxy → timezone → phone_network', case.flow.next()['next_action'])
                    case.advance()
                    for stage in ('phone_proxy', 'timezone', 'phone_network'):
                        self.assertEqual(case.flow.next()['stage'], stage)
                        premature = case.payload(case.data('login'))
                        premature['stage'] = 'login'
                        with self.assertRaises(WorkflowError):
                            case.flow.submit(premature)
                        if stage == 'phone_network':
                            partial = case.data(stage)
                            partial['exit_matches'] = False
                            case.flow.submit(case.payload(partial))
                            self.assertEqual(case.flow.next()['stage'], stage)
                        case.advance()
                    for stage in ('payment_preparation', 'app', 'login', 'subscription'):
                        self.assertEqual(case.flow.next()['stage'], stage)
                        case.advance()
                    self.assertIsNone(case.flow.next().get('stage'))
                finally:
                    case.doCleanups()

    def test_cleanup_on_resume_reuses_device_and_google_observations(self):
        self.flow.submit(self.payload({'banned_login': 'yes'}))
        self.reach('browser')
        self.flow.invalidate('cleanup', 'Recheck actual browser login residue')
        self.assertEqual(self.flow.next()['stage'], 'cleanup')
        self.flow.submit(self.payload({'outcome': 'cleaned', 'handled_scope': 'Selected browser site data'}))
        self.flow = Workflow(self.root, lambda: self.now)
        self.assertEqual(self.flow.next()['stage'], 'browser')
        self.advance()
        self.assertEqual(self.flow.next()['stage'], 'phone_proxy')

    def test_purchased_materials_survive_submit_restart_and_duplicate(self):
        self.reach('google')
        self.flow.submit(self.payload({'account_available': False}))
        bought = self.payload({'account_available': True})
        view = self.flow.submit(bought)
        self.assertEqual(view['stage'], 'google')
        self.assertEqual(view['observed']['account_origin'], 'purchased')
        self.assertIn('materials_explained', view['missing'])
        self.assertIn('https://2fa.run/', view['customer_message'])
        self.assertEqual(view['customer_images'], GOOGLE_IMAGES)
        self.assertNotIn('购买美区', view['customer_message'])
        self.flow = Workflow(self.root, lambda: self.now)
        self.assertEqual(self.flow.submit(bought)['customer_message'], view['customer_message'])
        shown = self.payload({'materials_explained': True, 'materials_images_shown': GOOGLE_IMAGES.copy()})
        self.assertEqual(self.flow.submit(shown)['stage'], 'vps')
        self.assertEqual(self.flow.submit(shown)['stage'], 'vps')

    def test_google_account_origin_and_materials_on_android(self):
        self.phone = 'android'
        self.reach('google')
        self.assertIn('account_origin', self.flow.next()['optional_fields'])
        self.flow.submit(self.payload({'account_available': False, 'purchase_channel': 'gmailbuy'}))
        view = self.flow.submit(self.payload({'account_available': True, 'account_origin': 'purchased'}))
        self.assertEqual(view['stage'], 'google')
        self.assertIn('https://2fa.run/', view['customer_message'])
        self.flow.submit(self.payload({'materials_explained': True, 'materials_images_shown': GOOGLE_IMAGES.copy()}))
        self.assertEqual(self.flow.next()['stage'], 'vps')
        self.flow.invalidate('google', 'Recovered own account for Android')
        view = self.flow.submit(self.payload({'account_available': True, 'account_origin': 'self_used'}))
        self.assertEqual(view['stage'], 'vps')

    def test_direct_purchased_account_receives_materials_before_vps(self):
        self.reach('google')
        view = self.flow.submit(self.payload({'account_origin': 'purchased', 'account_available': True}))
        self.assertEqual(view['stage'], 'google')
        self.assertIn('https://2fa.run/', view['customer_message'])
        self.assertIn('customer_images', view)
        self.flow.submit(self.payload({'materials_explained': True, 'materials_images_shown': GOOGLE_IMAGES.copy()}))
        self.assertEqual(self.flow.next()['stage'], 'vps')

    def test_recovered_personal_account_skips_purchase_materials(self):
        self.reach('google')
        self.flow.submit(self.payload({'account_available': False, 'purchase_channel': 'chuhai91'}))
        view = self.flow.submit(self.payload({'account_available': True, 'account_origin': 'self_used'}))
        self.assertEqual(view['stage'], 'vps')
        self.assertNotIn('purchase_channel', self.flow.state['records']['google']['data'])

    def test_seller_choice_survives_resume_and_can_change(self):
        self.reach('google')
        self.flow.submit(self.payload({'account_available': False, 'purchase_channel': 'gmailbuy'}))
        self.flow = Workflow(self.root, lambda: self.now)
        view = self.flow.next()
        self.assertIn('[GmailBuy](https://gmailbuy.com/)', view['customer_message'])
        self.assertNotIn('出海91', view['customer_message'])
        self.assertNotIn('purchase_images', view)
        view = self.flow.submit(self.payload({'purchase_channel': 'chuhai91'}))
        self.assertIn('QQ 邮箱也可以', view['customer_message'])
        self.assertEqual(set(view['purchase_images']), {'register', 'category', 'product'})

    def test_login_guidance_uses_current_stage_and_actual_verification(self):
        self.reach('login')
        view = self.flow.next()
        self.assertIn('手机网络已经验收完成', view['customer_message'])
        self.assertNotIn('等手机网络配置完成', view['customer_message'])
        self.assertNotIn('收到账号资料后', view['customer_message'])
        self.assertIn('自己的 Google 账号', view['customer_message'])
        self.assertIn('已绑定的身份验证器', view['customer_message'])
        self.assertEqual(len(view['verification_images']), 2)
        self.assertIn('实际验证方式', view['display_instruction'])

    def test_cleanup_branches_all_devices_keep_new_route_boundaries(self):
        for computer in ('mac', 'windows'):
            for phone in ('iphone', 'ipad', 'android'):
                for ban, outcome in (('no', None), ('unknown', None), ('yes', 'cleaned'),
                                     ('yes', 'deferred'), ('yes', 'not_applicable')):
                    with self.subTest(computer=computer, phone=phone, ban=ban, outcome=outcome):
                        case = fixtures.WorkflowTests(); case.setUp()
                        try:
                            case.computer, case.phone = computer, phone
                            case.flow.submit(case.payload({'banned_login': ban}))
                            if outcome:
                                case.flow.submit(case.payload({'outcome': outcome, 'handled_scope': 'Isolated actual scope'}))
                            self.assertEqual(case.flow.next()['stage'], 'devices')
                            case.reach('google')
                            self.assertIn('您有没有', case.flow.next()['customer_message'])
                            case.reach('browser')
                            case.advance()
                            for expected in ('phone_proxy', 'timezone', 'phone_network'):
                                case.flow = Workflow(case.root, lambda: case.now)
                                self.assertEqual(case.flow.next()['stage'], expected)
                                invalid = case.payload(case.data('login')); invalid['stage'] = 'login'
                                with self.assertRaises(WorkflowError): case.flow.submit(invalid)
                                case.advance()
                            self.assertEqual(case.flow.next()['stage'], 'payment_preparation')
                        finally: case.doCleanups()

    def test_browser_explanation_survives_partial_resume_and_stops_repeating(self):
        self.reach('browser')
        self.flow.submit(self.payload({'profile_ref': 'profile-a', 'saved': True}))
        self.flow = Workflow(self.root, lambda: self.now)
        message = self.flow.next()['customer_message']
        for phrase in ('Claude 桌面版', 'Claude Code', '有人担心', '目前使用正常', 'https://ping0.cc/'):
            self.assertIn(phrase, message)
        self.flow.submit(self.payload({'usage_explained': True}))
        self.assertNotIn('有人担心', self.flow.next().get('customer_message', ''))
        self.advance()
        self.assertEqual(self.flow.next()['stage'], 'phone_proxy')

    def test_phone_disconnect_restore_guidance_stays_at_failed_stage(self):
        self.computer = 'windows'
        self.reach('phone_proxy')
        view = self.flow.next()
        self.assertIn('断线测试', view['troubleshooting']['trigger'])
        self.assertIn('先恢复已知改动', view['troubleshooting']['action'])
        self.reach('phone_network')
        data = self.data('phone_network')
        data.update(https_ok=False, disconnect_checked=False)
        self.flow.submit(self.payload(data))
        self.flow = Workflow(self.root, lambda: self.now)
        view = self.flow.next()
        self.assertEqual(view['stage'], 'phone_network')
        self.assertIn('https_ok', view['missing'])
        self.assertIn('disconnect_checked', view['missing'])
        self.assertIn('恢复后的 HTTPS 与出口核对完成', view['next_action'])
        self.assertTrue((Path(__file__).resolve().parents[1] / view['troubleshooting']['reference'].split('#')[0]).is_file())
        self.advance()
        self.assertEqual(self.flow.next()['stage'], 'payment_preparation')

    def test_wechat_only_failure_keeps_working_node_and_separate_recovery_path(self):
        self.reach('phone_proxy')
        for stage in ('phone_proxy', 'phone_network'):
            self.reach(stage)
            view = self.flow.next()
            case = view['application_troubleshooting']
            self.assertIn('HTTPS 与出口检测正常', case['trigger'])
            self.assertIn('保持节点参数与服务端原样', case['action'])
            self.assertIn('微信走直连（DIRECT）', case['action'])
            self.assertIn('Claude 相关流量继续走原目标节点', case['action'])
            self.assertIn('查看实际请求命中', case['action'])
            self.assertLess(case['action'].index('先恢复最后可用配置'), case['action'].index('再处理微信分流'))
            self.assertIn('后续调整导致整体失联', case['trigger'])
            self.assertIn('不触发 TLS 指纹尝试或断线测试', case['action'])
            self.assertIn('原网络变差立即回到最后可用状态', case['action'])
            self.assertNotEqual(case['reference'], view['troubleshooting']['reference'])
            self.assertTrue((Path(__file__).resolve().parents[1] / case['reference'].split('#')[0]).is_file())

    def test_manual_phone_guidance_survives_failure_and_resume(self):
        self.computer, self.phone = 'windows', 'iphone'
        self.reach('phone_proxy')
        view = self.flow.next()
        self.assertIn('Windows 电脑上打开节点二维码', view['customer_message'])
        self.assertIn('每轮先标明操作设备', view['communication_instruction'])
        self.reach('phone_network')
        data = self.data('phone_network')
        data.update(https_ok=False, dns_checked=False)
        self.flow.submit(self.payload(data))
        self.flow = Workflow(self.root, lambda: self.now)
        view = self.flow.next()
        self.assertEqual(view['stage'], 'phone_network')
        self.assertIn('dns_checked', view['missing'])
        self.assertIn('manual_guidance', view['next_action'])
        guidance = view['manual_guidance']
        self.assertIn('绿色＋', guidance['action'])
        self.assertIn('退出重开回读', guidance['action'])
        for key in ('backup_reference', 'dns_reference'):
            path = Path(__file__).resolve().parents[1] / guidance[key].split('#')[0]
            self.assertTrue(path.is_file())
        self.advance()
        self.assertEqual(self.flow.next()['stage'], 'payment_preparation')
        self.assertNotIn('manual_guidance', self.flow.next())

    def test_android_does_not_receive_shadowrocket_recovery_steps(self):
        self.phone = 'android'
        self.reach('phone_network')
        self.assertNotIn('troubleshooting', self.flow.next())
        self.assertNotIn('application_troubleshooting', self.flow.next())
        self.assertNotIn('manual_guidance', self.flow.next())

    def test_windows_tun_case_is_available_on_failure_and_resume(self):
        self.computer = 'windows'
        self.reach('computer_network')
        view = self.flow.next()
        self.assertIn('6.1', view['troubleshooting']['action'])
        self.assertIn('socks -> proxy', view['troubleshooting']['trigger'])
        self.assertTrue((Path(__file__).resolve().parents[1] / view['troubleshooting']['reference'].split('#')[0]).exists())
        data = self.data('computer_network')
        data.update(https_ok=False, exit_matches=False, codex_reply_received=False)
        self.flow.submit(self.payload(data))
        resumed = Workflow(self.root).next()
        self.assertEqual(resumed['stage'], 'computer_network')
        self.assertIn('troubleshooting', resumed)
        self.assertIn('https_ok', resumed['missing'])
        self.assertIn('exit_matches', resumed['missing'])
        self.assertIn('codex_reply_received', resumed['missing'])
        self.flow.submit(self.payload(self.data('computer_network')))
        self.assertEqual(self.flow.next()['stage'], 'browser')
        self.assertNotIn('troubleshooting', self.flow.next())

    def test_scope_guidance_preserves_opening_and_mac_network(self):
        view = self.flow.next()
        self.assertEqual(view['stage'], 'intake')
        self.assertIn('封禁', view['customer_message'])
        self.assertIn('真实上下文', view['task_scope_instruction'])
        self.reach('computer_network')
        self.assertNotIn('troubleshooting', self.flow.next())
        self.assertIn('旧 VPN', self.flow.next()['customer_message'])

    def test_beginner_explanations_follow_each_platform_stage(self):
        for computer, phone in (('mac', 'iphone'), ('windows', 'iphone'), ('windows', 'android')):
            with self.subTest(computer=computer, phone=phone):
                case = fixtures.WorkflowTests()
                case.setUp()
                try:
                    case.computer, case.phone = computer, phone
                    expected = [
                        ('google', ('Google 账号用于登录', '同一个 Google 账号')),
                        ('vps', ('远程服务器', '网站完成购买')),
                        ('computer_network', ('TUN', '旧 VPN', '单独测通')),
                        ('browser', ('独立登录环境', '登录链接', '授权链接', '桌面版', '三个网站')),
                        ('phone_proxy', ('手机', '订阅', '桌面端')),
                        ('phone_network', ('三个网站', '目标线路')),
                        ('payment_preparation', ('Google Pay',) if phone == 'android' else ('礼品卡就是', '账户余额', '等待安排')),
                    ]
                    for stage, phrases in expected:
                        case.reach(stage)
                        view = case.flow.next()
                        for phrase in phrases:
                            self.assertIn(phrase, view['customer_message'])
                        self.assertIn('首次进入当前阶段', view['display_instruction'])
                        self.assertIn('communication_instruction', view['display_instruction'])
                        self.assertIn('先给明确建议', view['communication_instruction'])
                        if stage == 'browser':
                            self.assertIn('电脑浏览器中所有需要登录 Claude 账号的场景', view['customer_message'])
                            self.assertIn('有人担心，Claude 桌面版可能', view['customer_message'])
                            self.assertIn('一直在用 Claude 桌面版，目前使用正常', view['customer_message'])
                            self.assertIn('下载安装到电脑上的 Claude 软件', view['customer_message'])
                            self.assertIn('电脑“终端”里使用的 Claude 编程工具', view['customer_message'])
                            self.assertIn('关于 Claude 桌面版', view['customer_message'])
                            for site in ('https://ip.net.coffee/claude/', 'https://ping0.cc/', 'https://scamalytics.com/ip'):
                                self.assertIn(site, view['customer_message'])
                        if phone == 'android':
                            self.assertNotIn('Apple 账号用于', view['customer_message'])
                            self.assertNotIn('iOS 内购', view['customer_message'])
                            self.assertNotIn('礼品卡就是', view['customer_message'])
                    case.reach('subscription')
                    self.assertNotIn('权益已确认', case.flow.next().get('customer_message', ''))
                    case.advance()
                    message = case.flow.next()['customer_message']
                    self.assertIn('Claude 桌面端或 Claude Code／CLI', message)
                    self.assertIn('授权', message)
                    self.assertNotIn('日常请回电脑的 AdsPower', message)
                finally:
                    case.doCleanups()

    def test_apple_wait_and_support_keep_payment_explanation_at_right_time(self):
        self.reach('payment_preparation')
        self.flow.submit(self.payload({'account_origin': 'purchased', 'account_type': 'new',
            'apple_account_ref': 'new-account', 'store_signed_in': True,
            'first_used_at': self.now.isoformat(), 'apple_reminder_shown': True}))
        view = self.flow.next()
        self.assertEqual(view['status'], 'waiting')
        self.assertNotIn('礼品卡就是', view['customer_message'])
        self.now += timedelta(hours=49)
        self.flow = Workflow(self.root, lambda: self.now)
        self.assertIn('礼品卡就是', self.flow.next()['customer_message'])
        self.flow.submit(self.payload({'purchase_restricted': True}))
        self.assertEqual(self.flow.next()['status'], 'needs_support')
        self.assertNotIn('礼品卡就是', self.flow.next()['customer_message'])

    def test_google_preparation_shows_reuse_purchase_and_login_timing(self):
        self.reach('google')
        view = self.flow.next()
        self.assertIn('能正常登录 Claude、没有被 Claude 封禁', view['customer_message'])
        self.assertIn('Google／Gmail 能登录，但对应的 Claude 账号已被封禁', view['next_action'])
        self.assertIn('记录 account_available=false', view['next_action'])
        self.assertIn('不为回答这个问题提前登录', view['next_action'])
        self.assertIn('直接沿用', view['customer_message'])
        for url in ('https://chuhai91.cc', 'https://gmailbuy.com/'):
            self.assertNotIn(url, view['customer_message'])
        self.flow.submit(self.payload({'account_available': False}))
        for url in ('https://chuhai91.cc/', 'https://gmailbuy.com/'):
            self.assertIn(url, self.flow.next()['customer_message'])
        self.assertIn('手机网络配置完成后', view['customer_message'])
        self.assertIn('直接展示', view['display_instruction'])
        self.assertIn('不引导注册 Google 账号', view['next_action'])

    def test_google_missing_account_keeps_purchase_route_on_resume(self):
        self.reach('google')
        self.flow.submit(self.payload({'account_available': False}))
        view = Workflow(self.root).next()
        self.assertEqual(view['stage'], 'google')
        self.assertIn('购买', view['customer_message'])
        self.assertIn('**优先购买美区 Google 老号**', view['customer_message'])
        self.assertIn('首选 [出海91]', view['customer_message'])
        self.assertIn('QQ 邮箱也可以', view['customer_message'])
        self.assertIn('Google 谷歌账户 → 谷歌精品老号', view['customer_message'])
        self.assertIn('美国 IP 创建／注册', view['customer_message'])
        self.assertIn('当前价格和库存', view['customer_message'])
        self.assertIn('价格相对贵一点', view['customer_message'])
        self.assertIn('被封的可能性也大一点', view['customer_message'])
        self.assertIn('看您个人选择', view['customer_message'])
        self.assertIn('[GmailBuy](https://gmailbuy.com/)', view['customer_message'])
        self.assertIn('[2FA 取码工具：https://2fa.run/](https://2fa.run/)', view['account_materials_message'])
        self.assertIn('客户说买好并收到资料时', view['next_action'])
        self.assertIn('展示对应本地图片', view['next_action'])
        self.assertIn('先明确推荐', view['next_action'])
        self.assertIn('按实际页面定位老号分类并核对美区', view['next_action'])
        self.assertIn('避免叠加假设性风险', view['communication_instruction'])
        self.assertNotIn('您有没有', view['customer_message'])
        self.flow.submit(self.payload({'account_available': True}))
        if self.flow.next()['stage'] == 'google':
            self.assertIn('materials_explained', self.flow.next()['missing'])
            self.flow.submit(self.payload({'materials_explained': True, 'materials_images_shown': GOOGLE_IMAGES.copy()}))
        self.assertEqual(self.flow.next()['stage'], 'vps')

    def test_existing_google_account_advances_without_purchase_requirement(self):
        self.reach('google')
        self.flow.submit(self.payload({'account_available': True, 'account_origin': 'self_used'}))
        self.assertEqual(self.flow.next()['stage'], 'vps')
        self.reach('login')
        self.assertTrue(self.flow.next()['next_action'].startswith('使用 Google 账号登录 Claude'))
        self.assertIn('[2FA 取码工具：https://2fa.run/](https://2fa.run/)', self.flow.next()['customer_message'])

    def test_pdf_unanswered_does_not_block_after_display(self):
        self.reach('devices')
        self.flow.submit(self.payload({'computer':'mac','phone':'iphone','setup_explained':True}))
        self.assertIn('给您看的 PDF',self.flow.next()['customer_message'])
        self.flow.submit(self.payload({'pdf_explained':True,'pdf_save_choice':'unanswered'}))
        self.assertEqual(self.flow.next()['stage'],'google')
        self.assertEqual(Workflow(self.root).next()['stage'],'google')

    def test_android_first_response_before_vps_contains_payment_and_limits(self):
        self.reach('devices')
        self.flow.submit(self.payload({'computer':'windows','phone':'android'}))
        view=self.flow.next()
        self.assertIn('外区 Google Pay',view['customer_message'])
        self.assertIn('适配程度较低',view['customer_message'])
        self.assertIn('android_route_explained',view['missing'])
        self.assertIn('payment_route_status',view['missing'])
        self.assertNotIn('apple_account_ref',view['required_fields'])

    def test_timezone_messages_match_all_device_combinations(self):
        for computer, phone in (('windows', 'android'), ('windows', 'iphone'), ('mac', 'android'), ('mac', 'iphone')):
            with self.subTest(computer=computer, phone=phone):
                case = fixtures.WorkflowTests()
                case.setUp()
                try:
                    case.computer, case.phone = computer, phone
                    case.reach('phone_proxy'); case.advance()
                    view = case.flow.next()
                    self.assertEqual(view['stage'], 'timezone')
                    msg = view['customer_message']
                    self.assertIn('按设备设置定位权限', msg)
                    self.assertIn('Windows 11' if computer == 'windows' else 'Mac 电脑', msg)
                    self.assertIn('使用网络提供的时区' if phone == 'android' else 'iPhone／iPad', msg)
                    self.assertEqual('computer_location_off' in view['required_fields'], computer == 'windows')
                    self.assertIn('phone_location_off', view['required_fields'])
                    self.assertIn('直接展示', view['display_instruction'])
                    if phone == 'android':
                        self.assertNotIn('phone_timezone_location_off', view['required_fields'])
                    case.advance()
                    self.assertEqual(case.flow.next()['stage'], 'phone_network')
                finally:
                    case.doCleanups()

    def test_mac_global_location_is_not_required_but_timezone_and_web_permission_are(self):
        self.reach('timezone')
        view = self.flow.next()
        self.assertNotIn('computer_location_off', view['required_fields'])
        self.assertIn('computer_timezone_location_off', view['required_fields'])
        mac_text = view['customer_message'].split('**Mac 电脑：**')[1].split('**iPhone')[0]
        self.assertIn('总开关保持原有状态', mac_text)
        self.assertNotIn('关闭定位服务总开关', mac_text)
        data = self.data('timezone')
        data.update(computer_location_off=False, computer_timezone_location_off=False, browser_location_blocked=False)
        self.flow.submit(self.payload(data))
        resumed = Workflow(self.root).next()
        self.assertEqual(set(resumed['missing']), {'computer_timezone_location_off', 'browser_location_blocked'})
        self.flow.submit(self.payload({'computer_timezone_location_off': True, 'browser_location_blocked': True}))
        self.assertEqual(self.flow.next()['stage'], 'phone_network')

    def test_windows_old_progress_requires_missing_location_and_reuses_timezone(self):
        self.computer, self.phone, self.choice = 'windows', 'android', 'taipei'
        self.reach('timezone')
        data = self.data('timezone'); data.pop('computer_location_off')
        self.flow.submit(self.payload(data))
        view = Workflow(self.root).next()
        self.assertEqual(view['stage'], 'timezone')
        self.assertEqual(view['missing'], ['computer_location_off'])
        self.assertIn('沿用您已选的时区：Asia/Taipei', view['customer_message'])
        self.assertNotIn('您选哪一种', view['customer_message'])
        self.flow.submit(self.payload({'computer_location_off': False}))
        self.assertEqual(self.flow.next()['stage'], 'timezone')
        self.flow.submit(self.payload({'computer_location_off': True}))
        self.assertEqual(self.flow.next()['stage'], 'phone_network')

    def test_android_phone_and_timezone_reference_platform_guide(self):
        self.phone='android';self.computer='windows'
        for stage in ('phone_proxy','timezone'):
            self.reach(stage)
            self.assertEqual(self.flow.next()['reference'],'references/11-android-web-pay.md')
        self.assertIn('实际系统版本',self.flow.next()['customer_message'])

    def test_apple_preparation_first_message_asks_source_before_payment(self):
        self.reach('payment_preparation')
        view = self.flow.next()
        self.assertIn('account_origin', view['missing'])
        self.assertIn('刚购买／刚接手', view['customer_message'])
        self.assertIn('卖家称为', view['customer_message'])
        data = self.data('payment_preparation'); data.pop('account_origin')
        self.flow.submit(self.payload(data))
        self.assertEqual(self.flow.next()['stage'], 'payment_preparation')
        self.assertIn('account_origin', self.flow.next()['missing'])

    def test_purchased_seller_old_account_gets_new_account_warning_and_wait(self):
        self.reach('payment_preparation')
        data = self.data('payment_preparation')
        data.update(account_origin='purchased', account_type='longstanding', first_used_at=self.now.isoformat())
        self.flow.submit(self.payload(data))
        view = self.flow.next()
        self.assertEqual(view['observed']['account_type'], 'new')
        self.assertEqual(view['status'], 'waiting')
        for text in ('强烈建议', '新买或新注册', '两天', '苹果风控', '人工客服', '72 小时', '不要登录 iCloud'):
            self.assertIn(text, view['customer_message'])
        self.assertIn('apple_reminder_shown', view['missing'])

    def test_missing_shadowrocket_prompts_apple_source_and_new_registration_warning(self):
        self.reach('phone_proxy')
        self.flow.submit(self.payload({'client_available': False}))
        self.assertIn('刚购买／刚接手', self.flow.next()['customer_message'])
        self.assertIn('account_origin', self.flow.next()['missing'])
        self.flow.submit(self.payload({'account_origin': 'newly_registered', 'account_type': 'longstanding'}))
        view = self.flow.next()
        self.assertEqual(view['observed']['account_type'], 'new')
        self.assertIn('先不买礼品卡和付费 App', view['customer_message'])
        self.assertIn('first_used_at', view['missing'])

    def test_new_account_payment_recheck_and_subscription_reminder(self):
        self.account_type = 'new'
        self.reach('payment_preparation')
        data = self.data('payment_preparation'); data.update(account_origin='purchased', payment_ready=False)
        self.flow.submit(self.payload(data))
        self.assertIn('付款前再确认一次', self.flow.next()['customer_message'])
        self.assertEqual(self.flow.next()['stage'], 'payment_preparation')
        self.flow.submit(self.payload({'payment_ready': True}))
        self.reach('subscription')
        self.assertIn('付款前再确认一次', self.flow.next()['customer_message'])
        self.advance()
        self.assertEqual(self.flow.next()['status'], 'complete')

    def test_existing_longstanding_account_and_android_skip_new_account_warning(self):
        self.reach('payment_preparation')
        data = self.data('payment_preparation'); data['payment_ready'] = False
        self.flow.submit(self.payload(data))
        self.assertNotIn('强烈建议', self.flow.next().get('customer_message', ''))
        self.flow.invalidate('devices', 'switch to Android')
        self.phone = 'android'; self.computer = 'windows'
        self.reach('payment_preparation')
        self.assertNotIn('account_origin', self.flow.next()['required_fields'])
        self.assertNotIn('Apple ID', self.flow.next().get('customer_message', ''))

    def test_new_apple_wait_without_gift_card_or_reminder_ack(self):
        self.reach('payment_preparation')
        data=self.data('payment_preparation')
        data.update(account_type='new',first_used_at=self.now.isoformat(),payment_ready=False)
        self.flow.submit(self.payload(data));view=self.flow.next()
        self.assertEqual(view['status'],'waiting')
        self.assertEqual(view['resume_at'],(self.now+timedelta(hours=48)).isoformat())
        self.assertIn('apple_reminder_shown',view['missing'])
        self.assertIn('不要登录 iCloud',view['customer_message'])
        self.assertIn('暂不充值',view['customer_message'])
        self.assertEqual(self.flow.state['apple_accounts'][data['apple_account_ref']]['first_used_at'],data['first_used_at'])

    def test_customer_can_continue_wait_but_not_skip_payment_or_other_checks(self):
        self.reach('payment_preparation')
        data=self.data('payment_preparation');data.update(account_type='new',first_used_at=self.now.isoformat(),payment_ready=False,apple_reminder_shown=True)
        self.flow.submit(self.payload(data))
        with self.assertRaises(WorkflowError):self.flow.submit(self.payload({'wait_choice':'continue'}))
        p=self.payload({'wait_choice':'continue'});p['source']={'kind':'user','reference':'客户明确选择立即继续'}
        self.flow.submit(p)
        self.assertEqual(self.flow.next()['status'],'active')
        self.assertEqual(self.flow.next()['missing'],['payment_ready'])
        self.flow.submit(self.payload({'payment_ready':True}))
        self.assertEqual(self.flow.next()['stage'],'app')

    def test_early_shadowrocket_purchase_wait_and_formal_reuse(self):
        self.reach('phone_proxy')
        self.flow.submit(self.payload({'client_available':False,'apple_account_ref':'early-a','account_origin':'purchased','account_type':'new',
            'store_signed_in':True,'first_used_at':self.now.isoformat(),'apple_reminder_shown':True}))
        self.assertEqual(self.flow.next()['status'],'waiting')
        self.now+=timedelta(hours=49)
        phone_data = self.data('phone_proxy')
        phone_data.pop('account_type', None); phone_data.pop('account_origin', None)
        phone_data['client_available'] = True
        self.flow.submit(self.payload(phone_data));self.reach('payment_preparation')
        data=self.data('payment_preparation');data.pop('account_type');data.pop('account_origin');data['apple_account_ref']='early-a'
        self.flow.submit(self.payload(data))
        self.assertEqual(self.flow.next()['stage'],'app')
        self.assertEqual(self.flow.state['records']['payment_preparation']['data']['first_used_at'],(self.now-timedelta(hours=49)).isoformat())

    def test_existing_shadowrocket_requires_no_early_apple_purchase(self):
        self.reach('phone_proxy');self.advance()
        self.assertEqual(self.flow.next()['stage'],'timezone')
        self.assertEqual(self.flow.state['apple_accounts'],{})

    def test_restricted_purchase_preempts_new_account_wait(self):
        self.reach('payment_preparation')
        self.flow.submit(self.payload({'purchase_restricted':True,'account_type':'new','store_signed_in':True,'first_used_at':self.now.isoformat()}))
        view=self.flow.next()
        self.assertEqual(view['status'],'needs_support')
        self.assertEqual(view['reference'],'references/07-apple-purchase-support.md')
        self.assertNotIn('resume_at',view)
        self.flow.submit(self.payload({'support_case':'客服要求明天重试','support_retry_at':(self.now+timedelta(hours=24)).isoformat()}))
        self.assertEqual(self.flow.next()['resume_at'],(self.now+timedelta(hours=24)).isoformat())
        self.assertEqual(Workflow(self.root,lambda:self.now).next()['reference'],'references/07-apple-purchase-support.md')

    def test_restricted_shadowrocket_purchase_also_routes_to_support(self):
        self.reach('phone_proxy');self.flow.submit(self.payload({'client_available':False,'purchase_restricted':True}))
        self.assertEqual(self.flow.next()['status'],'needs_support')
        self.assertEqual(self.flow.next()['reference'],'references/07-apple-purchase-support.md')

    def test_windows_iphone_phone_network_displays_manual_checks_and_links(self):
        self.computer, self.phone = 'windows', 'iphone'
        self.reach('phone_network')
        view = self.flow.next(); message = view['customer_message']
        for text in ('Windows', '手机操作', 'https://ping0.cc/', 'https://ip.net.coffee/claude/',
                     'https://scamalytics.com/ip', '页面截图', 'Wi-Fi', '蜂窝', 'AdsPower',
                     'VPS', '电脑分数不代填', '检测时间'):
            self.assertIn(text, message)
        self.assertIn('source.reference', view['next_action'])
        self.assertIn('直接展示', view['display_instruction'])

    def test_phone_scores_must_be_complete_numeric_results(self):
        self.computer, self.phone = 'windows', 'iphone'
        self.reach('phone_network')
        original = self.data('phone_network')
        cases = [None, {}, {k:v for k,v in original['scores'].items() if k != 'scamalytics'}]
        for missing_site in ('netcoffee', 'ping0', 'scamalytics'):
            scores = deepcopy(original['scores']); scores[missing_site]['value'] = None
            cases.append(scores)
        scores = deepcopy(original['scores'])
        for observation in scores.values():
            observation.update(value=None, result='Phone page has no score')
        cases.append(scores)
        for scores in cases:
            with self.subTest(scores=scores):
                data = deepcopy(original); data['scores'] = scores
                self.flow.submit(self.payload(data))
                view = Workflow(self.root).next()
                self.assertEqual(view['stage'], 'phone_network')
                self.assertIn('scores', view['missing'])
        self.flow.submit(self.payload({'scores':original['scores']}))
        self.assertEqual(self.flow.next()['stage'], 'payment_preparation')

    def test_phone_exit_mismatch_blocks_even_with_three_real_scores(self):
        self.computer, self.phone = 'windows', 'iphone'
        self.reach('phone_network')
        data = self.data('phone_network'); data['exit_matches'] = False
        self.flow.submit(self.payload(data))
        self.assertEqual(self.flow.next()['stage'], 'phone_network')
        self.assertIn('exit_matches', self.flow.next()['missing'])
        self.flow.submit(self.payload({'exit_matches':True}))
        self.assertEqual(self.flow.next()['stage'], 'payment_preparation')

    def test_unverified_scores_cannot_be_overridden_by_score_review(self):
        for target in ('browser', 'phone_network'):
            self.reach(target)
            data = self.data(target)
            for observation in data['scores'].values(): observation['value'] = None
            data.update(score_review='continue', score_review_note='Customer wants to proceed')
            payload = self.payload(data); payload['source'] = {'kind':'user','reference':'customer reply'}
            self.flow.submit(payload)
            self.assertEqual(self.flow.next()['stage'], target)
            self.assertIn('scores', self.flow.next()['missing'])
            self.flow.submit(self.payload({'scores':self.data(target)['scores']}))
            self.assertNotEqual(self.flow.next()['stage'], target)

    def test_extreme_scores_cannot_silently_advance_and_new_scores_clear_review(self):
        self.reach('browser');d=self.data('browser')
        for name,obj in d['scores'].items():obj['value']=0 if name=='netcoffee' else 100
        self.flow.submit(self.payload(d));v=self.flow.next()
        self.assertEqual(v['stage'],'browser');self.assertIn('复查',v['customer_message'])
        self.assertIn('score_review',v['submission']['data'])
        p=self.payload({'score_review':'continue','score_review_note':'客户了解检测结果后决定继续'})
        p['source']['kind']='user';self.flow.submit(p)
        self.assertEqual(self.flow.next()['stage'],'phone_proxy')
        self.flow.invalidate('browser','changed browser connection')
        self.flow.submit(self.payload(d))
        self.assertIn('score_review',self.flow.next()['missing'])

    def test_small_score_deviation_does_not_add_gate(self):
        self.reach('browser');d=self.data('browser')
        for name,obj in d['scores'].items():obj['value']={'netcoffee':77,'ping0':32,'scamalytics':12}[name]
        self.flow.submit(self.payload(d));self.assertEqual(self.flow.next()['stage'],'phone_proxy')

    def test_both_browser_and_login_show_usage_reminder(self):
        for stage in ('browser','login'):
            self.reach(stage);self.assertIn('AdsPower',self.flow.next()['customer_message'])
            self.assertIn('授权链接',self.flow.next()['customer_message'])

    def test_subscription_requires_visible_closing_message_after_entitlement(self):
        self.reach('subscription');d=self.data('subscription');d.pop('handoff_explained')
        self.flow.submit(self.payload(d));v=self.flow.next()
        self.assertEqual(v['stage'],'subscription');self.assertIn('handoff_explained',v['missing'])
        for text in ('70%','精确定位','生物医药','网络安全','同一个 Google','PDF'):
            self.assertIn(text,v['customer_message'])
        self.flow.submit(self.payload({'handoff_explained':True}))
        self.assertEqual(self.flow.next()['status'],'complete')

    def test_generation_only_change_preserves_scripted_server_receipt(self):
        self.reach('server')
        good=lambda *a,**kw:SimpleNamespace(returncode=0,stdout=json.dumps({'status':'configured','node_file':'.local/network/node.txt'}))
        self.flow.run('server_deploy',runner=good)
        folder=self.root/'.local/network';folder.mkdir(exist_ok=True)
        (folder/'state.json').write_text('{"generation":2}')
        self.flow.sync()
        self.assertEqual(self.flow.next()['stage'],'computer_network')
        self.assertIn('server',self.flow.state['records'])
        self.assertEqual(self.flow.next()['progress'][4]['status'],'complete')

    def test_client_handoff_keeps_server_and_payment_history(self):
        self.reach(None);payment=deepcopy(self.flow.state['records']['subscription'])
        self.flow.invalidate('handoff','切换客户端')
        self.assertEqual(self.flow.next()['stage'],'computer_network')
        self.assertEqual(self.flow.state['records']['subscription'],payment)

    def test_vps_explanation_is_returned_before_purchase(self):
        self.reach('vps')
        message=self.flow.next()['customer_message']
        self.assertIn('远程服务器',message)
        self.assertIn('已买但没配置',message)
        self.assertNotIn('云端运行',message)
        self.assertIn('DMIT → 搬瓦工 → AKILE', message)
        self.assertIn('月付、季付、月付', message)
        self.assertIn('实际付款总额', message)
        action = self.flow.next()['next_action']
        self.assertIn('前一家缺货再看下一家', action)
        self.assertIn('不询问用户主要在哪个国家或地区使用', action)
        self.assertIn('node_timezone 从所选节点机房城市取得', action)
        self.assertIn('年付或多年预付只在用户明确要求时比较', action)
        self.assertIn('三家都缺货', action)
        self.assertNotIn('Hostinger', message + action)


    def test_purchase_restriction_during_actual_subscription_routes_support(self):
        self.reach('subscription')
        self.flow.submit(self.payload({'purchase_restricted':True}))
        view=self.flow.next()
        self.assertEqual(view['status'],'needs_support')
        self.assertEqual(view['reference'],'references/07-apple-purchase-support.md')
        self.assertNotIn('权益已确认',view['customer_message'])
        self.flow=Workflow(self.root,lambda:self.now)
        self.assertEqual(self.flow.next()['status'],'needs_support')
        d=self.data('subscription');d.update(purchase_restricted=False)
        self.flow.submit(self.payload(d))
        self.assertEqual(self.flow.next()['status'],'complete')

    def test_changing_new_apple_account_does_not_reuse_previous_age_or_consent(self):
        self.reach('payment_preparation')
        self.flow.submit(self.payload({'apple_account_ref':'first','account_type':'new','store_signed_in':True,
            'first_used_at':self.now.isoformat(),'apple_reminder_shown':True}))
        choice=self.payload({'wait_choice':'continue'});choice['source']['kind']='user'
        self.flow.submit(choice)
        self.flow.submit(self.payload({'apple_account_ref':'second','account_type':'new','store_signed_in':True,
            'first_used_at':self.now.isoformat()}))
        v=self.flow.next()
        self.assertEqual(v['status'],'waiting')
        self.assertNotIn('wait_choice',v['observed'])
        self.assertIn('apple_reminder_shown',v['missing'])
        self.assertIn('新买或新注册的 Apple ID',v['customer_message'])

    def test_wait_expiry_does_not_fill_missing_payment_details(self):
        self.reach('payment_preparation')
        self.flow.submit(self.payload({'apple_account_ref':'new','account_type':'new','store_signed_in':True,
            'first_used_at':self.now.isoformat(),'apple_reminder_shown':True}))
        self.now+=timedelta(hours=49)
        self.flow=Workflow(self.root,lambda:self.now)
        v=self.flow.next()
        self.assertEqual(v['stage'],'payment_preparation')
        self.assertEqual(v['status'],'active')
        self.assertIn('payment_ready',v['missing'])

    def test_partial_device_change_reexplains_android_without_old_ios_flags(self):
        self.reach('devices')
        self.flow.submit(self.payload({'computer':'mac','phone':'iphone','setup_explained':True}))
        self.flow.submit(self.payload({'computer':'windows','phone':'android'}))
        v=self.flow.next()
        self.assertIn('setup_explained',v['missing'])
        self.assertIn('Google Pay',v['customer_message'])
        self.flow.submit(self.payload({'phone':'iphone'}))
        v=self.flow.next()
        self.assertNotIn('android_route_explained',v['missing'])
        self.assertNotIn('Google Pay',v['customer_message'])

    def test_legacy_completed_state_only_requests_new_messages(self):
        self.reach(None)
        for key,field in [('devices','pdf_explained'),('browser','usage_explained'),
                          ('login','browser_notice_shown'),('subscription','handoff_explained')]:
            self.flow.state['records'][key]['data'].pop(field)
        self.flow.save();self.flow=Workflow(self.root,lambda:self.now)
        for key,field,phrase in [('devices','pdf_explained','PDF'),('browser','usage_explained','AdsPower'),
                                 ('login','browser_notice_shown','授权链接'),('subscription','handoff_explained','70%')]:
            v=self.flow.next();self.assertEqual(v['stage'],key)
            self.assertEqual(v['missing'],[field]);self.assertIn(phrase,v['customer_message'])
            self.flow.submit(self.payload({field:True}))
        self.assertEqual(self.flow.next()['status'],'complete')

    def test_probe_port_change_preserves_server_receipt(self):
        folder=self.root/'.local/network';folder.mkdir()
        c={'context':'same-server','server':{'address':'192.0.2.1'},'probe':{'proxy':'http://127.0.0.1:1'}}
        (folder/'input.json').write_text(json.dumps(c));self.flow.sync();self.reach('server')
        good=lambda *a,**kw:SimpleNamespace(returncode=0,stdout=json.dumps({'status':'configured','node_file':'.local/network/node.txt'}))
        self.flow.run('server_deploy',runner=good)
        c['probe']['proxy']='http://127.0.0.1:2'
        (folder/'input.json').write_text(json.dumps(c));self.flow.sync()
        self.assertEqual(self.flow.next()['stage'],'computer_network')
        self.assertIn('server',self.flow.state['records'])
        c['server']['address']='192.0.2.2'
        (folder/'input.json').write_text(json.dumps(c));self.flow.sync()
        self.assertEqual(self.flow.next()['stage'],'server')

    def test_legacy_signature_migration_preserves_progress(self):
        self.reach('login')
        self.flow.state['network_signature'].pop('server')
        self.flow.save();self.flow=Workflow(self.root,lambda:self.now);self.flow.sync()
        self.assertEqual(self.flow.next()['stage'],'login')
        self.assertIn('server',self.flow.state['network_signature'])

    def test_cleanup_opening_reminder_has_no_later_reinstall_gate(self):
        self.flow.submit(self.payload({'banned_login':'yes'}))
        self.assertIn('删除后重新下载',self.flow.next()['customer_message'])
        self.flow.submit(self.payload({'outcome':'deferred','handled_scope':'已展示开场建议'}))
        self.reach(None)
        self.assertEqual(self.flow.next()['status'],'complete')
        self.assertFalse(any('reinstall' in key for stage in catalog(self.flow.state) for key in stage['fields']))

    def test_all_device_routes_reach_closing_advice(self):
        for computer,phone in [('mac','ipad'),('windows','iphone'),('windows','android'),('mac','android')]:
            with self.subTest(computer=computer,phone=phone):
                with tempfile.TemporaryDirectory() as folder:
                    self.root=Path(folder);self.flow=Workflow(self.root,lambda:self.now);self.flow.init()
                    self.computer=computer;self.phone=phone;self.reach('subscription')
                    d=self.data('subscription');d.pop('handoff_explained')
                    self.flow.submit(self.payload(d))
                    self.assertIn('70%',self.flow.next()['customer_message'])
                    self.flow.submit(self.payload({'handoff_explained':True}))
                    self.assertEqual(self.flow.next()['status'],'complete')

    def test_early_purchase_restriction_survives_phone_recheck(self):
        self.reach('phone_proxy')
        self.flow.submit(self.payload({'client_available':False,'apple_account_ref':'restricted',
            'purchase_restricted':True,'support_retry_at':(self.now+timedelta(hours=72)).isoformat()}))
        self.flow.invalidate('phone','same account on replacement phone')
        self.flow.submit(self.payload({'apple_account_ref':'restricted'}))
        v=self.flow.next()
        self.assertEqual(v['status'],'waiting')
        self.assertEqual(v['reference'],'references/07-apple-purchase-support.md')
        self.assertEqual(v['resume_at'],(self.now+timedelta(hours=72)).isoformat())


# Keep inherited baseline tests in their original module; this file adds only new cases.
for name in list(fixtures.WorkflowTests.__dict__):
    if name.startswith('test_') and name not in CustomerFlowAudit.__dict__:
        setattr(CustomerFlowAudit,name,None)

if __name__=='__main__':unittest.main()
