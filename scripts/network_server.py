#!/usr/bin/env python3
"""Linux helper sent over SSH; one JSON request on stdin, one JSON result.

Only installs a fresh, pinned 3x-ui or resumes its own installation. Never
adopts/upgrades someone else's panel. Imported by local contract tests too.
"""
import contextlib
import hashlib
import ipaddress
import json
import os
import platform
import re
import secrets
import shlex
import shutil
import socket
import ssl
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import uuid
import zipfile
from pathlib import Path
from urllib.parse import urlencode, quote

VERSION = "v3.10.2"
XRAY_VERSION = "26.7.28"
DEFAULT_SNI = "www.cloudflare.com"
MIN_CLIENT_VERSION = "1.0.0"
SERVER_OS = {"id": "debian", "version_id": "12", "name": "Debian 12"}
SERVER_OS_INSTRUCTION = (
    '新购 VPS 默认选择 ' + SERVER_OS['name'] + '，DMIT、搬瓦工和 AKILE 使用同一系统规则。'
    '选系统时核对当前选中项；商家没有提供该系统时，先说明实际选项并与客户确认处理方式。'
    '首次脚本部署从服务器 /etc/os-release 读取实际系统，符合规则后继续。'
    '系统不同先处理差异；已有正常节点继续核对复用，重装需客户明确确认。')
XRAY_ARCHIVES = {
    "x86_64": ("Xray-linux-64.zip", "8195d909f1109b8f3d99eefe401a3c451d7bf4af71f24d3815420f77e5dd2a40"),
    "aarch64": ("Xray-linux-arm64-v8a.zip", "f5698bb218ada3b4022db26fafc39601c5f53b46b19eb76c9616325985807501"),
}
ARCHIVES = {
    "x86_64": ("amd64", "bfda7921984e7a72555c38d4e861c7a8b67b3686b658608937de99682f1452d0"),
    "aarch64": ("arm64", "a867c65ce52ad49f6504dd4c9c395337dc92ba57ae478da4f1b7ddb624014ed5"),
}
HOME = Path("/var/lib/claude-setup-network")
INSTALL = Path("/usr/local/x-ui")
UNIT = Path("/etc/systemd/system/x-ui.service")
FLOW = "xtls-rprx-vision"


class Failure(Exception):
    pass


class SystemMismatch(Failure):
    def __init__(self, observed):
        super().__init__('server_os_mismatch')
        self.result = {'status': 'failed', 'error': 'server_os_mismatch',
                       'operating_system': observed, 'expected_system': SERVER_OS.copy(),
                       'next_action': '当前系统是 ' + observed['name'] + '，新部署默认使用 ' + SERVER_OS['name'] +
                       '。先说明系统差异并确认处理方式；已有正常节点走复用流程，重装由客户明确确认。'}


def check_server_os(managed, path=Path('/etc/os-release')):
    values = {}
    for line in path.read_text().splitlines():
        key, separator, value = line.partition('=')
        if separator and key in ('ID', 'VERSION_ID', 'PRETTY_NAME'):
            values[key] = ''.join(shlex.split(value))
    require(values.get('ID') and values.get('VERSION_ID'), 'server_os_unavailable')
    observed = {'id': values['ID'], 'version_id': values['VERSION_ID'],
                'name': values.get('PRETTY_NAME', values['ID'] + ' ' + values['VERSION_ID'])}
    if not managed and (observed['id'], observed['version_id']) != (SERVER_OS['id'], SERVER_OS['version_id']):
        raise SystemMismatch(observed)
    return observed


