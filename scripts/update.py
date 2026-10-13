#!/usr/bin/env python3
"""Check a public GitHub guide; apply only a user-approved, pinned commit."""
import argparse, base64, hashlib, io, json, math, os, re, shutil, stat, subprocess, sys, tempfile, time, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
REPO = 'ninedaywoo-web/claude-setup-guide'
ROOT = Path(__file__).resolve().parents[1]
LIMIT = 250 * 1024 * 1024
CHECK_INTERVAL = 24 * 60 * 60
CACHE_SCHEMA = 1
CACHE_PATH = Path('.local/update-check.json')
class UpdateError(Exception): pass
class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        from urllib.parse import urlparse
        host=urlparse(newurl).hostname
        if urlparse(newurl).scheme!='https' or host not in {'api.github.com','codeload.github.com','github.com'}:
            raise UpdateError('更新下载跳转到了不支持的地址。')
        new=super().redirect_request(req,fp,code,msg,headers,newurl)
        if host!='api.github.com': new.remove_header('Authorization')
        return new

def token():
    value=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if value:return value
    if shutil.which('gh'):
        try:
            r=subprocess.run(['gh','auth','token','--hostname','github.com'],capture_output=True,text=True,timeout=10)
            if r.returncode==0:return r.stdout.strip()
        except (OSError,subprocess.TimeoutExpired):pass
    return None

def request(path, auth, binary=False):
    headers={'User-Agent':'claude-setup-guide-updater','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
    if auth:headers['Authorization']='Bearer '+auth
    req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,headers=headers)
    with urllib.request.build_opener(Redirect()).open(req,timeout=30) as response:
        data=response.read(LIMIT+1)
    if len(data)>LIMIT:raise UpdateError('下载体积超过上限。')
    return data if binary else json.loads(data)

def file_json(name,commit,auth):
    obj=request('contents/'+name+'?ref='+commit,auth)
    return json.loads(base64.b64decode(obj['content']))

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(root):return json.loads((root/'manifest.json').read_text())['files']
def verify(root):
    files=manifest(root)
    for name,expected in files.items():
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name or path.parts[0] in {'.local','.git'}:raise UpdateError('文件清单包含非法路径。')
        p=root/name
        if p.is_symlink() or not p.is_file() or digest(p)!=expected:raise UpdateError('文件校验失败：'+name)
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != set(files)|{'manifest.json'}:raise UpdateError('更新包包含未列入清单的文件。')

