"""Regression cases from the DMIT price-page / order-catalog discrepancy."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest
import test_workflow as fixtures
from vps_purchase import TARGETS, evaluate
from workflow import WorkflowError

NOW = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)


def observation(vendor='dmit', status='available'):
    t = TARGETS[vendor]
    return {**t, 'status': status, 'page': 'configuration', 'checked_at': NOW.isoformat(),
            'evidence': t['plan'] + (' Out of Stock' if status == 'sold_out' else ' configuration Monthly'),
            'amount': 10.90, 'currency': 'CNY' if vendor == 'akile' else 'USD', 'renewal_amount': 10.90}


def alternative():
    x = observation()
    x.update(plan='LAX.AN5.T1.V2C2G', network='Tier 1', amount=14.90, renewal_amount=14.90,
             url='https://www.dmit.io/cart.php?a=add&pid=example',
             evidence='LAX.AN5.T1.V2C2G configuration Monthly')
    return x


class PurchaseEvidenceTests(unittest.TestCase):
    def test_price_page_order_now_does_not_establish_stock(self):
        x = observation(); x['url'] = 'https://www.dmit.io/pages/pricing'
        self.assertEqual(evaluate({'dmit': x}, NOW)['reason'], 'official_order_url_required')

    def test_customer_t1_offer_rejected_even_if_available(self):
        for plan, network in [('LAX.AN5.T1.V2C2G', 'Tier 1'), ('LAX.AN5.Pro.TINY', 'Premium'), ('LAX.AN5.Pro.MINI', 'Premium')]:
            with self.subTest(plan=plan):
                x = observation(); x.update(plan=plan, network=network)
                self.assertEqual(evaluate({'dmit': x}, NOW)['reason'], 'target_mismatch')

    def test_t1_url_cannot_be_labeled_premium(self):
        x = observation(); x['url'] = 'https://www.dmit.io/cart.php?network=tier-1'
        self.assertEqual(evaluate({'dmit': x}, NOW)['reason'], 'target_mismatch')

    def test_catalog_order_button_not_configuration(self):
        x = observation(); x['page'] = 'catalog'
        self.assertFalse(evaluate({'dmit': x}, NOW)['can_purchase'])

    def test_sold_out_goes_to_bandwagon_and_then_akile(self):
        checks = {'dmit': observation(status='sold_out')}
        self.assertEqual(evaluate(checks, NOW)['vendor'], 'bandwagon')
        checks['bandwagon'] = observation('bandwagon', 'sold_out')
        self.assertEqual(evaluate(checks, NOW)['vendor'], 'akile')
        checks['akile'] = observation('akile', 'sold_out')
        self.assertEqual(evaluate(checks, NOW)['status'], 'no_verified_offer')

    def test_absent_target_requires_complete_catalog(self):
        x = observation(); x.update(status='not_listed', page='catalog', evidence='Full AN5 Premium list: MINI, MICRO, MEDIUM, LARGE, GIANT')
        self.assertFalse(evaluate({'dmit': x}, NOW)['can_purchase'])
        self.assertEqual(evaluate({'dmit': x}, NOW)['vendor'], 'dmit')
        x['catalog_complete'] = True
        self.assertEqual(evaluate({'dmit': x}, NOW)['vendor'], 'bandwagon')

    def test_challenge_is_unknown_and_can_check_next_vendor(self):
        x = observation(); x.update(status='unknown', page='challenge', evidence='Cloudflare security verification')
        r = evaluate({'dmit': x}, NOW)
        self.assertEqual(r['checked'], [{'vendor': 'dmit', 'status': 'unknown'}])
        self.assertEqual(r['vendor'], 'bandwagon')
        x['status'] = 'login_required'
        self.assertEqual(evaluate({'dmit': x}, NOW)['reason'], 'page_status_mismatch')
        x['page'] = 'login'
        self.assertEqual(evaluate({'dmit': x}, NOW)['vendor'], 'bandwagon')

    def test_observation_records_actual_time(self):
        for at in (NOW + timedelta(minutes=1), NOW.replace(tzinfo=None)):
            x = observation(); x['checked_at'] = at.isoformat()
            self.assertEqual(evaluate({'dmit': x}, NOW)['reason'], 'observation_time_required')

    def test_available_requires_price_cycle_and_matching_evidence(self):
        for changes in ({'amount': None}, {'renewal_amount': None}, {'cycle': 'annually'}, {'currency': 'JPY'},
                        {'evidence': 'Order Now'}, {'evidence': 'LAX.AS3.Pro.TINY Out of Stock'}, {'url': 'https://dmit.io.evil.test/cart.php'}):
            with self.subTest(changes=changes):
                x = observation(); x.update(changes)
                self.assertFalse(evaluate({'dmit': x}, NOW)['can_purchase'])
        self.assertTrue(evaluate({'dmit': observation()}, NOW)['can_purchase'])

    def test_skip_first_vendor_is_not_accepted(self):
        self.assertEqual(evaluate({'bandwagon': observation('bandwagon')}, NOW)['vendor'], 'dmit')

    def test_other_dmit_stock_keeps_bandwagon_recommendation_and_waits_for_choice(self):
        checks = {'dmit': observation(status='sold_out'), 'bandwagon': observation('bandwagon')}
        r = evaluate(checks, NOW, alternatives=[alternative()])
        self.assertEqual(r['status'], 'awaiting_choice')
        self.assertEqual(r['recommended_plan'], 'USCA_9-1GB')
        self.assertFalse(r['can_purchase'])
        for choice, vendor in [('USCA_9-1GB', 'bandwagon'), ('LAX.AN5.T1.V2C2G', 'dmit')]:
            r = evaluate(checks, NOW, alternatives=[alternative()], choice=choice)
            self.assertTrue(r['can_purchase'])
            self.assertEqual(r['vendor'], vendor)
            self.assertEqual(r['recommended_plan'], 'USCA_9-1GB')

    def test_unverified_other_dmit_is_not_an_option(self):
        checks = {'dmit': observation(status='sold_out'), 'bandwagon': observation('bandwagon')}
        for changes in ({'url': 'https://www.dmit.io/pages/pricing'}, {'status': 'sold_out'}, {'page': 'catalog'}, {'network': 'Premium'}):
            x = alternative(); x.update(changes)
            r = evaluate(checks, NOW, alternatives=[x])
            self.assertEqual(r['alternatives'], [])
            self.assertEqual(r['vendor'], 'bandwagon')

    def test_alternative_does_not_skip_bandwagon_check(self):
        r = evaluate({'dmit': observation(status='sold_out')}, NOW, alternatives=[alternative()], choice='LAX.AN5.T1.V2C2G')
        self.assertFalse(r['can_purchase'])

    def test_default_available_ignores_unrequested_alternatives(self):
        r = evaluate({'dmit': observation()}, NOW, alternatives=[alternative()])
        self.assertTrue(r['can_purchase'])
        self.assertEqual(r['plan'], 'LAX.AS3.Pro.TINY')
        self.assertEqual(r['alternatives'], [])


class PurchaseWorkflowTests(unittest.TestCase):
    setUp = fixtures.WorkflowTests.setUp
    data = fixtures.WorkflowTests.data
    def payload(self, data=None):
        # These tests isolate purchasing policy. Capture integration is exercised
        # with actual saved page files in test_capture_receipts.py.
        if data:
            items = list(data.get('purchase_checks', {}).items())
            items += [('dmit', x) for x in data.get('dmit_alternatives', [])]
            for vendor, item in items:
                key = 'fixture-' + vendor + '-' + item['plan']
                billing = ('Quarterly' if item.get('cycle') == 'quarterly' else 'Monthly') + ' ' + str(item.get('amount', 10.90)) + ' ' + item.get('currency', 'USD')
                item.update(receipt_id=key, billing_evidence=billing)
                self.flow.state['receipts'].append({'id': key, 'action': 'vps_capture', 'success': True,
                    'result': {'vendor': vendor, 'url': item['url'], 'checked_at': item['checked_at'],
                               'page': item['page'], 'text': item['evidence'] + '\n' + billing}})
        return fixtures.WorkflowTests.payload(self, data)
    advance = fixtures.WorkflowTests.advance
    reach = fixtures.WorkflowTests.reach

    def checks(self):
        x = observation(); x['checked_at'] = self.now.isoformat()
        return {'dmit': x}

    def test_new_purchase_requires_order_observations_before_completion(self):
        self.reach('vps')
        r = self.flow.submit(self.payload({'access_ready': False}))
        self.assertEqual(r['observed']['vps_origin'], 'purchase')
        d = self.data('vps'); d['vps_origin'] = 'purchase'
        with self.assertRaises(WorkflowError): self.flow.submit(self.payload(d))
        self.assertEqual(self.flow.next()['stage'], 'vps')
        r = self.flow.submit(self.payload({'purchase_checks': self.checks()}))
        self.assertTrue(r['purchase_decision']['can_purchase'])
        self.assertEqual(r['stage'], 'vps')
        self.assertEqual(self.flow.submit(self.payload(d))['stage'], 'server')
        self.now += timedelta(days=2)
        self.assertEqual(self.flow.next()['stage'], 'server')

    def test_order_page_sold_out_replaces_earlier_available_result(self):
        self.reach('vps')
        self.flow.submit(self.payload({'access_ready': False, 'purchase_checks': self.checks()}))
        checks = self.checks(); checks['dmit'].update(status='sold_out', evidence='LAX.AS3.Pro.TINY Out of Stock')
        self.flow.submit(self.payload({'purchase_checks': checks}))
        self.assertFalse(self.flow.next()['purchase_decision']['can_purchase'])
        d = self.data('vps'); d['vps_origin'] = 'purchase'
        with self.assertRaises(WorkflowError): self.flow.submit(self.payload(d))

    def test_unknown_stock_copy_does_not_claim_sold_out(self):
        self.reach('vps'); checks = self.checks()
        checks['dmit'].update(status='unknown', page='challenge', evidence='Cloudflare')
        r = self.flow.submit(self.payload({'access_ready': False, 'purchase_checks': checks}))
        self.assertIn('DMIT库存尚未核实', r['customer_message'])
        self.assertIn('USCA_9-1GB', r['customer_message'])
        self.assertNotIn('DMIT目标套餐显示缺货', r['customer_message'])

    def test_existing_and_legacy_completed_vps_are_reused(self):
        self.reach('vps'); self.advance()
        self.flow.state['records']['vps']['data'].pop('vps_origin')
        self.assertEqual(self.flow.next()['stage'], 'server')

    def test_missing_origin_cannot_bypass_by_submitting_access_ready(self):
        self.reach('vps'); d = self.data('vps'); d.pop('vps_origin')
        with self.assertRaises(WorkflowError): self.flow.submit(self.payload(d))
        self.assertEqual(self.flow.next()['stage'], 'vps')

    def test_alternative_comparison_and_customer_choice_end_to_end(self):
        self.reach('vps'); checks = self.checks()
        checks['dmit'].update(status='sold_out', evidence='LAX.AS3.Pro.TINY Out of Stock')
        checks['bandwagon'] = observation('bandwagon'); checks['bandwagon']['checked_at'] = self.now.isoformat()
        checks['bandwagon'].update(amount=49.99, renewal_amount=49.99)
        alt = alternative(); alt['checked_at'] = self.now.isoformat()
        r = self.flow.submit(self.payload({'access_ready': False, 'purchase_checks': checks, 'dmit_alternatives': [alt]}))
        self.assertEqual(r['purchase_decision']['recommended_plan'], 'USCA_9-1GB')
        self.assertIn('没有交付实践', r['customer_message'])
        self.assertIn('成熟适配经验', r['customer_message'])
        self.assertIn('Tier 1', r['customer_message'])
        self.assertIn('49.99 USD／三个月', r['customer_message'])
        self.assertFalse(r['purchase_decision']['can_purchase'])
        with self.assertRaises(WorkflowError):
            self.flow.submit(self.payload({'purchase_choice': alt['plan']}))
        p = self.payload({'purchase_choice': alt['plan']})
        p['source'] = {'kind': 'user', 'reference': '客户明确选择已说明差异的其他 DMIT 套餐'}
        self.assertTrue(self.flow.submit(p)['purchase_decision']['can_purchase'])
        d = self.data('vps'); d['vps_origin'] = 'purchase'
        self.assertEqual(self.flow.submit(self.payload(d))['stage'], 'server')

    def test_refresh_keeps_customer_selected_plan(self):
        self.reach('vps'); checks = self.checks()
        self.flow.submit(self.payload({'access_ready': False, 'purchase_checks': checks}))
        p = self.payload({'purchase_choice': TARGETS['dmit']['plan']}); p['source']['kind'] = 'user'
        self.flow.submit(p)
        checks = deepcopy(checks)
        checks['dmit']['evidence'] += ' refreshed configuration page'
        self.assertEqual(self.flow.submit(self.payload({'purchase_checks': checks}))['observed']['purchase_choice'], TARGETS['dmit']['plan'])

    def test_default_missing_and_bandwagon_available_is_explained(self):
        self.reach('vps'); checks = self.checks()
        checks['dmit'].update(status='sold_out', evidence='LAX.AS3.Pro.TINY Out of Stock')
        checks['bandwagon'] = observation('bandwagon'); checks['bandwagon']['checked_at'] = self.now.isoformat()
        checks['bandwagon']['evidence'] = 'USCA_9 Memory 1 GB configuration 3 Months'
        r = self.flow.submit(self.payload({'access_ready': False, 'purchase_checks': checks}))
        self.assertTrue(r['purchase_decision']['can_purchase'])
        self.assertEqual(r['purchase_decision']['vendor'], 'bandwagon')
        self.assertIn('DMIT目标套餐显示缺货', r['customer_message'])
        self.assertNotIn('您目前是还没买', r['customer_message'])