def require(condition, code):
    if not condition:
        raise Failure(code)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def save(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def command(args, timeout=45):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    require(r.returncode == 0, "command_failed")
    return r.stdout


def validate(c):
    require(isinstance(c, dict), "invalid_server_config")
    c.setdefault("sni", DEFAULT_SNI)
    require(set(c) == {"address", "port", "panel_port", "sni"}, "invalid_server_fields")
    try:
        ipaddress.ip_address(c["address"])
    except (ValueError, TypeError):
        raise Failure("server_address_must_be_ip")
    for key in ("port", "panel_port"):
        require(type(c[key]) is int and 1 <= c[key] <= 65535, "invalid_port")
    require(c["port"] != c["panel_port"], "ports_collide")
    require(isinstance(c["sni"], str) and re.fullmatch(r"(?=.{1,253}$)[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*\.[A-Za-z]{2,63}", c["sni"]), "invalid_sni")
    return c


def port_free(port):
    try:
        with socket.socket() as s:
            s.bind(("0.0.0.0", port))
        return True
    except OSError:
        return False


def target_tls(sni):
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.maximum_version = ssl.TLSVersion.TLSv1_3
    with socket.create_connection((sni, 443), timeout=12) as raw:
        with ctx.wrap_socket(raw, server_hostname=sni) as tls:
            return tls.version() == "TLSv1.3"


def preflight(c):
    validate(c)
    require(platform.system() == "Linux", "linux_required")
    managed = (HOME / "receipt.json").exists()
    operating_system = check_server_os(managed)
    require(platform.machine() in ARCHIVES, "unsupported_architecture")
    require(os.geteuid() == 0, "root_or_passwordless_sudo_required")
    require(Path("/run/systemd/system").is_dir() and shutil.which("systemctl"), "systemd_required")
    require(shutil.disk_usage("/usr/local").free >= 600 * 1024 * 1024, "insufficient_disk")
    unit = subprocess.run(["systemctl", "show", "x-ui", "--property=LoadState", "--value"], capture_output=True, text=True, timeout=15)
    require(unit.returncode == 0, "systemd_query_failed")
    existing = INSTALL.exists() or Path("/etc/x-ui").exists() or UNIT.exists() or unit.stdout.strip() == "loaded"
    require(managed or not existing, "existing_panel_requires_manual_path")
    require(managed or not Path("/etc/default/x-ui").exists(), "existing_panel_environment")
    require(managed or port_free(c["port"]), "node_port_in_use")
    require(managed or port_free(c["panel_port"]), "panel_port_in_use")
    require(target_tls(c["sni"]), "target_tls13_failed")
    return {"status": "passed", "architecture": ARCHIVES[platform.machine()][0], "panel_version": VERSION,
            "operating_system": operating_system,
            "deployment_xray_version": XRAY_VERSION, "managed_install": managed,
            "target_tls13": True, "external_firewall": "unverified"}


class Panel:
    def __init__(self, receipt):
        self.base = "http://127.0.0.1:%d/%s/panel/api/" % (receipt["config"]["panel_port"], receipt["base_path"])
        self.token = receipt["token"]
        # A server-side proxy environment must never reroute panel credentials.
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def call(self, path, payload=None):
        req = urllib.request.Request(self.base + path,
            data=None if payload is None else json.dumps(payload).encode(),
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        with self.opener.open(req, timeout=15) as r:
            data = json.loads(r.read(4 * 1024 * 1024))
        require(data.get("success") is True, "panel_api_rejected")
        return data.get("obj")


def object_field(value):
    return json.loads(value) if isinstance(value, str) else value


def node_payload(c, identity, min_client_version=MIN_CLIENT_VERSION):
    payload = {
        "remark": identity["remark"], "enable": True, "port": c["port"], "listen": "0.0.0.0",
        "protocol": "vless", "total": 0, "expiryTime": 0,
        "settings": {"clients": [{"id": identity["uuid"], "email": identity["email"], "enable": True,
                                   "flow": FLOW, "subId": identity["sub_id"]}], "decryption": "none", "fallbacks": []},
        "streamSettings": {"network": "tcp", "security": "reality", "tcpSettings": {"acceptProxyProtocol": False, "header": {"type": "none"}},
            "realitySettings": {"show": False, "target": c["sni"] + ":443", "xver": 0,
                "serverNames": [c["sni"]], "privateKey": identity["private_key"], "shortIds": [identity["short_id"]],
                "settings": {"publicKey": identity["public_key"], "fingerprint": "chrome", "serverName": c["sni"], "spiderX": "/"}}},
        "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"], "routeOnly": False},
    }
    if min_client_version:
        payload["streamSettings"]["realitySettings"]["minClientVer"] = min_client_version
    return payload