def extract_archive(data,dest):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names=set();prefix=None;total=0
        for m in z.infolist():
            p=PurePosixPath(m.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in m.filename or not p.parts:raise UpdateError('更新包包含非法路径。')
            if prefix is None:prefix=p.parts[0]
            if prefix!=p.parts[0]:raise UpdateError('更新包根目录不一致。')
            if stat.S_ISLNK(m.external_attr>>16):raise UpdateError('更新包不允许符号链接。')
            parts=p.parts[1:]
            if not parts:continue
            if parts[0] in {'.local','.git'}:raise UpdateError('更新包包含用户数据目录。')
            rel=PurePosixPath(*parts).as_posix()
            if rel in names:raise UpdateError('更新包路径重复。')
            names.add(rel);total+=m.file_size
            if total>LIMIT:raise UpdateError('更新包解压体积超过上限。')
            target=dest/rel
            if m.is_dir():target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                with z.open(m) as inp,target.open('wb') as out:shutil.copyfileobj(inp,out)
    verify(dest)

def replace_package(root,new):
    old=manifest(root)
    for name,expected in old.items():
        p=root/name
        if not p.is_file() or digest(p)!=expected:raise UpdateError('本地课程已有改动，已停止覆盖：'+name)
    allowed=set(old)|{'manifest.json'}
    for p in root.rglob('*'):
        rel=p.relative_to(root)
        if rel.parts[0] in {'.local','.git'} or '__pycache__' in rel.parts:continue
        if p.is_file() and rel.as_posix() not in allowed:raise UpdateError('发现额外本地文件，请移入 .local 后再更新：'+str(rel))
    for name in ['.local','.git']:
        p=root/name
        if p.is_symlink():raise UpdateError('用户目录为符号链接，请手动更新。')
        if p.exists():shutil.copytree(p,new/name)
    backup=Path(tempfile.mkdtemp(prefix=root.name+'-backup-',dir=root.parent));backup.rmdir()
    root.rename(backup)
    try:new.rename(root)
    except BaseException:
        backup.rename(root)
        raise
    return backup

def version_parts(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d+(?:\.\d+){0,2}',value):
        raise UpdateError('版本号格式不支持，请使用数字版本号，例如 1.0.9。')
    parts=tuple(int(part) for part in value.split('.'))
    return parts+(0,)*(3-len(parts))

def version_result(local_version,remote,commit):
    if not isinstance(commit,str) or not re.fullmatch('[a-f0-9]{40}',commit):
        raise UpdateError('远端提交标识无效，未生成更新命令。')
    if remote.get('repository',REPO)!=REPO:
        raise UpdateError('仓库标识不一致。')
    local_parts=version_parts(local_version)
    remote_version=remote['version']
    remote_parts=version_parts(remote_version)
    status='update_available' if remote_parts>local_parts else 'local_ahead' if remote_parts<local_parts else 'current'
    summary=remote.get('summary',[])
    if not isinstance(summary,list) or not all(isinstance(item,str) for item in summary):
        raise UpdateError('远端更新摘要格式无效。')
    recommendations={
        'update_available':'建议更新；用户同意后再更新。',
        'local_ahead':'本地版本高于远端版本，无需更新，不建议回退。',
        'current':'当前版本与远端版本一致。',
    }
    return {
        'status':status,'local_version':local_version,'remote_version':remote_version,
        'commit':commit,'summary':summary,'recommendation':recommendations[status],
        'update_notice':f'已有最新更新（v{remote_version}），建议更新。' if status=='update_available' else None,
        'apply_command':f'python3 scripts/update.py apply --commit {commit}' if status=='update_available' else None,
    }

def failed_check(local_version,status='unavailable'):
    return {
        'status':status,'local_version':local_version,'update_notice':None,'apply_command':None,
        'message':'本次未能检查更新。继续使用本地教程；可运行 python3 scripts/update.py check --force 重试。',
    }

def cached_check(root,local_version,now):
    try:
        record=json.loads((root/CACHE_PATH).read_text())
        if record['schema']!=CACHE_SCHEMA or record['repository']!=REPO or record['local_version']!=local_version:
            return None
        checked_at=record['checked_at']
        if isinstance(checked_at,bool) or not isinstance(checked_at,(int,float)) or not math.isfinite(checked_at):
            return None
        if not 0<=now-checked_at<CHECK_INTERVAL:
            return None
        previous=record['result']
        if previous['status'] in {'current','update_available','local_ahead'}:
            # Rebuild the notice and command; never execute instructions stored in a cache.
            result=version_result(local_version,{'version':previous['remote_version'],'summary':previous['summary']},previous['commit'])
            if result['status']!=previous['status']:
                return None
        elif previous['status'] in {'unavailable','not_updated'}:
            result=failed_check(local_version,previous['status'])
        else:
            return None
        return result,checked_at
    except (OSError,ValueError,TypeError,KeyError,UpdateError):
        return None

def cache_check(root,local_version,result,checked_at):
    cache=root/CACHE_PATH
    temporary=None
    try:
        cache.parent.mkdir(parents=True,exist_ok=True)
        record={'schema':CACHE_SCHEMA,'repository':REPO,'local_version':local_version,'checked_at':checked_at,'result':result}
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',prefix='.update-check-',suffix='.json',dir=cache.parent,delete=False) as out:
            temporary=Path(out.name)
            json.dump(record,out,ensure_ascii=False,indent=2)
            out.write('\n')
        temporary.replace(cache)
        return True
    except OSError:
        return False
    finally:
        if temporary is not None:
            try:temporary.unlink(missing_ok=True)
            except OSError:pass

def check(root,auth,force=False,now=None):
    local_version=json.loads((root/'version.json').read_text())['version']
    now=time.time() if now is None else now
    saved=None if force else cached_check(root,local_version,now)
    if saved is not None:
        result,checked_at=saved
        cache_saved=True
    else:
        try:
            commit=request('git/ref/heads/main',auth)['object']['sha']
            remote=file_json('version.json',commit,auth)
            result=version_result(local_version,remote,commit)
        except UpdateError:
            result=failed_check(local_version,'not_updated')
        except Exception:
            # Do not expose remote responses, credentials, or network errors.
            result=failed_check(local_version)
        checked_at=now
        cache_saved=cache_check(root,local_version,result,checked_at)
    return dict(result,cached=saved is not None,cache_saved=cache_saved,
                checked_at=datetime.fromtimestamp(checked_at,timezone.utc).isoformat(),
                next_check_at=datetime.fromtimestamp(checked_at+CHECK_INTERVAL,timezone.utc).isoformat())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['check','apply']);ap.add_argument('--commit');ap.add_argument('--force',action='store_true',help='check 时忽略 24 小时缓存，立即重新联网');args=ap.parse_args()
    if args.force and args.action!='check':ap.error('--force 仅适用于 check。')
    try:
        auth=None  # Public repository: no login or credential lookup required.
        if args.action=='check':result=check(ROOT,auth,force=args.force)
        else:
            if not args.commit or not re.fullmatch('[a-f0-9]{40}',args.commit):raise UpdateError('请使用刚才检查到并经用户同意的完整提交 SHA。')
            meta=file_json('version.json',args.commit,auth)
            if meta['repository']!=REPO:raise UpdateError('仓库标识不一致。')
            data=request('zipball/'+args.commit,auth,binary=True)
            with tempfile.TemporaryDirectory(prefix='.guide-update-',dir=ROOT.parent) as work:
                new=Path(work)/ROOT.name;new.mkdir();extract_archive(data,new)
                if json.loads((new/'version.json').read_text())!=meta:raise UpdateError('包版本与批准的版本不一致。')
                backup=replace_package(ROOT,new)
            result={'status':'updated','version':meta['version'],'backup':str(backup),'message':'已保留 .local 进度。请重新读取 SKILL.md 和变更章节。'}
    except UpdateError as e:result={'status':'not_updated','message':str(e)}
    except Exception:
        # Never log headers, credentials, response bodies, or credential-helper stderr.
        result={'status':'unavailable','message':'本次无法检查或下载更新。请稍后重试，或从公开仓库下载最新 ZIP。继续使用本地教程。'}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status'] in {'current','local_ahead','update_available','updated'} else 2
if __name__=='__main__':sys.exit(main())
