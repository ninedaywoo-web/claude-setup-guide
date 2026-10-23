#!/usr/bin/env python3
"""Windows cleanup core adapted from MIT-licensed CCBaga target/key rules.

See licenses/README.md. No desktop shell, browser engine or system ID changes.
"""
import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from network_server import Failure, require, save
from network import lock

KEYS = json.loads(Path(__file__).with_name("windows-cleanup-keys.json").read_text(encoding="utf-8"))
CACHE = ("Cache", "Code Cache", "GPUCache", "DawnCache", "DawnGraphiteCache", "DawnWebGPUCache", "GraphiteDawnCache",
         "ShaderCache", "GrShaderCache", "Service Worker/CacheStorage", "Service Worker/ScriptCache", "logs", "Crashpad")
STORAGE = ("Local Storage", "Session Storage", "IndexedDB", "Network", "Cookies", "Cookies-journal", "Service Worker",
           "WebStorage", "Sessions", "Storage", "Shared Dictionary", "SharedStorage", "SharedStorage-wal", "DIPS",
           "DIPS-journal", "DIPS-wal", "DIPS-shm", "TransportSecurity", "Trust Tokens", "Trust Tokens-journal",
           "Reporting and Nel", "Reporting and Nel-journal", "Network Persistent State", "BrowsingTopicsState", "blob_storage")
SCOPES = ("cache", "account", "credentials", "desktop")


def safe(path):
    # lstat at every level catches NTFS junctions, symlinks and redirected parents.
    for p in [path] + list(path.parents):
        try:
            m = p.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(m.st_mode) and not (getattr(m, "st_file_attributes", 0) & 0x400), "linked_path_refused")
        require(stat.S_ISDIR(m.st_mode) or stat.S_ISREG(m.st_mode), "special_file_refused")


def snapshot(path):
    safe(path)
    if not path.exists():
        return None
    result = {}
    def visit(p):
        safe(p)
        rel = str(p.relative_to(path))
        if p.is_dir():
            result[rel] = "directory"
            for child in sorted(p.iterdir()):
                visit(child)
        else:
            h = hashlib.sha256()
            with p.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            result[rel] = h.hexdigest()
    visit(path)
    return result


def definitions(home, roaming, local):
    items = []
    def add(path, scope, operation="move"):
        items.append({"path": str(path), "scope": scope, "operation": operation})
    for name in ("cache", "stats-cache.json", "telemetry", "usage-data", "usage.jsonl", "usage.with-fix.jsonl"):
        add(home / ".claude" / name, "cache")
    add(home / ".claude.json", "account", "edit")
    for name in (".user-id", ".machine-id"):
        add(home / ".claude" / name, "account")
    add(home / ".claude/.credentials.json", "credentials", "edit")
    package = local / "Packages/Claude_pzs8sxrjxfjjc/LocalCache"
    roots = [base / name for base in (roaming, local, package / "Roaming", package / "Local") for name in ("Claude", "Claude-3p")]
    for root in roots:
        for name in CACHE:
            add(root / name, "cache")
        for name in STORAGE:
            add(root / name, "desktop")
    for root in (local, package / "Local"):
        add(root / "claude-cli-nodejs", "cache")
    return items


def transform(text, scope):
    data = json.loads(text)
    require(isinstance(data, dict), "config_object_required")
    removed = [key for key in KEYS[scope] if key in data]
    for key in removed:
        del data[key]
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n", removed


def plan(home, roaming, local, scopes):
    require(bool(scopes) and set(scopes) <= set(SCOPES), "invalid_cleanup_scope")
    entries = []
    for item in definitions(home, roaming, local):
        if item["scope"] not in scopes:
            continue
        path = Path(item["path"])
        before = snapshot(path)
        if before is None:
            continue
        item = dict(item, before=before)
        if item["operation"] == "edit":
            require(path.stat().st_size <= 8 * 1024 * 1024, "config_too_large")
            _, keys = transform(path.read_text(encoding="utf-8-sig"), item["scope"])
            if not keys:
                continue
            item["keys"] = keys
        entries.append(item)
    # Desktop scope contains Service Worker; do not move its children twice.
    entries = [x for x in entries if not any(Path(y["path"]) in Path(x["path"]).parents for y in entries)]
    return {"schema": 1, "home": str(home), "roaming": str(roaming), "local": str(local), "scopes": list(scopes), "entries": entries}


