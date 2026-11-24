#!/usr/bin/env python3
"""Opt-in real-model customer journeys in disposable project copies.

python3 tests/model_replay.py --journey gift --model <available-model>
Offline unittest checks never invoke Codex. Model runs use the installed CLI.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_workflow as fixtures
from workflow import Workflow
from update import cache_check, failed_check

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    'bought': ('google', '买好了，账号资料也收到了，但我不知道怎么登录啊。'),
    'repeat_code': ('vps', '刚才那个验证码还是不会弄，图没显示，你再教我一下。'),
    'computer_first': ('devices', 'Windows，先配置电脑吧。'),
    'system': ('vps', '商家系统默认选的是 Ubuntu 22.04，我直接用这个吗？'),
    'stock': ('vps', 'DMIT 的价格页有 Order Now，14.9 美元的那个是不是就有货？我直接买了？'),
    'gift_buy': ('payment_preparation', '我要买礼品卡，怎么购买？'),
    'alipay': ('payment_preparation', '支付宝里面根本找不到你说的礼品卡小程序，搜了几次都没有，怎么办？'),
}
JOURNEYS = {
    'support_recovery': ('payment_preparation', [
        '购买时 Apple 提示购买受限，需要联系客服，先带我处理这个问题。',
        '客服已经处理，购买限制已解除，没有新的重试等待。继续购买礼品卡。']),
    'phone_account_swap': ('phone_proxy', [
        'App Store 已换成我自己一直正常使用的老美区账号，代号 apple-new，已登录成功。小火箭节点、路由都没有改，VPN 还没打开。',
        '现在已打开 VPN，仍选中同一台 VPS 的 node-a，全局路由为代理，手机节点连接成功。继续。']),
    'vps_recheck': ('vps', [
        '推荐的搬瓦工 2 GB、89.99 美元季付页面显示缺货，请核对这次页面快照。我还没购买。',
        '卖家通知恢复了，请重新核对当前页面快照里的 2 GB 套餐和费用。',
        '已经买好这个 2 GB 季付套餐，系统 Debian 12，洛杉矶，节点代号 node-a，时区 America/Los_Angeles，SSH 访问也准备好了。请接下一步，暂不实际连接。']),
    'first_ssh': ('server', [
        '新 VPS 的访问资料已经放好，请按程序做部署前检查。',
        '已在真实终端与控制台核对指纹，输入 yes 保存，SSH 登录成功，系统是 Debian 12。请重试检查并继续部署。']),
    'cleanup_scope': ('cleanup', [
        '这台 Mac 用过被封的 Claude 账号，请先说明清理操作，本轮先不要执行清理；我现在的系统时区是洛杉矶。',
        '我已按清理步骤完成备份和清理，Claude 桌面端和 CLI 残留已处理，系统时区保持原值。请补跑只读审计并继续后续流程。']),
    'cleanup_logout_guard': ('cleanup', [
        'Mac 上用 Claude 桌面版、Chrome 和 iPhone App 都登录过被封禁账号，我已经把三个地方都退出登录了，直接下一步吧。',
        '好，先运行只读审计，然后我按清理步骤完成了备份和清理，桌面端、Chrome 站点数据和 CLI 残留都已处理，iPhone 也删除并重装了官方 App。继续。']),
    'missing_score': ('browser', [
        '两个检测站的数值已提供，NetCoffee 一直超时，缺的这一个先算了吧，我同意继续。',
        'NetCoffee 恢复了，同一个 AdsPower 环境实际测到 85；Ping0 风险 20，Scamalytics 风险 5。其他刚才已经验收的配置和环境都没变，请记录并继续。']),
    'browser_swap': ('browser', [
        '我把原来的 AdsPower 环境换成新建的 browser-b，刚创建，设置还没做。前面桌面端和浏览器的使用说明我已看明白，不用再重复。',
        'browser-b 已保存并打开，HTTP 代理和指纹设置完成，禁止网页定位，已在这个环境检查出口一致、HTTPS、DNS、IPv6、WebRTC 和断线恢复。NetCoffee 85、Ping0 20、Scamalytics 5，均为刚才实际检测，请继续。']),
    'cross_stage_google': ('google', [
        '我有好几个以前的 Gmail，都没有注册过 Claude。不记得密码和手机号是否使用了，注册 Claude 需要这些吗？我的 Mac 默认是已经登录上的。',
        'Mac 登录的是 Gmail，不是 Claude。手机号是 +86，密码还没找到。那注册 Claude 要不要外国手机号？',
        'Google 密码已经从自己保存的密码里找到了，账号能正常使用，恢复邮箱也能收信，没有被 Claude 封过。我还没买 VPS，下一步呢？',
        'VPS 还没买。我再问一下，后面 iPhone 订阅是不是用 Apple ID？我电脑还装了 ChatGPT 和 Photoshop，这些要卸载吗？',
        '我看到有人说明年这个套餐要涨到 129 美元，还说购买之前必须先买域名。这些是真的吗？我还在注册页面。']),
    'google': ('google', [
        '没有能正常登录的谷歌账号。',
        '就按你推荐的出海91买。把购买程序发我一下，刚才没看到图。是先注册谷歌吗？',
        '出海91网站已经注册并登录好了，下一步买哪个？',
        '买好了，账号资料也收到了，看不懂。',
        '刚才那个验证码还是不会弄，图没显示，你再教我一下。',
        '图都看到了，我现在知道账号和验证码怎么用了。还没实际登录，下一步呢？']),
    'google_reuse': ('google', [
        '设备和教程都准备好了，继续按流程，你现在要问我什么？',
        '我没有 Claude 账号，也没有登录过。',
        '有，我自己的 Gmail 能正常登录，从来没用过 Claude。']),
    'google_other_account': ('google', [
        '我的 Gmail 能登录，但是这个号以前用 Claude 被封过了。',
        '我还有一个自己的 Gmail 可以正常登录，这个号从来没用过 Claude。']),
    'gift': ('payment_preparation', [
        '我要买礼品卡，怎么购买？',
        '从备忘录点开了，现在已经在支付宝里面看到礼品卡页面了。',
        '美区礼品卡买好了，16位卡密也收到了，接下来呢？',
        '已经在这个美区 Apple 账户兑换成功，余额也确认足够了。']),
    'vps': ('vps', [
        '没有 VPS，按你们默认推荐帮我选。',
        '我打开注册页面了，英文看不懂，First Name、Last Name和地址怎么填？',
        '表单填好了。',
        '注册成功并登录 Client Area 了，商家系统默认选的是 Ubuntu 22.04，系统怎么选？',
        '已经按 Debian 12 买好了洛杉矶 VPS，标签 node-demo，时区 America/Los_Angeles，SSH访问也准备好了。这轮先给下一步，暂不执行服务器连接。']),
    'server': ('server', [
        '服务器已经买好，SSH资料已放在项目输入文件里了，请按程序检查后部署。',
        '我已经按你说的完成 Debian 12 重装，原 SSH 访问已经恢复，请重新检查并继续部署。']),
    'phone_gallery': ('phone_proxy', [
        '电脑这边已经完成了，现在开始配置我的 iPhone，怎么做？',
        '那个小火箭配置的图没看懂，再解释一下。',
        '小火箭已经安装，已导入并选中 node-a，连接的是同一台 VPS，全局路由选代理，VPN 已开启，节点连接成功。下一步呢？']),
    'login_gallery': ('login', [
        '手机网络已经验收通过，现在开始登录 Claude，怎么操作？',
        '现在要求身份验证器验证码，我还是不知道怎么用。',
        '已经用准备好的 Google 账号在 Claude App 登录成功，账号代号 claude-main。我知道之后电脑网页授权要用已配置的 AdsPower，继续订阅。']),
    'mac_gallery': ('computer_network', [
        '服务端已配置完成，现在开始配置我的 Mac，怎么做？',
        'Karing 的图还是没看懂，你重新说明一下。']),
    'network': ('computer_network', [
        'Windows客户端已配置：系统代理关闭，TUN开启，全局模式，旧VPN已关闭，断线测试和恢复完成，Codex回复正常。HTTP入口和目标出口已放在输入文件里，请实际检测后继续。',
        '刚才客户端选错了节点，现在已选回目标节点，HTTP入口不变。系统代理关闭、TUN和全局开启、旧VPN已关闭，断线恢复和Codex回复都正常。请重新检测，测通再继续。']),
}


DEVICE_BOUNDARY = r'''
"""Replay-only remote/network boundary; production controller stays unchanged."""
from network_real import *
from network_server import check_server_os, SystemMismatch
from workflow_guard import check

def fixture_main():
    action = sys.argv[1]
    route = sys.argv[sys.argv.index('--route')+1] if '--route' in sys.argv else None
    check(ROOT, 'network:' + action + (':' + route if route else ''))
    config(ROOT / '.local/network/input.json')
    try:
        if (ROOT / '.local/fixtures/ssh-unknown').exists():
            print(json.dumps({'status':'failed','error':'ssh_host_key_unknown','next_action':'先在真实终端核对并保存服务器主机指纹，再重试原动作。'}))
            return 1
        if action == 'probe':
            passed = read_json(ROOT / '.local/fixtures/probe.json')['passed']
            result = {'status':'passed' if passed else 'failed', 'route':route,
                      'exit_matches':passed, 'https_204':passed}
        else:
            observed = check_server_os(False, ROOT / '.local/fixtures/os-release')
            result = {'status':'passed','operating_system':observed}
            if action in ('deploy','export'):
                private_file(ROOT / '.local/network/node.txt', 'vless://isolated-replay-node\n')
                result.update(status='configured' if action=='deploy' else 'exported',node_file='.local/network/node.txt')
    except SystemMismatch as exc:
        result = exc.result
    print(json.dumps(result))
    return int(result['status']=='failed')

if __name__=='__main__': raise SystemExit(fixture_main())
'''

CLEANUP_BOUNDARY = r'''
"""Replay-only cleanup boundary; enforces workflow_guard without touching host HOME."""
from pathlib import Path
import sys
from workflow_guard import check

def main():
    root = Path(__file__).resolve().parents[1]
    op = 'apply' if '--apply' in sys.argv else ('restore' if '--restore' in sys.argv else 'audit')
    check(root, 'cleanup:' + op)
    print('只读审计（隔离演练）：检测到 Claude 桌面端与 CLI 可清理缓存；时区保持原值。')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
'''


def source_hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('scripts','references') for p in (root/folder).rglob('*')
            if p.is_file() and '__pycache__' not in p.parts}


def prepare(root, name, stage):
    for folder in ('scripts','references','assets'):
        shutil.copytree(ROOT/folder,root/folder,ignore=shutil.ignore_patterns('__pycache__'))
    for filename in ('AGENTS.md','SKILL.md','version.json'):
        shutil.copy2(ROOT/filename,root/filename)
    fixture=fixtures.WorkflowTests(); fixture.setUp()
    try:
        fixture.computer='mac' if name in ('mac_gallery','cross_stage_google','cleanup_scope','cleanup_logout_guard') else 'windows'; fixture.now=datetime.now(timezone.utc)
        if name in ('cleanup_scope','cleanup_logout_guard'):
            fixture.flow.submit(fixture.payload({'banned_login':'yes'}))
        fixture.reach(stage)
        if name=='phone_account_swap':
            fixture.flow.submit(fixture.payload({'node_label':'node-a','client':'Shadowrocket','client_available':True,'global_route':True,'vpn_connected':False,
                'apple_account_ref':'apple-old','account_origin':'purchased','account_type':'new','first_used_at':fixture.first_used_at.isoformat(),'store_signed_in':True,'apple_reminder_shown':True}))
        if name in ('missing_score','browser_swap'):
            data=fixture.data('browser')
            data['scores']['netcoffee']={'value':None,'result':'检测网站超时，另外两站正常'}
            fixture.flow.submit(fixture.payload(data))
        if name=='bought':
            fixture.flow.submit(fixture.payload({'google_account_status':'unavailable','purchase_channel':'chuhai91'}))
        if stage=='payment_preparation':
            data=fixture.data(stage); data['payment_ready']=False
            if name=='alipay': data['gift_channel']='alipay'
            fixture.flow.submit(fixture.payload(data))
        shutil.copytree(fixture.root/'.local',root/'.local')
    finally:
        fixture.doCleanups()
    version=json.loads((root/'version.json').read_text())['version']
    cache_check(root,version,failed_check(version),time.time())
    if name in ('vps','vps_recheck'):
        folder=root/'.local/fixtures'; folder.mkdir()
        pages={
            'dmit': {'url':'https://www.dmit.io/cart.php?region=los-angeles&network=premium&generation=as3',
                     'text':'Los Angeles Premium AS3\nLAX.AS3.Pro.TINY\nOut of Stock'},
            'bandwagon': {'url':'https://bandwagonhost.com/order/ecommerce/Los%20Angeles/USCA_9',
                         'text':'Configure Product\nUSCA_9 Memory 1 GB\nBilling Cycle\nQuarterly $49.99 USD\nRenewal $49.99 USD Quarterly\nContinue'},
        }
        if name=='vps_recheck':
            pages['bandwagon']['text']='USCA_9 2 GB Out of Stock'
        for vendor,page in pages.items(): (folder/(vendor+'.json')).write_text(json.dumps(page))
    if name in ('server','network','first_ssh'):
        folder=root/'.local/fixtures'; folder.mkdir()
        (folder/'os-release').write_text('ID=ubuntu\nVERSION_ID="22.04"\nPRETTY_NAME="Ubuntu 22.04 LTS"\n')
        (folder/'probe.json').write_text('{"passed":false}')
        if name=='first_ssh':
            (folder/'os-release').write_text('ID=debian\nVERSION_ID="12"\nPRETTY_NAME="Debian GNU/Linux 12"\n')
            (folder/'ssh-unknown').touch()
        network=root/'.local/network'; network.mkdir(exist_ok=True)
        (network/'input.json').write_text(json.dumps({'context':'isolated-replay',
            'ssh':{'host':'203.0.113.10','user':'root'},
            'server':{'address':'203.0.113.10','port':443,'panel_port':18899,'sni':'www.cloudflare.com'},
            'probe':{'proxy':'http://127.0.0.1:10809','expected_exit_ipv4':'203.0.113.10'}}))
        flow=Workflow(root); flow.state['network_signature']=flow.signature(); flow.save()
        shutil.copy2(root/'scripts/network.py',root/'scripts/network_real.py')
        (root/'scripts/network.py').write_text(DEVICE_BOUNDARY)
    if name in ('cleanup_scope','cleanup_logout_guard'):
        shutil.copy2(root/'scripts/cleanup.py',root/'scripts/cleanup_real.py')
        (root/'scripts/cleanup.py').write_text(CLEANUP_BOUNDARY)


def run_turn(root, message, transcript, prefix, model, timeout, snapshots=False):
    prompt=('这是隔离的客户带做演练。项目已经完成启动，.local 保存了当前进度和此前已验收的场景条件。'
            '按项目现有规则处理客户消息。仅运行本目录流程查询、图解、采集与观察提交；不操作真实设备、外部网页或支付。'
            '回复客户当前这一轮操作，直接展示需要的链接和原图。')
    if snapshots:
        prompt+=('演练使用固定的官方订购页浏览器快照 .local/fixtures/dmit.json 和 bandwagon.json，'
                 '不代表当前真实库存。用项目页面采集动作读这些 browser_file，按程序结果推进，不联网。')
    if (root/'scripts/network_real.py').exists():
        prompt+=('本演练的服务器 SSH 和网络请求已接到隔离测试替身，只有这些外部操作使用固定场景结果；'
                 '流程控制、系统规则、票据、回执与跳转仍使用项目真实实现。按客户要求调用 workflow run；'
                 '保持脚本与 .local/fixtures 文件不变，场景变化由测试主持者提供。')
    if (root/'scripts/cleanup_real.py').exists():
        prompt+=('本演练的清理脚本已接到隔离只读替身，不会修改真实主机文件；'
                 '可按控制层规则通过 workflow run --action cleanup_audit 执行审计回执，保持脚本文件不变。')
    prompt+='\n此前对话：\n'+json.dumps(transcript,ensure_ascii=False)+'\n客户本轮消息：'+message
    command=['codex','exec','--ephemeral','--json','--skip-git-repo-check','-C',str(root),
             '-s','workspace-write','-c','approval_policy="never"','-o',str(root/'reply.txt'),'-']
    if model: command[2:2]=['--model',model]
    (prefix.with_suffix('.input.txt')).write_text(prompt)
    reply=root/'reply.txt'
    if reply.exists(): reply.unlink()
    try:
        with prefix.with_suffix('.jsonl').open('w') as out, prefix.with_suffix('.stderr').open('w') as err:
            run=subprocess.run(command,input=prompt,text=True,stdout=out,stderr=err,timeout=timeout)
        code=run.returncode
    except subprocess.TimeoutExpired:
        code=124
    events=[]
    for line in prefix.with_suffix('.jsonl').read_text().splitlines():
        try: events.append(json.loads(line))
        except ValueError: pass
    response=reply.read_text() if reply.exists() else ''
    prefix.with_suffix('.md').write_text(response)
    commands=[e['item'].get('command','') for e in events
              if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution']
    return code,response,commands


def assess(root, name, turn, response, commands, before, code, transcript=()):
    view=Workflow(root).next(); stage=view['stage']
    checks={'model_completed':code==0,'workflow_called':any('workflow.py' in c for c in commands),
            'response_present':bool(response.strip()),'source_unchanged':source_hashes(root)==before}
    images=re.findall(r'!\[[^\]]*\]\(<?([^)>]+)>?\)',response)
    def picture(fragment): return any(fragment in x and Path(x).is_file() for x in images)
    if name in ('bought','repeat_code') or name=='google' and turn in (3,4):
        checks.update(code_link='https://2fa.run/' in response,
                      original_images=picture('/google-account/02-2fa-original.png') and picture('/google-account/03-google-code-original.png'),
                      no_early_login=stage in ('google','vps'))
        if name=='bought' or name=='google' and turn==3:
            checks['account_materials_picture']=picture('/google-account/01-order-original.png')
    elif name=='google':
        if turn==5:
            checks['vps_handoff']=stage=='vps' and 'VPS' in response
        else:
            checks['stage_preserved']=stage=='google'
        if turn==0:
            checks['two_sellers']='https://chuhai91.cc/' in response and 'https://gmailbuy.com/' in response
            checks['us_aged_account']=all(word in response for word in ('购买','美区','老号'))
        if turn in (0,1):
            checks['complete_purchase_gallery']=all(picture('/chuhai91/'+p) for p in
                ('01-register.png','02-google-aged-category.png','03-us-ip-product.png'))
            checks['direct_register_link']='https://chuhai91.cc/auth/register' in response
            checks['seller_registration']=re.search(r'注册[^。！\n]{0,20}出海91|出海91[^。！\n]{0,24}注册',response) is not None
        if turn==1:
            checks['new_purchase_preview']=all(picture('/google-account/'+p+'-original.png') for p in
                ('01-order','02-2fa','03-google-code'))
        if turn==2:
            checks['correct_purchase_step']=picture('/chuhai91/02-google-aged-category.png') or picture('/chuhai91/03-us-ip-product.png')
            checks['direct_category_link']='https://chuhai91.cc/categories/premium-aged-google-accounts' in response
    elif name in ('google_reuse', 'google_other_account'):
        finished = turn == len(JOURNEYS[name][1]) - 1
        records = Workflow(root).state['records']
        facts = records.get('google', {}).get('data', {})
        checks['expected_stage'] = stage == ('vps' if finished else 'google')
        checks['no_premature_purchase'] = 'https://chuhai91.cc/' not in response and 'https://gmailbuy.com/' not in response
        if finished:
            checks['correct_reuse'] = facts.get('account_origin') == 'self_used' and facts.get('google_account_status') == 'available'
            checks['vps_handoff'] = 'VPS' in response
        else:
            checks['awaiting_google_confirmation'] = 'google_account_status' not in facts
            checks['asks_about_google'] = ('Google' in response or 'Gmail' in response) and ('？' in response or '?' in response)
            checks['no_phone_requirement'] = '手机号' not in response and '短信' not in response
    elif name=='cross_stage_google':
        checks['expected_stage']=stage==('google' if turn<2 else 'vps')
        checks['no_blanket_phone_exemption']=not any(x in response for x in ('不需要外国手机号', 'Claude 注册不要求单独填写手机号', '不需要为注册 Claude 单独换号', '手机号不是注册 Claude 的必填项', '手机号不是注册 Claude 的固定必填项', '注册／登录 Claude 不需要外国手机号'))
        checks['login_not_completed']=not Workflow(root).state['records'].get('login',{}).get('data',{}).get('signed_in')
        if turn==2:
            checks['vps_next_step']='VPS' in response and '89.99' in response
    elif name=='computer_first':
        checks.update(phone_question=any(x in response for x in ('iPhone','安卓','手机类型')),stage_preserved=stage=='devices')
    elif name=='system' or name=='vps' and turn==3:
        checks.update(debian_recommended='Debian 12' in response,stage_preserved=stage=='vps')
    elif name=='stock':
        checks.update(stock_not_invented=not view['purchase_decision']['can_purchase'],
                      order_button_insufficient=any(x in response for x in ('不能','不代表','不足','先核对','先查','价格页')),stage_preserved=stage=='vps')
    elif name=='vps':
        if turn==0:
            decision=view['purchase_decision']
            checks.update(fallback=decision.get('vendor')=='bandwagon' and decision['can_purchase'],
                          actual_price='89.99' in response,stage_preserved=stage=='vps',
                          maintainer_offer=decision.get('source')=='maintainer',
                          no_customer_stock_lookup=not any(r['action']=='vps_capture' for r in Workflow(root).state['receipts']))
        elif turn in (1,2):
            checks['registration_does_not_complete_vps']=stage=='vps' and 'access_ready' in view['missing']
            if turn==1:
                checks['english_fields_explained']='First Name' in response and 'Last Name' in response
                checks['registration_form_picture']=picture('/vps-purchase/bandwagon-register-2.png')
        else:
            checks['server_handoff']=stage=='server' and 'server_readback' in view['missing']
    elif name=='support_recovery':
        view=Workflow(root).next()
        checks['expected_stage']=stage=='payment_preparation'
        checks['support_state']=view.get('status')=='needs_support' if turn==0 else view.get('status')!='needs_support'
        if turn==0:
            checks['support_gallery']=all(picture(f'/images/apple/{i}.jpg') for i in (18,19))
        else:
            checks['normal_gallery']=all(picture(f'/images/apple/{i}.jpg') for i in (14,15)) and not any(picture(f'/images/apple/{i}.jpg') for i in (18,19))
    elif name=='phone_account_swap':
        data=Workflow(root).state['records']['phone_proxy']['data']
        checks['proxy_preserved']=data.get('node_label')=='node-a' and data.get('client')=='Shadowrocket' and data.get('global_route') is True
        checks['new_account_recorded']=data.get('apple_account_ref')=='apple-new' and data.get('account_origin')=='self_used'
        checks['expected_stage']=stage==('phone_proxy' if turn==0 else 'timezone')
    elif name=='vps_recheck':
        flow=Workflow(root)
        decision=flow.purchase_decision(flow.state['records']['vps']['data'])
        checks['capture_used']=any(r['action']=='vps_capture' for r in flow.state['receipts'])
        checks['expected_purchase_state']=(not decision['can_purchase']) if turn==0 else decision['can_purchase'] and decision['plan']=='USCA_9-2GB'
        checks['expected_stage']=stage==('server' if turn==2 else 'vps')
    elif name=='first_ssh':
        receipts=Workflow(root).state['receipts']
        if turn==0:
            checks.update(unknown_host_recorded=any(r['result'].get('error')=='ssh_host_key_unknown' for r in receipts), stage_preserved=stage=='server', confirmation_explained='指纹' in response)
        else:
            checks.update(deployment_readback=any(r['action']=='server_deploy' and r['success'] for r in receipts),client_handoff=stage=='computer_network')
    elif name in ('cleanup_scope','cleanup_logout_guard'):
        receipts=Workflow(root).state['receipts']
        checks['expected_stage']=(stage=='cleanup') if turn==0 else (stage in ('devices','google') if name=='cleanup_logout_guard' else stage=='devices')
        checks['no_early_timezone_change']=not any('settimezone' in command for command in commands)
        if turn==1:
            checks['cleanup_audit_receipt']=any(r['action']=='cleanup_audit' and r['success'] for r in receipts)
        elif name=='cleanup_logout_guard':
            checks['rejects_logout_as_cleanup']=any(x in response for x in ('清理','审计','重装','删除'))
    elif name in ('missing_score','browser_swap'):
        checks['expected_stage']=stage==('browser' if turn==0 else 'phone_proxy')
        data=Workflow(root).state['records']['browser']['data']
        if name=='browser_swap':
            checks['usage_explanation_retained']=data.get('usage_explained') is True
            checks['new_profile_verification']=data.get('checked_profile_ref')==data.get('profile_ref') if turn==1 else not data.get('proxy_configured')
        else:
            checks['third_site_required']=data['scores']['netcoffee']['value'] is None if turn==0 else data['scores']['netcoffee']['value']==85
    elif name=='server':
        receipts=Workflow(root).state['receipts']
        if turn==0:
            checks.update(actual_mismatch=any(r['result'].get('error')=='server_os_mismatch' for r in receipts),
                          held_at_server=stage=='server',debian_explained='Debian 12' in response)
        else:
            checks.update(deployment_readback=any(r['action']=='server_deploy' and r['success'] for r in receipts),
                          client_handoff=stage=='computer_network')
    elif name=='network':
        receipts=Workflow(root).state['receipts']
        if turn==0:
            checks.update(failed_probe_recorded=any(r['action'].startswith('probe_') and not r['success'] for r in receipts),
                          held_at_network=stage=='computer_network')
        else:
            checks.update(both_probes=all(any(r['action']==action and r['success'] for r in receipts)
                                         for action in ('probe_proxy','probe_system')),browser_handoff=stage=='browser')
            checks['desktop_and_cli_explained'] = ('桌面' in response and ('Claude Code' in response or 'CLI' in response))
            checks['existing_usage_information'] = ('权限' in response and '正常' in response and any(x in response for x in ('反馈','交付','用户')))
    elif name in ('gift_buy','alipay') or name=='gift' and turn==0:
        checks.update(memo_jump='备忘录' in response and 'https://render.alipay.com/p/s/i/?scheme=' in response,
                      original_picture=picture('/images/apple/14.jpg'),stage_preserved=stage=='payment_preparation')
    elif name=='gift':
        data=Workflow(root).state['records']['payment_preparation']['data']
        if turn==1:
            checks.update(entry_recorded=data.get('gift_entry')=='opened',stage_preserved=stage=='payment_preparation')
        elif turn==2:
            checks.update(redeem_picture=picture('/images/apple/15.jpg'),stage_preserved=stage=='payment_preparation')
        else:
            checks.update(balance_confirmed=data.get('payment_ready') is True,app_handoff=stage=='app')
    if turn==0 and name in ('vps','gift','server','network','phone_gallery','login_gallery','mac_gallery'):
        required={
            'vps':[f'/vps-purchase/bandwagon-register-{i}.png' for i in range(1,5)]+['/vps-purchase/bandwagon-plan.png'],
            'gift':[f'/images/apple/{i:02}.jpg' for i in (14,15)],
            'server':[f'/images/network/{i}.jpg' for i in range(10,15)],
            'network':[f'/images/network/{i:02}.jpg' for i in (1,2,15,16,17)],
            'phone_gallery':['/images/network/14.jpg','/step-guides/phone-qr-import.png','/images/browser-iphone/10.jpg'],
            'login_gallery':[],
            'mac_gallery':[f'/images/network/{i:02}.jpg' for i in (1,2,19,20)],
        }[name]
        checks['complete_stage_gallery']=all(picture(p) for p in required)
        checks['no_unsolicited_support_images']=not any('/images/apple/'+p in x for x in images for p in ('18.jpg','19.jpg'))
        if name=='login_gallery':
            checks['no_purchased_order_for_personal_account']=not picture('/google-account/01-order-original.png')
        if name=='phone_gallery':
            checks['no_unrelated_account_images']=not any(picture(f'/images/apple/{i:02}.jpg') for i in range(1,10))
    if name=='network' and turn==1:
        checks['complete_browser_gallery']=all(picture(f'/images/browser-iphone/0{i}.png') for i in (1,2,3))
    if name in ('phone_gallery','login_gallery','mac_gallery'):
        expected = {'phone_gallery':'phone_proxy','login_gallery':'login','mac_gallery':'computer_network'}[name] if turn<2 else {'phone_gallery':'timezone','login_gallery':'subscription'}[name]
        checks['stage_preserved']=stage==expected
    return {'case':name,'turn':turn+1,'passed':all(checks.values()),'checks':checks,'stage':stage}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=tuple(CASES),action='append')
    parser.add_argument('--journey',choices=tuple(JOURNEYS),action='append')
    parser.add_argument('--output',type=Path,default=ROOT/'.local/model-replay')
    parser.add_argument('--model',help='本机 CLI 可用模型，省略则沿用当前配置')
    parser.add_argument('--timeout',type=int,default=240)
    args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    selections=[(x,CASES[x][0],[CASES[x][1]]) for x in args.case or []]
    selections += [(x,*JOURNEYS[x]) for x in args.journey or []]
    if not selections: selections=[(x,*v) for x,v in JOURNEYS.items()]
    summaries=[]
    for name,stage,messages in selections:
        with tempfile.TemporaryDirectory(prefix='claude-replay-') as temp:
            root=Path(temp); prepare(root,name,stage); before=source_hashes(root); transcript=[]
            for turn,message in enumerate(messages):
                if turn==1 and name=='vps_recheck':
                    p=root/'.local/fixtures/bandwagon.json'; page=json.loads(p.read_text())
                    page['text']='Configure Product\nUSCA_9 2 GB\nBilling Cycle\nQuarterly $89.99 USD\nRenewal $89.99 USD Quarterly\nContinue'
                    p.write_text(json.dumps(page))
                if turn==1 and name=='first_ssh':
                    (root/'.local/fixtures/ssh-unknown').unlink()
                if turn==1 and name=='server':
                    (root/'.local/fixtures/os-release').write_text('ID=debian\nVERSION_ID="12"\nPRETTY_NAME="Debian GNU/Linux 12"\n')
                if turn==1 and name=='network':
                    (root/'.local/fixtures/probe.json').write_text('{"passed":true}')
                fixture_before = {str(p): p.read_bytes() for p in (root/'.local/fixtures').glob('*') if p.is_file()}
                prefix=args.output/(name+'-'+str(turn+1))
                code,response,commands=run_turn(root,message,transcript,prefix,args.model,args.timeout,name=='vps_recheck')
                result=assess(root,name,turn,response,commands,before,code,transcript)
                result['checks']['fixture_unchanged'] = all(Path(p).is_file() and Path(p).read_bytes()==content for p,content in fixture_before.items())
                result['passed'] = all(result['checks'].values())
                result.update(model=args.model or 'configured_default',exit_code=code,input=message)
                summaries.append(result); transcript += [{'user':message,'assistant':response}]
                prefix.with_suffix('.state.json').write_text(json.dumps(Workflow(root).state,ensure_ascii=False,indent=2))
                print(json.dumps(result,ensure_ascii=False),flush=True)
                (args.output/'summary.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2))
                if code: return 1
    return int(not all(r['passed'] for r in summaries))


if __name__=='__main__': raise SystemExit(main())
