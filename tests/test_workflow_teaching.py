"""Adversarial teaching delivery and re-explanation, using isolated progress."""
import io
import json
from copy import deepcopy
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

import test_workflow as fixtures
from workflow import Workflow
import workflow
import update
from workflow_teaching import CARDS, GOOGLE_IMAGES, ROOT, guide


class TeachingTests(unittest.TestCase):
    def setUp(self):
        self.case = fixtures.WorkflowTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.case.computer = 'windows'

    def buy(self):
        c = self.case
        c.reach('google')
        return c.flow.submit(c.payload({'account_available': True, 'account_origin': 'purchased'}))

    def test_purchase_renders_all_three_original_pages_in_message(self):
        view = self.buy()
        self.assertEqual(view['customer_images'], GOOGLE_IMAGES)
        for path in GOOGLE_IMAGES:
            self.assertIn(str(ROOT / path), view['customer_message'])
        self.assertIn('https://2fa.run/', view['customer_message'])
        self.assertEqual(view['stage'], 'google')

    def test_boolean_alone_does_not_replace_three_image_receipt(self):
        c = self.case
        self.buy()
        view = c.flow.submit(c.payload({'materials_explained': True}))
        self.assertEqual(view['stage'], 'google')
        self.assertIn('materials_images_shown', view['missing'])
        view = c.flow.submit(c.payload({'materials_images_shown': GOOGLE_IMAGES[:1]}))
        self.assertEqual(view['stage'], 'google')
        view = c.flow.submit(c.payload({'materials_images_shown': GOOGLE_IMAGES.copy()}))
        self.assertEqual(view['stage'], 'vps')

    def test_buy_and_explained_in_same_submission_still_needs_image_receipt(self):
        c=self.case;c.reach('google')
        view=c.flow.submit(c.payload({'account_available':True,'account_origin':'purchased','materials_explained':True}))
        self.assertEqual(view['stage'],'google')
        self.assertIn('materials_images_shown',view['missing'])

    def test_unknown_origin_is_clarified_and_known_personal_account_reused(self):
        c=self.case;c.reach('google')
        view=c.flow.submit(c.payload({'account_available':True}))
        self.assertEqual(view['stage'],'google')
        self.assertIn('account_origin',view['missing'])
        self.assertIn('还是刚购买',view['customer_message'])
        self.assertNotIn('customer_images',view)
        view=c.flow.submit(c.payload({'account_origin':'self_used'}))
        self.assertEqual(view['stage'],'vps')

    def test_repeat_and_cross_stage_help_preserve_state_and_ticket(self):
        c=self.case;self.buy()
        c.flow.submit(c.payload({'materials_explained':True,'materials_images_shown':GOOGLE_IMAGES.copy()}))
        c.reach('phone_network')
        before=deepcopy(c.flow.state);ticket=c.flow.next()['ticket']
        saved=c.flow.path.read_bytes()
        for _ in range(2):
            view=c.flow.guide('google_2fa')
            self.assertEqual(view['customer_images'],GOOGLE_IMAGES[1:])
            self.assertIn('https://2fa.run/',view['customer_message'])
            self.assertIn('身份验证器',view['customer_message'])
            self.assertTrue(view['progress_unchanged'])
        self.assertEqual(c.flow.state,before)
        self.assertEqual(c.flow.path.read_bytes(),saved)
        self.assertEqual(c.flow.next()['ticket'],ticket)
        self.assertEqual(c.flow.next()['stage'],'phone_network')

    def test_completed_delivery_can_reopen_teaching_without_reopening_setup(self):
        c=self.case
        while c.flow.next()['stage'] is not None:c.advance()
        before=deepcopy(c.flow.state)
        self.assertEqual(c.flow.guide('google_materials')['customer_images'],GOOGLE_IMAGES)
        self.assertEqual(c.flow.state,before)
        self.assertEqual(c.flow.next()['status'],'complete')

    def test_current_browser_step_has_matching_default_picture(self):
        c=self.case;c.reach('browser')
        self.assertEqual(c.flow.next()['default_teaching']['topic'],'browser_profile')
        view=c.flow.submit(c.payload({'profile_ref':'profile-a'}))
        self.assertEqual(view['default_teaching']['topic'],'browser_proxy')
        view=c.flow.submit(c.payload({'proxy_configured':True}))
        self.assertEqual(view['default_teaching']['topic'],'browser_fingerprint')
        self.assertIn('03.png',view['customer_message'])

    def test_seller_and_platform_images_do_not_cross_routes(self):
        c=self.case;c.reach('google')
        c.flow.submit(c.payload({'account_available':False,'purchase_channel':'gmailbuy'}))
        self.assertNotIn('chuhai_register',[t['id'] for t in c.flow.next()['teaching_topics']])
        with self.assertRaisesRegex(ValueError,'not_for_current'):c.flow.guide('chuhai_register')
        with self.assertRaisesRegex(ValueError,'not_for_current'):c.flow.guide('mac_client')
        self.assertEqual(c.flow.guide('gmailbuy')['customer_images'],[])

    def test_android_has_no_apple_defaults_or_gift_topics(self):
        c=self.case;c.phone='android'
        c.reach('payment_preparation')
        topics=c.flow.next()['teaching_topics']
        self.assertFalse(any(t['id'].startswith(('apple','gift')) for t in topics))
        with self.assertRaisesRegex(ValueError,'not_for_current'):c.flow.guide('gift_redeem')
        c.reach('app')
        self.assertNotIn('images/apple',c.flow.next()['customer_message'])

    def test_waiting_and_purchase_failure_keep_their_route(self):
        c=self.case;c.reach('payment_preparation')
        view=c.flow.submit(c.payload({'account_origin':'purchased','account_type':'new',
                    'apple_account_ref':'apple-test','store_signed_in':True,
                    'first_used_at':c.now.isoformat(),'wait_choice':'wait','apple_reminder_shown':True}))
        self.assertEqual(view['status'],'waiting')
        self.assertNotIn('default_teaching',view)
        before=deepcopy(c.flow.state)
        self.assertIn('15.jpg',c.flow.guide('gift_redeem')['customer_message'])
        self.assertEqual(c.flow.state,before)
        self.assertEqual(c.flow.next()['status'],'waiting')
        view=c.flow.submit(c.payload({'purchase_restricted':True}))
        self.assertEqual(view['default_teaching']['topic'],'apple_support')
        self.assertNotIn('17.jpg',view['customer_message'])

    def test_teaching_position_survives_resume_without_completing_operation(self):
        c=self.case;c.reach('vps')
        view=c.flow.submit(c.payload({'teaching_topic':'vps_bandwagon','teaching_step':3}))
        self.assertEqual(view['stage'],'vps')
        self.assertIn('access_ready',view['missing'])
        self.assertIn('bandwagon-register-3.png',view['customer_message'])
        c.flow=Workflow(c.root,lambda:c.now)
        self.assertEqual(c.flow.next()['default_teaching']['step'],3)
        view=c.flow.submit(c.payload({'teaching_topic':'vps_akile'}))
        self.assertNotIn('teaching_step',view['observed'])
        self.assertEqual(view['default_teaching']['step'],1)

    def test_invalid_teaching_metadata_does_not_crash_or_complete_stage(self):
        c=self.case;c.reach('vps')
        view=c.flow.submit(c.payload({'teaching_topic':[], 'teaching_step':1}))
        self.assertEqual(view['stage'],'vps')
        self.assertIn('teaching_topic',view['missing'])
        self.assertIn('teaching_step',view['missing'])

    def test_multi_page_process_defaults_to_one_picture(self):
        c=self.case;c.reach('payment_preparation')
        view=c.flow.guide('gift_official')
        self.assertEqual(len(view['customer_images']),1)
        self.assertEqual(view['total_steps'],4)
        self.assertEqual(view['step'],1)

    def test_gallery_step_selects_one_original_page_and_rejects_invalid_index(self):
        c=self.case;c.reach('vps')
        view=c.flow.guide('vps_bandwagon',3)
        self.assertEqual(len(view['customer_images']),1)
        self.assertTrue(view['customer_images'][0].endswith('bandwagon-register-3.png'))
        for index in (0,-1,6):
            with self.assertRaisesRegex(ValueError,'out_of_range'):c.flow.guide('vps_bandwagon',index)

    def test_guides_cover_all_existing_markdown_figures_and_use_existing_sources(self):
        mapped={p for item in CARDS.values() for p in item['images']}
        referenced=set()
        for path in (ROOT/'references').glob('*.md'):
            for img in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',path.read_text()):
                referenced.add((path.parent/img).resolve().relative_to(ROOT).as_posix())
        self.assertLessEqual(referenced,mapped)
        for item in CARDS.values():
            self.assertTrue((ROOT/item['reference']).is_file())
            for img in item['images']:self.assertTrue((ROOT/img).is_file())

    def test_missing_image_is_reported_without_false_embedded_image(self):
        c=self.case;c.reach('google')
        with patch('workflow_teaching.ROOT',c.root):
            result=c.flow.guide('google_2fa')
        self.assertEqual(result['customer_images'],[])
        self.assertEqual(result['missing_images'],GOOGLE_IMAGES[1:])
        self.assertNotIn('![',result['customer_message'])
        self.assertIn('缺图或显示失败',result['display_instruction'])

    def test_sms_help_does_not_supply_authenticator_diagrams(self):
        c=self.case;c.reach('login')
        result=c.flow.guide('google_other_verification')
        self.assertEqual(result['customer_images'],[])
        self.assertNotIn('2fa.run',result['customer_message'])
        self.assertIn('短信',result['title'])

    def test_legacy_completed_materials_are_not_reopened_for_new_receipt(self):
        c=self.case;c.reach('google')
        c.flow.state['records']['google']={'data':{'account_origin':'purchased',
                'account_available':True,'materials_explained':True},'observations':[]}
        c.flow.save()
        self.assertEqual(c.flow.next()['stage'],'vps')
        self.assertEqual(c.flow.guide('google_materials')['customer_images'],GOOGLE_IMAGES)

    def test_cli_guide_neither_syncs_nor_saves_or_checks_update(self):
        c=self.case;c.reach('google');before=c.flow.path.read_bytes()
        out=io.StringIO()
        with patch.object(workflow,'ROOT',c.root),patch.object(sys,'argv',[
                'workflow.py','guide','--topic','google_2fa','--step','1']),\
                patch.object(workflow.Workflow,'sync',side_effect=AssertionError('sync called')),\
                patch.object(workflow.Workflow,'save',side_effect=AssertionError('save called')),\
                patch.object(workflow,'workflow_output',side_effect=AssertionError('update called')),\
                patch('sys.stdout',out):
            self.assertEqual(workflow.main(),0)
        result=json.loads(out.getvalue())
        self.assertEqual(len(result['customer_images']),1)
        self.assertTrue(result['progress_unchanged'])
        self.assertEqual(c.flow.path.read_bytes(),before)

    def test_update_notice_preserves_teaching_and_image_display_instructions(self):
        view=self.buy()
        with patch.object(update,'check',return_value={'status':'update_available',
                          'update_notice':'新版提示','apply_command':'test'}):
            result=update.workflow_output(self.case.root,view)
        self.assertIn('默认在聊天直接展示',result['display_instruction'])
        self.assertIn('materials_images_shown',result['display_instruction'])
        self.assertIn('新版提示',result['customer_message'])
        for img in GOOGLE_IMAGES:self.assertIn(str(ROOT/img),result['customer_message'])

    def test_known_topics_can_be_selected_after_explanation_flag(self):
        c=self.case;c.reach('browser')
        c.flow.submit(c.payload({'usage_explained':True}))
        view=c.flow.guide('browser_proxy')
        self.assertIn('02.png',view['customer_message'])
        self.assertIn('已讲过的标记不抑制',view['display_instruction'])


if __name__=='__main__':unittest.main()
