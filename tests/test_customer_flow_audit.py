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
from workflow_definition import catalog


class CustomerFlowAudit(fixtures.WorkflowTests):
    # Reuse the isolated state machine fixture, not live devices/accounts.
    def test_google_preparation_shows_reuse_purchase_and_login_timing(self):
        self.reach('google')
        view = self.flow.next()
        self.assertIn('直接沿用', view['customer_message'])
        for url in ('https://chuhai91.cc', 'https://gmailbuy.com/'):
            self.assertIn(url, view['customer_message'])
        self.assertIn('手机网络配置完成后', view['customer_message'])
        self.assertIn('直接展示', view['display_instruction'])
        self.assertIn('不引导注册 Google 账号', view['next_action'])

    def test_google_missing_account_keeps_purchase_route_on_resume(self):
        self.reach('google')
        self.flow.submit(self.payload({'account_available': False}))
        view = Workflow(self.root).next()
        self.assertEqual(view['stage'], 'google')
        self.assertIn('购买', view['customer_message'])
        self.assertNotIn('您有没有', view['customer_message'])
        self.flow.submit(self.payload({'account_available': True}))
        self.assertEqual(self.flow.next()['stage'], 'vps')

    def test_existing_google_account_advances_without_purchase_requirement(self):
        self.reach('google')
        self.flow.submit(self.payload({'account_available': True}))
        self.assertEqual(self.flow.next()['stage'], 'vps')
        self.reach('login')
        self.assertEqual(self.flow.next()['next_action'], '使用 Google 账号登录 Claude')

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
        self.flow.submit(self.payload({'client_available':False,'apple_account_ref':'early-a','account_type':'new',
            'store_signed_in':True,'first_used_at':self.now.isoformat(),'apple_reminder_shown':True}))
        self.assertEqual(self.flow.next()['status'],'waiting')
        self.now+=timedelta(hours=49)
        self.advance();self.reach('payment_preparation')
        data=self.data('payment_preparation');data.pop('account_type');data['apple_account_ref']='early-a'
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
        self.assertIn('新 Apple ID',v['customer_message'])

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