def processes_stopped():
    script = r"""$ErrorActionPreference='Stop'; $busy=$false
Get-CimInstance Win32_Process | ForEach-Object {
 if ($_.Name -match '^(claude|claude-code|claude-3p)(\.exe)?$') {$busy=$true}
 if ($_.Name -match '^(node|bun)(\.exe)?$') {
  if (!$_.CommandLine) {throw 'process inspection unavailable'}
  if ($_.CommandLine -match '(@anthropic-ai[\\/]claude-code|[\\/]claude-code[\\/])') {$busy=$true}
 }
}; if ($busy) {exit 3}
"""
    r = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True, timeout=30)
    require(r.returncode == 0, "close_claude_or_resolve_process_inspection")


def protect(folder):
    r = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                        "[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value"], capture_output=True, text=True, timeout=15)
    sid = r.stdout.strip()
    require(r.returncode == 0 and sid.startswith("S-1-") and all(x.isdigit() for x in sid[2:].split("-")), "user_sid_unavailable")
    r = subprocess.run(["icacls.exe", str(folder), "/inheritance:r", "/grant:r", "*" + sid + ":(OI)(CI)F"], capture_output=True, timeout=15)
    require(r.returncode == 0, "backup_acl_failed")


def copy(source, target):
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)


def revalidate(p):
    allowed = {(x["path"], x["scope"], x["operation"]) for x in definitions(Path(p["home"]), Path(p["roaming"]), Path(p["local"]))}
    for e in p["entries"]:
        require((e["path"], e["scope"], e["operation"]) in allowed, "target_not_allowlisted")
        require(snapshot(Path(e["path"])) == e["before"], "target_changed_rescan_required")


def apply(p, batch, check=processes_stopped, secure=protect):
    check()
    revalidate(p)
    safe(batch)
    require(not batch.exists(), "backup_batch_exists")
    batch.mkdir(parents=True, mode=0o700)
    secure(batch)
    journal = dict(p, status="backing_up", completed=[])
    save(batch / "manifest.json", journal)
    try:
        # Back up and verify ALL selected targets before changing the first one.
        for n, e in enumerate(p["entries"]):
            src = Path(e["path"])
            dst = batch / ("backup-%d" % n)
            copy(src, dst)
            require(snapshot(dst) == e["before"] and snapshot(src) == e["before"], "backup_verification_failed")
        check()
        revalidate(p)
        journal["status"] = "applying"
        save(batch / "manifest.json", journal)
        for n, e in enumerate(p["entries"]):
            check()
            src = Path(e["path"])
            require(snapshot(src) == e["before"], "target_changed_rescan_required")
            # Journal the intent before mutation so interruption can be reconciled.
            if e["operation"] == "edit":
                value, _ = transform(src.read_text(encoding="utf-8-sig"), e["scope"])
                expected = {".": hashlib.sha256(value.encode()).hexdigest()}
            else:
                value, expected = None, None
            journal["pending"] = {"index": n, "after": expected}
            save(batch / "manifest.json", journal)
            if value is not None:
                # Keep credentials private, including the replacement file's ACL.
                tmp = batch / "replacement.json"
                with tmp.open("w", encoding="utf-8", newline="") as f:
                    f.write(value)
                os.replace(tmp, src)
            else:
                # Recoverable quarantine; never permanently delete or clear trash.
                shutil.move(str(src), str(batch / ("removed-%d" % n)))
            require(snapshot(src) == expected, "cleanup_readback_failed")
            journal["completed"].append(journal.pop("pending"))
            save(batch / "manifest.json", journal)
        journal["status"] = "completed"
        save(batch / "manifest.json", journal)
    except BaseException:
        journal["status"] = "partial"
        save(batch / "manifest.json", journal)
        raise
    return {"status": "completed", "items": len(journal["completed"]), "backup": str(batch)}