def matches(actual, expected):
    """Ignore counters/timestamps, never silently repair user edits."""
    for k in ("remark", "enable", "port", "listen", "protocol", "total", "expiryTime"):
        if actual.get(k) != expected[k]:
            return False
    settings = object_field(actual["settings"])
    clients = settings.get("clients", [])
    if len(clients) != 1 or settings.get("decryption") != "none":
        return False
    if any(clients[0].get(k) != v for k, v in expected["settings"]["clients"][0].items()):
        return False
    stream = object_field(actual["streamSettings"])
    if stream.get("network") not in ("tcp", "raw") or stream.get("security") != "reality":
        return False
    reality = stream.get("realitySettings", {})
    want = expected["streamSettings"]["realitySettings"]
    if "minClientVer" in want and reality.get("minClientVer") != want["minClientVer"]:
        return False
    return all(reality.get(k) == want[k] for k in ("privateKey", "serverNames", "shortIds")) and reality.get("target", reality.get("dest")) == want["target"]


def ensure_node(panel, receipt, persist):
    if "identity" not in receipt:
        keys = panel.call("server/getNewX25519Cert")
        require(all(isinstance(keys.get(k), str) and re.fullmatch(r"[A-Za-z0-9_-]{43}", keys[k]) for k in ("privateKey", "publicKey")), "invalid_key_pair")
        receipt["identity"] = {"uuid": str(uuid.uuid4()), "email": "guide-" + secrets.token_hex(8),
            "remark": "claude-setup-" + secrets.token_hex(8), "sub_id": secrets.token_hex(16),
            "private_key": keys["privateKey"], "public_key": keys["publicKey"], "short_id": secrets.token_hex(8)}
        persist(receipt)  # Durable identity BEFORE the API mutation.
    payload = node_payload(receipt["config"], receipt["identity"], receipt.get("min_client_version"))
    existing = panel.call("inbounds/list")
    nodes = [n for n in existing if n.get("remark") == payload["remark"]]
    require(len(nodes) <= 1, "duplicate_managed_nodes")
    if nodes:
        require(matches(nodes[0], payload), "node_config_drift")
    else:
        require(not any(n.get("port") == payload["port"] for n in existing), "node_port_in_use")
        # No retry on an ambiguous POST; next invocation lists and reconciles.
        panel.call("inbounds/add", payload)
    nodes = [n for n in panel.call("inbounds/list") if n.get("remark") == payload["remark"]]
    require(len(nodes) == 1 and matches(nodes[0], payload), "node_readback_failed")
    receipt["inbound_id"] = nodes[0]["id"]
    receipt["stage"] = "node_configured"
    persist(receipt)
    return nodes[0]


def export_uri(receipt):
    c, i = receipt["config"], receipt["identity"]
    addr = "[" + c["address"] + "]" if ":" in c["address"] else c["address"]
    params = {"type": "tcp", "encryption": "none", "security": "reality", "flow": FLOW,
              "sni": c["sni"], "fp": "chrome", "pbk": i["public_key"], "sid": i["short_id"], "spx": "/"}
    return "vless://%s@%s:%d?%s#%s" % (i["uuid"], addr, c["port"], urlencode(params), quote(i["remark"]))


def xray_binary(installation=None):
    return (installation or INSTALL) / "bin" / ("xray-linux-" + ARCHIVES[platform.machine()][0])


def xray_version(binary):
    return command([str(binary), "version"]).splitlines()[0].split()[1]


def install_xray(installation):
    name, checksum = XRAY_ARCHIVES[platform.machine()]
    with tempfile.TemporaryDirectory(dir=str(HOME)) as tmp:
        archive = Path(tmp) / name
        url = "https://github.com/XTLS/Xray-core/releases/download/v%s/%s" % (XRAY_VERSION, name)
        with urllib.request.urlopen(url, timeout=60) as src, archive.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        require(hashlib.sha256(archive.read_bytes()).hexdigest() == checksum, "xray_checksum_mismatch")
        binary = xray_binary(installation)
        with zipfile.ZipFile(archive) as bundle:
            binary.write_bytes(bundle.read("xray"))
        binary.chmod(0o755)
        require(xray_version(binary) == XRAY_VERSION, "xray_version_mismatch")


