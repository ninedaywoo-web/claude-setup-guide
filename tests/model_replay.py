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
    'google': ('google', [
        '没有能正常登录 Claude 的 Google 账号。',
        '我选出海91，网站已经注册好了，下一步买什么？',
        '买好了，账号资料也收到了，看不懂。',
        '刚才那个验证码还是不会弄，图没显示，你再教我一下。']),
    'gift': ('payment_preparation', [
        '我要买礼品卡，怎么购买？',
        '从备忘录点开了，现在已经在支付宝里面看到礼品卡页面了。',
        '美区礼品卡买好了，16位卡密也收到了，接下来呢？',
        '已经在这个美区 Apple 账户兑换成功，余额也确认足够了。']),
    'vps': ('vps', [
        '没有 VPS，按你们默认推荐帮我选。',
        '就选你推荐的搬瓦工这档，商家默认是 Ubuntu 22.04，系统怎么选？',
        '已经按 Debian 12 买好了洛杉矶 VPS，标签 node-demo，时区 America/Los_Angeles，SSH访问也准备好了。这轮先给下一步，暂不执行服务器连接。']),
    'server': ('server', [
        '服务器已经买好，SSH资料已放在项目输入文件里了，请按程序检查后部署。',
        '我已经按你说的完成 Debian 12 重装，原 SSH 访问已经恢复，请重新检查并继续部署。']),
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
        fixture.computer='windows'; fixture.now=datetime.now(timezone.utc)
        fixture.reach(stage)
        if name=='bought':
            fixture.flow.submit(fixture.payload({'account_available':False,'purchase_channel':'chuhai91'}))
        if stage=='payment_preparation':
            data=fixture.data(stage); data['payment_ready']=False
            if name=='alipay': data['gift_channel']='alipay'
            fixture.flow.submit(fixture.payload(data))
        shutil.copytree(fixture.root/'.local',root/'.local')
    finally:
        fixture.doCleanups()
    version=json.loads((root/'version.json').read_text())['version']
    cache_check(root,version,failed_check(version),time.time())
    if name=='vps':
        folder=root/'.local/fixtures'; folder.mkdir()
        pages={
            'dmit': {'url':'https://www.dmit.io/cart.php?region=los-angeles&network=premium&generation=as3',
                     'text':'Los Angeles Premium AS3\nLAX.AS3.Pro.TINY\nOut of Stock'},
            'bandwagon': {'url':'https://bandwagonhost.com/order/ecommerce/Los%20Angeles/USCA_9',
                         'text':'Configure Product\nUSCA_9 Memory 1 GB\nBilling Cycle\nQuarterly $49.99 USD\nRenewal $49.99 USD Quarterly\nContinue'},
        }
        for vendor,page in pages.items(): (folder/(vendor+'.json')).write_text(json.dumps(page))
    if name in ('server','network'):
        folder=root/'.local/fixtures'; folder.mkdir()
        (folder/'os-release').write_text('ID=ubuntu\nVERSION_ID="22.04"\nPRETTY_NAME="Ubuntu 22.04 LTS"\n')
        (folder/'probe.json').write_text('{"passed":false}')
        network=root/'.local/network'; network.mkdir(exist_ok=True)
        (network/'input.json').write_text(json.dumps({'context':'isolated-replay',
            'ssh':{'host':'203.0.113.10','user':'root'},
            'server':{'address':'203.0.113.10','port':443,'panel_port':18899,'sni':'www.cloudflare.com'},
            'probe':{'proxy':'http://127.0.0.1:10809','expected_exit_ipv4':'203.0.113.10'}}))
        flow=Workflow(root); flow.state['network_signature']=flow.signature(); flow.save()
        shutil.copy2(root/'scripts/network.py',root/'scripts/network_real.py')
        (root/'scripts/network.py').write_text(DEVICE_BOUNDARY)


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


def assess(root, name, turn, response, commands, before, code):
    view=Workflow(root).next(); stage=view['stage']
    checks={'model_completed':code==0,'workflow_called':any('workflow.py' in c for c in commands),
            'response_present':bool(response.strip()),'source_unchanged':source_hashes(root)==before}
    images=re.findall(r'!\[[^\]]*\]\(<?([^)>]+)>?\)',response)
    def picture(fragment): return any(fragment in x and Path(x).is_file() for x in images)
    if name in ('bought','repeat_code') or name=='google' and turn>=2:
        checks.update(code_link='https://2fa.run/' in response,
                      original_images=picture('/google-account/02-2fa-original.png') and picture('/google-account/03-google-code-original.png'),
                      no_early_login=stage in ('google','vps'))
        if name=='bought' or name=='google' and turn==2:
            checks['account_materials_picture']=picture('/google-account/01-order-original.png')
    elif name=='google':
        checks['stage_preserved']=stage=='google'
        if turn==0:
            checks['two_sellers']='https://chuhai91.cc' in response and 'https://gmailbuy.com' in response
            checks['us_aged_account']='美区' in response and '老号' in response
        else:
            checks['correct_purchase_step']=picture('/chuhai91/02-google-aged-category.png') or picture('/chuhai91/03-us-ip-product.png')
    elif name=='computer_first':
        checks.update(phone_question=any(x in response for x in ('iPhone','安卓','手机类型')),stage_preserved=stage=='devices')
    elif name=='system' or name=='vps' and turn==1:
        checks.update(debian_recommended='Debian 12' in response,stage_preserved=stage=='vps')
    elif name=='stock':
        checks.update(stock_not_invented=not view['purchase_decision']['can_purchase'],
                      order_button_insufficient=any(x in response for x in ('不能','不代表','不足','先核对','先查','价格页')),stage_preserved=stage=='vps')
    elif name=='vps':
        if turn==0:
            decision=view['purchase_decision']
            checks.update(fallback=decision.get('vendor')=='bandwagon' and decision['can_purchase'],
                          actual_price='49.99' in response,stage_preserved=stage=='vps',
                          page_captures=sum(r['action']=='vps_capture' for r in Workflow(root).state['receipts'])>=2)
        else:
            checks['server_handoff']=stage=='server' and 'server_readback' in view['missing']
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
                if turn==1 and name=='server':
                    (root/'.local/fixtures/os-release').write_text('ID=debian\nVERSION_ID="12"\nPRETTY_NAME="Debian GNU/Linux 12"\n')
                if turn==1 and name=='network':
                    (root/'.local/fixtures/probe.json').write_text('{"passed":true}')
                fixture_before = {str(p): p.read_bytes() for p in (root/'.local/fixtures').glob('*') if p.is_file()}
                prefix=args.output/(name+'-'+str(turn+1))
                code,response,commands=run_turn(root,message,transcript,prefix,args.model,args.timeout,name=='vps')
                result=assess(root,name,turn,response,commands,before,code)
                result['checks']['fixture_unchanged'] = all(Path(p).is_file() and Path(p).read_bytes()==content for p,content in fixture_before.items())
                result['passed'] = all(result['checks'].values())
                result.update(model=args.model or 'configured_default',exit_code=code,input=message)
                summaries.append(result); transcript += [{'user':message,'assistant':response}]
                prefix.with_suffix('.state.json').write_text(json.dumps(Workflow(root).state,ensure_ascii=False,indent=2))
                print(json.dumps(result,ensure_ascii=False),flush=True)
                (args.output/'summary.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2))
                if code: break
    return int(not all(r['passed'] for r in summaries))


if __name__=='__main__': raise SystemExit(main())
