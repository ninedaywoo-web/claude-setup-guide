#!/usr/bin/env python3
"""Open the fixed local Google account purchase and 2FA visual guide."""
import json
from pathlib import Path
import sys
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
GUIDE_RELATIVE = Path('assets/google-account/guide.html')


def guide_info(root=ROOT):
    candidate = (Path(root) / GUIDE_RELATIVE).resolve()
    path = candidate if candidate.is_file() else (ROOT / GUIDE_RELATIVE).resolve()
    return {
        'exists': path.is_file(),
        'path': path.as_posix(),
        'url': path.as_uri(),
        'markdown_link': f'[打开本地 Google 账号购买与 2FA 图文指南](<{path.as_posix()}>)',
    }


def open_google_guide(root=ROOT, opener=None):
    info = guide_info(root)
    if not info['exists']:
        return {**info, 'status': 'missing', 'opened': False}
    try:
        opened = bool((opener or webbrowser.open)(info['url']))
    except Exception as exc:
        return {**info, 'status': 'fallback', 'opened': False, 'open_error': str(exc)}
    return {**info, 'status': 'opened' if opened else 'fallback', 'opened': opened}


def main():
    result = open_google_guide(ROOT)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['exists'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