def install_archive():
    arch, checksum = ARCHIVES[platform.machine()]
    with tempfile.TemporaryDirectory(dir=str(HOME)) as tmp:
        archive = Path(tmp) / "release.tar.gz"
        url = "https://github.com/MHSanaei/3x-ui/releases/download/%s/x-ui-linux-%s.tar.gz" % (VERSION, arch)
        with urllib.request.urlopen(url, timeout=60) as src, archive.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        require(hashlib.sha256(archive.read_bytes()).hexdigest() == checksum, "archive_checksum_mismatch")
        with tarfile.open(archive) as tar:
            for m in tar.getmembers():
                require(not m.name.startswith("/") and ".." not in Path(m.name).parts and (m.isfile() or m.isdir()), "unsafe_archive")
            tar.extractall(tmp)
        # Staging on the destination filesystem allows an atomic rename.
        stage = INSTALL.with_name(".claude-setup-x-ui-stage")
        require(not stage.exists(), "staging_directory_requires_inspection")
        try:
            shutil.copytree(Path(tmp) / "x-ui", stage)
            # Assemble the delivery bundle before installing or starting the panel.
            install_xray(stage)
            stage.rename(INSTALL)
        finally:
            if stage.exists():
                shutil.rmtree(stage)


def configure_panel(receipt):
    c = receipt["config"]
    command([str(INSTALL / "x-ui"), "setting", "-username", receipt["username"], "-password", receipt["password"],
             "-port", str(c["panel_port"]), "-webBasePath", "/" + receipt["base_path"] + "/", "-listenIP", "127.0.0.1"])
    if "token" not in receipt:
        out = command([str(INSTALL / "x-ui"), "setting", "-getApiToken", "-tokenName", "claude-setup", "-tokenScope", "admin"])
        match = re.search(r"^apiToken: (\S+)$", out, re.M)
        require(match, "token_creation_failed")
        receipt["token"] = match.group(1)
    # The pinned CLI has no subEnable flag. Change only these settings in our
    # freshly initialized database, before starting the panel; never on an
    # adopted/existing installation. Its default subscription listener is public.
    database = Path("/etc/x-ui/x-ui.db")
    require(database.is_file(), "panel_database_missing")
    with sqlite3.connect(str(database)) as db:
        for key in ("subEnable", "subJsonEnable", "subClashEnable"):
            rows = db.execute("SELECT id FROM settings WHERE key = ?", (key,)).fetchall()
            if rows:
                db.execute("UPDATE settings SET value = 'false' WHERE key = ?", (key,))
            else:
                db.execute("INSERT INTO settings (key, value) VALUES (?, 'false')", (key,))


def panel_listen_verified(port):
    """Read real Linux listener addresses, not merely CLI exit status."""
    listeners = []
    for name in ("tcp", "tcp6"):
        for line in Path("/proc/net/" + name).read_text().splitlines()[1:]:
            fields = line.split()
            address, number = fields[1].split(":")
            if fields[3] == "0A" and int(number, 16) == port:
                listeners.append((name, address))
    require(listeners == [("tcp", "0100007F")], "panel_not_loopback_only")


def wait_panel(receipt):
    panel = Panel(receipt)
    for _ in range(20):
        try:
            panel.call("inbounds/list")
            return panel
        except Exception:
            time.sleep(0.5)
    raise Failure("panel_not_ready")