def restore(batch, check=processes_stopped):
    safe(batch)
    p = json.loads((batch / "manifest.json").read_text(encoding="utf-8"))
    require(p["schema"] == 1, "invalid_backup_schema")
    allowed = {(x["path"], x["scope"], x["operation"]) for x in definitions(Path(p["home"]), Path(p["roaming"]), Path(p["local"]))}
    todo = list(p["completed"])
    if p.get("pending"):
        todo.append(p["pending"])
    # Resolve interrupted operations by content, refuse to overwrite new user data.
    for item in todo:
        n = item["index"]
        e = p["entries"][n]
        require((e["path"], e["scope"], e["operation"]) in allowed, "target_not_allowlisted")
        require(snapshot(batch / ("backup-%d" % n)) == e["before"], "backup_verification_failed")
        current = snapshot(Path(e["path"]))
        require(current in (e["before"], item["after"]), "new_data_refuse_restore")
    check()
    p['status'] = 'restoring'
    p['restore_completed'] = []
    save(batch / 'manifest.json', p)
    for item in reversed(todo):
        n = item["index"]; e = p["entries"][n]; dst = Path(e["path"])
        check()
        current = snapshot(dst)
        if current == e["before"]:
            p['restore_completed'].append(n)
            save(batch / 'manifest.json', p)
            continue
        require(current == item["after"], "new_data_refuse_restore")
        dst.parent.mkdir(parents=True, exist_ok=True)
        if e["operation"] == "edit":
            temp = batch / "restore.tmp"
            shutil.copy2(batch / ("backup-%d" % n), temp)
            check()
            require(snapshot(dst) == item['after'], 'new_data_refuse_restore')
            os.replace(temp, dst)
        else:
            # Build on the destination filesystem; interruption leaves dst absent.
            with tempfile.TemporaryDirectory(prefix='.claude-restore-', dir=dst.parent) as staging:
                temp = Path(staging) / 'content'
                copy(batch / ("backup-%d" % n), temp)
                require(snapshot(temp) == e['before'], 'restore_verification_failed')
                check()
                require(snapshot(dst) == item['after'], 'new_data_refuse_restore')
                temp.rename(dst)
        require(snapshot(dst) == e["before"], "restore_verification_failed")
        p['restore_completed'].append(n)
        save(batch / 'manifest.json', p)
    p["status"] = "restored"
    save(batch / "manifest.json", p)
    return {"status": "restored", "backup": str(batch)}


def main():
    parser = argparse.ArgumentParser(description="Windows 端清理 Skill：审计、备份、按范围清理与恢复")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--audit", action="store_true")
    group.add_argument("--apply", action="store_true")
    group.add_argument("--restore", metavar="BACKUP_DIRECTORY")
    parser.add_argument("--scope", nargs="+", choices=SCOPES, default=["cache"])
    args = parser.parse_args()
    try:
        from workflow_guard import check
        try:
            check(Path(__file__).resolve().parents[1], 'cleanup:' + ('restore' if args.restore else ('apply' if args.apply else 'audit')))
        except ValueError as exc:
            raise Failure(str(exc))
        require(sys.platform == "win32", "windows_required")
        home = Path.home()
        roaming = Path(os.environ["APPDATA"])
        local = Path(os.environ["LOCALAPPDATA"])
        if args.restore:
            batch = Path(args.restore).absolute()
            require(home / "ClaudeBackups/windows-cleanup" in batch.parents, "unexpected_backup_location")
            p = json.loads((batch / "manifest.json").read_text(encoding="utf-8"))
            require((p["home"], p["roaming"], p["local"]) == tuple(map(str, (home, roaming, local))), "backup_device_mismatch")
        else:
            p = plan(home, roaming, local, args.scope)
            print(json.dumps({"status": "audited", "targets": [{k: v for k, v in e.items() if k != "before"} for e in p["entries"]]}, ensure_ascii=False, indent=2))
            if not args.apply:
                return 0
            require(bool(p["entries"]), "no_matching_targets")
            batch = home / "ClaudeBackups/windows-cleanup" / uuid.uuid4().hex
        require(sys.stdin.isatty(), "interactive_confirmation_required")
        print("将恢复所选批次。" if args.restore else "将备份并校验以上项目，再处理所选范围。account/credentials/desktop 可能退出登录；保留项目、Skills、MCP 和其他设置。")
        if input("确认以上实际范围后输入 CONFIRM；其他输入取消：").strip() != "CONFIRM":
            print("已取消，未修改。")
            return 0
        with lock(home / "ClaudeBackups/windows-cleanup"):
            result = restore(batch) if args.restore else apply(p, batch)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"status": "failed_or_partial", "error": str(e) if isinstance(e, Failure) else type(e).__name__}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
