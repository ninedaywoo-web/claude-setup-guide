"""Real file/CLI capture boundaries and forged observation regressions."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import test_workflow as fixtures
from vps_capture import capture
from vps_purchase import evaluate, TARGETS
from workflow_view import compact

URL = 'https://www.dmit.io/cart.php?a=confproduct&i=0'
PAGE = '''Configure Product
LAX.AS3.Pro.TINY
Billing Cycle
Monthly $10.90 USD
Renewal $10.90 USD
Continue'''


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / '.local').mkdir()
        self.path = self.root / '.local/browser.json'

    def snapshot(self, text=PAGE):
        self.path.write_text(json.dumps({'url': URL, 'text': text}))
        return capture({'vendor': 'dmit', 'url': URL, 'browser_file': str(self.path)}, self.root)

    def item(self, page):
        return {**TARGETS['dmit'], 'url': URL, 'page': 'configuration', 'status': 'available',
                'amount': 10.90, 'renewal_amount': 10.90, 'currency': 'USD',
                'checked_at': page['checked_at'], 'receipt_id': 'capture-1',
                'evidence': 'LAX.AS3.Pro.TINY', 'billing_evidence': 'Monthly $10.90 USD\nRenewal $10.90 USD'}

    def decision(self, item, page):
        return evaluate({'dmit': item}, datetime.now(timezone.utc), captures={'capture-1': page})

    def test_saved_page_and_actual_quote_allow_purchase(self):
        page = self.snapshot()
        self.assertEqual(json.loads(Path(page['capture_file']).read_text())['text'], PAGE)
        self.assertTrue(self.decision(self.item(page), page)['can_purchase'])

    def test_unfetched_quote_or_changed_price_has_no_purchase_result(self):
        page = self.snapshot(); item = self.item(page)
        for change in ({'evidence': 'LAX.AS3.Pro.TINY available now'}, {'amount': 14.90},
                       {'cycle': 'quarterly'}, {'receipt_id': 'invented'},
                       {'url': 'https://www.dmit.io/cart.php?a=add&pid=other'}):
            with self.subTest(change=change):
                self.assertFalse(self.decision(dict(item, **change), page)['can_purchase'])

    def test_catalog_cannot_be_relabelled_configuration(self):
        page = self.snapshot('LAX.AS3.Pro.TINY\nOrder Now\nMonthly $10.90 USD\nRenewal $10.90 USD')
        self.assertEqual(page['page'], 'catalog')
        self.assertEqual(self.decision(self.item(page), page)['reason'], 'captured_page_type_mismatch')

    def test_catalog_billing_filter_does_not_become_a_product_form(self):
        from vps_capture import PageText
        parser = PageText()
        parser.feed('<h1>Products</h1><select name="billingcycle"><option>Monthly</option></select><button>Order Now</button>')
        self.assertFalse(parser.configuration)

    def test_sold_out_capture_cannot_supply_available_evidence(self):
        page = self.snapshot('LAX.AS3.Pro.TINY\nOut of Stock')
        self.assertFalse(self.decision(self.item(page), page)['can_purchase'])
        item = dict(self.item(page), page='catalog', status='sold_out', evidence='LAX.AS3.Pro.TINY\nOut of Stock')
        self.assertEqual(self.decision(item, page)['vendor'], 'bandwagon')

    def test_challenge_stays_unknown_and_next_vendor_is_checked(self):
        page = self.snapshot('Just a moment... Verify you are human')
        item = dict(self.item(page), page='challenge', status='unknown', evidence=page['text'])
        self.assertEqual(self.decision(item, page)['vendor'], 'bandwagon')

    def test_http_capture_reads_page_without_browser_file(self):
        # Exercise native HTML extraction using a real HTTP response on loopback.
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from threading import Thread
        from unittest.mock import patch
        from urllib.request import urlopen
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200); self.end_headers()
                self.wfile.write(b'<h1>LAX.AS3.Pro.TINY</h1><form id="frmConfigureProduct"><select name="billingcycle"><option>Monthly $10.90 USD</option></select></form><script>invented stock</script>')
            def log_message(self, *args): pass
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True); thread.start()
        def local_transport(request, **kwargs):
            response = urlopen('http://127.0.0.1:' + str(server.server_port), **kwargs)
            response.geturl = lambda: request.full_url
            return response
        try:
            with patch('vps_capture.urllib.request.urlopen', side_effect=local_transport):
                page = capture({'vendor': 'dmit', 'url': URL}, self.root)
            self.assertEqual(page['capture_method'], 'http')
            self.assertEqual(page['page'], 'configuration')
            self.assertNotIn('invented stock', page['text'])
        finally:
            server.shutdown(); server.server_close(); thread.join()


class ReceiptGateTests(unittest.TestCase):
    setUp = fixtures.WorkflowTests.setUp
    data = fixtures.WorkflowTests.data
    payload = fixtures.WorkflowTests.payload
    reach = fixtures.WorkflowTests.reach
    advance = fixtures.WorkflowTests.advance

    def test_no_probe_config_still_requires_actual_probes(self):
        self.reach('computer_network')
        self.flow.submit(self.payload())
        self.assertEqual(self.flow.next()['missing'], ['probe_proxy', 'probe_system'])
        self.assertFalse((self.root / '.local/network/input.json').exists())

    def test_new_purchase_cannot_use_existing_flag_to_skip_readback(self):
        self.reach('server')
        from test_vps_purchase import observation
        offer = observation(); offer['checked_at'] = self.now.isoformat()
        self.flow.state['records']['vps']['data'].update(vps_origin='purchase', purchase_checks={'dmit': offer})
        self.flow.submit(self.payload())
        self.assertEqual(self.flow.next()['missing'], ['server_readback'])

    def test_inventory_without_capture_never_returns_available(self):
        from test_vps_purchase import observation
        self.reach('vps'); item = observation(); item['checked_at'] = self.now.isoformat()
        result = self.flow.submit(self.payload({'access_ready': False, 'purchase_checks': {'dmit': item}}))
        self.assertFalse(result['purchase_decision']['can_purchase'])
        self.assertEqual(result['purchase_decision']['reason'], 'page_capture_required')

    def test_compact_keeps_customer_images_and_all_waiting_rules(self):
        for stage in ('vps', 'browser', 'phone_proxy', 'payment_preparation'):
            self.reach(stage); full = self.flow.next(); short = compact(full)
            self.assertEqual(short['customer_message'], full['customer_message'])
            self.assertEqual(short.get('customer_images'), full.get('customer_images'))
            self.assertEqual(short['missing'], full['missing'])
            self.assertEqual(short['allowed_actions'], full['allowed_actions'])
            self.assertLess(len(json.dumps(short)), len(json.dumps(full)))


class AlipayGuideTests(unittest.TestCase):
    def test_existing_jump_url_and_original_picture_are_in_runtime_guide(self):
        from workflow_teaching import guide, ROOT
        state = {'records': {'devices': {'data': {'computer':'windows','phone':'iphone'}}}}
        result = guide('gift_alipay',state,'payment_preparation')
        chapter = (ROOT/'references/03-apple.md').read_text()
        import re
        url = re.search(r'\[(https://render\.alipay\.com/[^\]]+)\]',chapter)[1]
        self.assertIn(url,result['customer_message'])
        self.assertIn('备忘录',result['customer_message'])
        self.assertIn('打开支付宝',result['customer_message'])
        self.assertEqual(result['customer_images'],['assets/images/apple/14.jpg'])


class GiftRouteTests(unittest.TestCase):
    setUp = fixtures.WorkflowTests.setUp
    data = fixtures.WorkflowTests.data
    payload = fixtures.WorkflowTests.payload
    reach = fixtures.WorkflowTests.reach
    advance = fixtures.WorkflowTests.advance

    def test_default_buy_route_and_missing_entry_keep_alipay(self):
        self.reach('payment_preparation')
        data = self.data('payment_preparation'); data['payment_ready'] = False
        result = self.flow.submit(self.payload(data))
        self.assertEqual(result['default_teaching']['topic'], 'gift_alipay')
        self.assertIn('首推支付宝', result['customer_message'])
        self.assertIn('render.alipay.com', result['customer_message'])
        self.assertEqual(result['customer_message'].count('![支付宝渠道购买礼品卡]'), 1)
        result = self.flow.submit(self.payload({'gift_channel':'alipay','gift_entry':'missing','teaching_topic':'gift_official'}))
        self.assertEqual(result['default_teaching']['topic'], 'gift_alipay')
        self.assertIn('备忘录', result['next_action'])
        result = self.flow.submit(self.payload({'gift_entry':'opened'}))
        self.assertEqual(result['stage'], 'payment_preparation')
        self.assertEqual(result['observed']['gift_channel'], 'alipay')
        result = self.flow.submit(self.payload({'teaching_topic':'gift_redeem'}))
        self.assertEqual(result['default_teaching']['topic'], 'gift_redeem')
        self.assertNotIn('render.alipay.com', result['customer_message'])
        result = self.flow.submit(self.payload({'payment_ready':True}))
        self.assertEqual(result['stage'], 'app')

    def test_waiting_and_explicit_other_channel_keep_their_path(self):
        self.account_type = 'new'; self.first_used_at = self.now
        self.reach('payment_preparation')
        data = self.data('payment_preparation'); data.update(payment_ready=False, account_origin='purchased')
        result = self.flow.submit(self.payload(data))
        self.assertEqual(result['status'], 'waiting')
        self.assertNotIn('render.alipay.com', result.get('customer_message',''))
        payload = self.payload({'account_origin':'self_used','account_type':'longstanding','gift_channel':'apple_official','teaching_topic':'gift_official'})
        payload['source'] = {'kind':'user','reference':'客户明确选择苹果官网购买'}
        result = self.flow.submit(payload)
        self.assertEqual(result['default_teaching']['topic'], 'gift_official')
        self.assertNotIn('render.alipay.com', result.get('customer_message',''))


class CaptureWorkflowIntegrationTests(unittest.TestCase):
    setUp = fixtures.WorkflowTests.setUp
    data = fixtures.WorkflowTests.data
    payload = fixtures.WorkflowTests.payload
    reach = fixtures.WorkflowTests.reach
    advance = fixtures.WorkflowTests.advance

    def test_cli_capture_to_purchase_to_server_gate(self):
        source = Path(__file__).resolve().parents[1] / 'scripts'
        shutil.copytree(source, self.root/'scripts', ignore=shutil.ignore_patterns('__pycache__'))
        self.reach('vps')
        snapshot = self.root/'.local/browser.json'
        snapshot.write_text(json.dumps({'url':URL,'text':PAGE}))
        inputs = self.root/'.local/page-input.json'
        inputs.write_text(json.dumps({'vendor':'dmit','url':URL,'browser_file':str(snapshot)}))
        execution = self.flow.run('vps_capture', inputs)['execution']
        self.assertTrue(execution['success'])
        page = execution['result']; self.now = datetime.now(timezone.utc)
        item = {**TARGETS['dmit'], 'url':URL, 'page':'configuration','status':'available',
                'checked_at':page['checked_at'],'receipt_id':execution['id'],
                'amount':10.90,'renewal_amount':10.90,'currency':'USD',
                'evidence':'LAX.AS3.Pro.TINY','billing_evidence':'Monthly $10.90 USD\nRenewal $10.90 USD'}
        result = self.flow.submit(self.payload({'access_ready':False,'purchase_checks':{'dmit':item}}))
        self.assertTrue(result['purchase_decision']['can_purchase'])
        data = self.data('vps'); data['vps_origin']='purchase'
        self.assertEqual(self.flow.submit(self.payload(data))['stage'],'server')
        result = self.flow.submit(self.payload({'mode':'existing','service_running':True,'node_exported':True,'parameters_checked':True}))
        self.assertEqual(result['stage'],'server')
        self.assertIn('server_readback',result['missing'])


class StdinSubmissionTests(unittest.TestCase):
    setUp = fixtures.WorkflowCLITests.setUp
    cli = fixtures.WorkflowCLITests.cli
    def test_submit_json_stdin_preserves_actual_fields(self):
        import subprocess, sys
        first = self.cli('workflow.py','init')
        payload = first['submission']; payload.update(source={'kind':'user','reference':'客户反馈未登录过封禁账号'},data={'banned_login':'no'})
        result = subprocess.run([sys.executable,str(self.root/'scripts/workflow.py'),'submit','--input','-'],
                                input=json.dumps(payload),text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout)
        self.assertEqual(json.loads(result.stdout)['stage'],'devices')