def deploy(c):
    checked = preflight(c)
    HOME.mkdir(mode=0o700, parents=True, exist_ok=True)
    import fcntl
    with (HOME / "lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Failure("deployment_busy")
        path = HOME / "receipt.json"
        persist = lambda r: save(path, r)
        if path.exists():
            receipt = json.loads(path.read_text())
            require(receipt["config"] == c and receipt["version"] == VERSION, "managed_config_changed")
        else:
            # Repeat the read-only checks under the deployment lock.
            preflight(c)
            receipt = {"version": VERSION, "xray_version": XRAY_VERSION, "min_client_version": MIN_CLIENT_VERSION,
                       "config": c, "stage": "prepared", "username": "guide-" + secrets.token_hex(4),
                       "password": secrets.token_urlsafe(32), "base_path": secrets.token_hex(16)}
            persist(receipt)
        if not INSTALL.exists():
            install_archive()
        require(command([str(INSTALL / "x-ui"), "-v"]).strip().lstrip("v") == VERSION.lstrip("v"), "panel_version_changed")
        if receipt.get("xray_version"):
            require(xray_version(xray_binary()) == receipt["xray_version"], "xray_version_changed")
        if receipt["stage"] == "prepared":
            configure_panel(receipt)
            receipt["stage"] = "panel_configured"
            persist(receipt)
        if receipt["stage"] == "panel_configured":
            UNIT.write_text("[Unit]\nDescription=3x-ui (claude-setup managed)\nAfter=network-online.target\nWants=network-online.target\n\n[Service]\nType=simple\nWorkingDirectory=/usr/local/x-ui\nExecStart=/usr/local/x-ui/x-ui\nRestart=on-failure\nRestartSec=5\nUMask=0077\n\n[Install]\nWantedBy=multi-user.target\n")
            command(["systemctl", "daemon-reload"])
            command(["systemctl", "enable", "--now", "x-ui"])
            receipt["stage"] = "panel_ready"
            persist(receipt)
        else:
            # Resume our managed installation using its current service state.
            active = subprocess.run(['systemctl', 'is-active', 'x-ui'], capture_output=True, text=True, timeout=15)
            if active.returncode != 0 or active.stdout.strip() != 'active':
                command(['systemctl', 'start', 'x-ui'])
        panel = wait_panel(receipt)
        panel_listen_verified(c["panel_port"])
        ensure_node(panel, receipt, persist)
        return {"status": "configured", "panel_version": VERSION, "client_route": "unverified",
                "operating_system": checked['operating_system']}


def verify(c):
    path = HOME / "receipt.json"
    require(path.exists(), "no_managed_install")
    receipt = json.loads(path.read_text())
    require(receipt["config"] == c and receipt["version"] == VERSION, "managed_config_changed")
    require("identity" in receipt, "node_not_configured")
    require(command([str(INSTALL / "x-ui"), "-v"]).strip().lstrip("v") == VERSION.lstrip("v"), "panel_version_changed")
    require(command(["systemctl", "is-active", "x-ui"]).strip() == "active", "panel_not_active")
    panel = Panel(receipt)
    panel_listen_verified(c["panel_port"])
    nodes = [n for n in panel.call("inbounds/list") if n.get("remark") == receipt["identity"]["remark"]]
    require(len(nodes) == 1 and matches(nodes[0], node_payload(c, receipt["identity"], receipt.get("min_client_version"))), "node_readback_failed")
    status = panel.call("server/status")
    require(status.get("xray", {}).get("state") == "running", "xray_not_running")
    if receipt.get("xray_version"):
        require(status["xray"].get("version") == receipt["xray_version"], "xray_version_changed")
    with socket.create_connection(("127.0.0.1", c["port"]), timeout=5):
        pass
    return {"status": "passed", "panel_version": VERSION, "xray_version": status["xray"].get("version"),
            "client_route": "unverified", "uri": export_uri(receipt),
            "panel": {"port": c["panel_port"], "base_path": receipt["base_path"],
                      "username": receipt["username"], "password": receipt["password"]}}


def main():
    try:
        request = json.load(sys.stdin)
        action, c = request["action"], validate(request["server"])
        require(action in ("preflight", "deploy", "verify"), "invalid_action")
        result = {"preflight": preflight, "deploy": deploy, "verify": verify}[action](c)
        print(json.dumps(result))
    except Exception as e:
        # Never echo response bodies, subprocess arguments or credentials.
        print(json.dumps(e.result if isinstance(e, SystemMismatch) else
                         {"status": "failed", "error": str(e) if isinstance(e, Failure) else type(e).__name__}))
        sys.exit(1)


if __name__ == "__main__":
    main()
