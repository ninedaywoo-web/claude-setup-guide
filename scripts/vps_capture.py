#!/usr/bin/env python3
"""Capture an official order page for the workflow's stock observations."""
import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from network import private_file
from workflow_guard import check

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {'dmit': ('dmit.io', 'www.dmit.io'),
         'bandwagon': ('bandwagonhost.com', 'www.bandwagonhost.com'),
         'akile': ('akile.ai', 'www.akile.ai')}


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.hidden = [], 0
        self.configuration = False
        self.login = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1
        a = dict(attrs)
        if a.get('id', '').lower() == 'frmconfigureproduct':
            self.configuration = True
        if tag == 'input' and a.get('type', '').lower() == 'password':
            self.login = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, text):
        if not self.hidden and text.strip():
            self.parts.append(text.strip())


def official_url(vendor, url):
    u = urlsplit(url)
    if vendor not in HOSTS or u.scheme != 'https' or u.hostname not in HOSTS[vendor] or u.username or u.password:
        raise ValueError('使用当前商家的官方订购网址')
    if vendor == 'dmit' and u.path != '/cart.php':
        raise ValueError('DMIT 从 cart.php 订购页采集')
    if vendor == 'bandwagon' and not u.path.startswith(('/order/', '/cart.php')):
        raise ValueError('搬瓦工从 order 或 cart.php 订购页采集')


def capture(options, root):
    if not isinstance(options, dict) or not isinstance(options.get('vendor'), str) or not isinstance(options.get('url'), str):
        raise ValueError('填写 vendor 与实际页面 url')
    if 'browser_file' in options and (not isinstance(options['browser_file'], str) or not options['browser_file'].strip()):
        raise ValueError('browser_file 使用浏览器采集文件路径')
    vendor, url = options['vendor'], options['url']
    official_url(vendor, url)
    method, code = 'http', 200
    if options.get('browser_file'):
        path = Path(options['browser_file']).resolve()
        if (root / '.local').resolve() not in path.parents:
            raise ValueError('浏览器原始采集文件放入本项目 .local')
        snapshot = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(snapshot, dict) or snapshot.get('url') != url or not isinstance(snapshot.get('text'), str) or not snapshot['text'].strip():
            raise ValueError('浏览器采集须包含实际 url 与原始可见 text')
        text, method, configured, login = snapshot['text'], 'browser', False, False
    else:
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 ClaudeSetupGuide'})
            with urllib.request.urlopen(request, timeout=20) as response:
                url = response.geturl()
                official_url(vendor, url)
                html = response.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as exc:
            code, html = exc.code, exc.read().decode('utf-8', errors='replace')
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            code, html = 0, str(exc)
        parser = PageText()
        parser.feed(html)
        text, configured, login = '\n'.join(parser.parts), parser.configuration, parser.login
    lowered = text.lower()
    if code != 200 or any(x in lowered for x in ('just a moment', 'verify you are human', 'checking your browser')):
        page = 'error' if code != 200 else 'challenge'
    elif configured or (re.search(r'configure|配置产品|配置商品', lowered) and re.search(r'billing cycle|计费周期|付款周期', lowered)):
        page = 'configuration'
    elif login or any(x in lowered for x in ('please login to continue', 'sign in to continue', '请先登录')):
        page = 'login'
    else:
        page = 'catalog'
    at = datetime.now(timezone.utc).isoformat()
    sha = hashlib.sha256((url + '\n' + text).encode()).hexdigest()
    dest = root / '.local/vps-pages' / (sha + '.json')
    result = {'vendor': vendor, 'url': url, 'text': text, 'page': page, 'http_status': code,
              'checked_at': at, 'sha256': sha, 'capture_method': method,
              'capture_file': str(dest)}
    private_file(dest, json.dumps(result, ensure_ascii=False, indent=2))
    return dict(result, status='captured')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    try:
        check(ROOT, 'vps:capture')
        result = capture(json.loads(args.input.read_text(encoding='utf-8')), ROOT)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
