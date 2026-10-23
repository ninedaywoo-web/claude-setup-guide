#!/usr/bin/env python3
"""Deterministic execution receipts, SSH deployment and explicit-route probes.

Python 3.9+, stdlib + native ssh/curl. Does not switch VPNs or operate UI.
"""
import argparse
import base64
import contextlib
import datetime
import ipaddress
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

from network_server import Failure, require, save, digest, validate

ROOT = Path(__file__).resolve().parents[1]
EXIT_URLS = ("https://api.ipify.org", "https://ipv4.icanhazip.com")
HTTPS_URL = "https://www.gstatic.com/generate_204"
SITES = {"netcoffee": "https://ip.net.coffee/claude/", "ping0": "https://ping0.cc/", "scamalytics": "https://scamalytics.com/ip"}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def private_file(path, text):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


@contextlib.contextmanager
def lock(folder):
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (folder / "execution.lock").open("a+b") as f:
        if os.name == "nt":
            import msvcrt
            f.seek(0); f.write(b"0"); f.flush(); f.seek(0)
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                raise Failure("execution_busy")
        else:
            import fcntl
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Failure("execution_busy")
        try:
            yield
        finally:
            if os.name == "nt":
                f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


def config(path):
    c = read_json(path)
    require(isinstance(c, dict) and set(c) <= {"server", "ssh", "probe", "context"}, "invalid_config_fields")
    require(isinstance(c.get("context"), str) and bool(c["context"].strip()), "context_required")
    if "server" in c:
        validate(c["server"])
    if "ssh" in c:
        s = c["ssh"]
        require(set(s) <= {"host", "user", "port", "identity_file", "sudo", "batch_mode"}, "invalid_ssh_fields")
        require(isinstance(s.get("host"), str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.:-]*", s["host"]), "invalid_ssh_host")
        require(isinstance(s.get("user"), str) and re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_-]*", s["user"]), "invalid_ssh_user")
        require(type(s.get("port", 22)) is int and 1 <= s.get("port", 22) <= 65535, "invalid_ssh_port")
        for k in ("sudo", "batch_mode"):
            require(k not in s or type(s[k]) is bool, "invalid_ssh_flag")
    if "probe" in c:
        p = c["probe"]
        require(set(p) == {"proxy", "expected_exit_ipv4"}, "invalid_probe_fields")
        try:
            require(ipaddress.ip_address(p["expected_exit_ipv4"]).version == 4, "expected_ipv4_required")
            u = urlsplit(p["proxy"])
            require(u.scheme == "http" and u.hostname in ("127.0.0.1", "localhost", "::1") and u.port and not u.username and not u.password and not u.path and not u.query and not u.fragment, "local_http_proxy_required")
        except (ValueError, TypeError):
            raise Failure("invalid_probe_config")
    return c


class State:
    def __init__(self, root, configuration):
        self.folder = root / ".local/network"
        self.path = self.folder / "state.json"
        self.root = root
        self.data = read_json(self.path) if self.path.exists() else {"schema": 1, "steps": {}, "generation": 0}
        require(self.data.get("schema") == 1, "unsupported_state_schema")
        current = digest(configuration)
        if self.data.get("context_hash") != current:
            self.invalidate()
            self.data["context_hash"] = current
        # A previous running operation is uncertain, never assumed successful.
        for step in self.data["steps"].values():
            if step["status"] == "running":
                step["status"] = "interrupted"
        self.persist()

    def persist(self):
        save(self.path, self.data)

    def invalidate(self):
        for step in self.data["steps"].values():
            step["status"] = "stale"
        self.data["generation"] += 1
        self.persist()

    def begin(self, step):
        # A new deployment attempt makes old export/route evidence stale.
        if step == "deploy":
            self.invalidate()
        self.data["steps"][step] = {"status": "running", "at": now()}
        self.persist()

    def finish(self, step, result):
        self.data["steps"][step] = {"status": result["status"], "at": now(), "result": result}
        self.persist()

    def report(self):
        return {"status": "recorded", "generation": self.data["generation"], "steps": self.data["steps"],
                "scope": "script_execution", "other_checks_record": ".local/progress.md"}

    def write_report(self):
        report = self.report()
        save(self.folder / "report.json", report)
        # Add only a link; never recreate or rewrite the user's progress text.
        progress = self.root / ".local/progress.md"
        marker = "<!-- network-execution-report -->"
        text = progress.read_text(encoding="utf-8") if progress.exists() else ""
        if marker not in text:
            private_file(progress, text + "\n\n" + marker + "\n脚本执行结果见 [网络执行记录](network/report.json)。VPN 交接、浏览器、手机和账号结果继续记在本进度文件。\n")
        return report


def remote(action, c):
    require("server" in c and "ssh" in c, "server_and_ssh_required")
    require(shutil.which("ssh"), "ssh_missing")
    s = c["ssh"]
    payload = base64.b64encode((ROOT / "scripts/network_server.py").read_bytes()).decode()
    code = "import base64;exec(compile(base64.b64decode('%s'),'network_server.py','exec'))" % payload
    remote_cmd = (["sudo", "-n"] if s.get("sudo") else []) + ["python3", "-c", code]
    args = ["ssh", "-T", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=12", "-o", "ServerAliveInterval=15",
            "-o", "ServerAliveCountMax=2", "-o", "BatchMode=" + ("yes" if s.get("batch_mode", True) else "no"), "-p", str(s.get("port", 22))]
    if s.get("identity_file"):
        args += ["-i", str(Path(s["identity_file"]).expanduser())]
    args += [s["user"] + "@" + s["host"], shlex.join(remote_cmd)]
    r = subprocess.run(args, input=json.dumps({"action": action, "server": c["server"]}), capture_output=True, text=True,
                       timeout=420 if action == "deploy" else 70)
    try:
        data = json.loads(r.stdout)
    except ValueError:
        raise Failure("ssh_or_remote_protocol_failed")
    if r.returncode != 0 or data.get("status") == "failed":
        # Only the helper's bounded error codes may be shown to users.
        code = data.get("error", "remote_failed")
        raise Failure(code if re.fullmatch(r"[A-Za-z0-9_]{1,80}", code) else "remote_failed")
    return data


def curl_request(url, proxy, timeout=15):
    curl = shutil.which("curl.exe" if os.name == "nt" else "curl")
    require(curl, "curl_missing")
    env = {k: v for k, v in os.environ.items() if k.lower() not in ("http_proxy", "https_proxy", "all_proxy", "no_proxy")}
    with tempfile.TemporaryDirectory() as tmp:
        body_path = Path(tmp) / "body"
        args = [curl, "--disable", "--silent", "--show-error", "--ipv4", "--connect-timeout", str(min(timeout, 8)),
                "--max-time", str(timeout), "--max-filesize", "4096", "--proxy", proxy or "", "--noproxy", "" if proxy else "*",
                "--output", str(body_path), "--write-out", "%{http_code}", "--url", url]
        try:
            r = subprocess.run(args, capture_output=True, text=True, env=env, timeout=timeout + 3)
        except subprocess.TimeoutExpired:
            return {"code": 0, "transport": "timeout", "body": ""}
        status = int(r.stdout) if r.stdout.strip().isdigit() else 0
        body = body_path.read_bytes()[:4096].decode("utf-8", errors="replace") if body_path.exists() else ""
        return {"code": status, "transport": "ok" if r.returncode == 0 else "curl_%d" % r.returncode, "body": body}


def probe(c, route, request=curl_request):
    require("probe" in c, "probe_config_required")
    proxy = c["probe"]["proxy"] if route == "proxy" else None
    observations, exits = [], []
    for url in EXIT_URLS:
        r = request(url, proxy)
        valid = False
        if r["transport"] == "ok" and r["code"] == 200:
            try:
                value = ipaddress.ip_address(r["body"].strip())
                valid = value.version == 4
                if valid:
                    exits.append(str(value))
            except ValueError:
                pass
        observations.append({"service": urlsplit(url).hostname, "http_status": r["code"], "transport": r["transport"], "valid_ipv4": valid})
    https = request(HTTPS_URL, proxy)
    match = bool(exits) and all(x == c["probe"]["expected_exit_ipv4"] for x in exits)
    reachable = https["transport"] == "ok" and https["code"] == 204 and not https["body"].strip()
    return {"status": "passed" if match and reachable else "failed", "route": route, "exit_matches": match,
            "exit_sources": observations, "https_204": reachable, "https_status": https["code"],
            "scope": "ipv4_requests_only", "vpn_handoff": "unverified"}


def scores(data, expected_context):
    require(isinstance(data, dict) and set(data) == {"context", "environment", "observed_at", "exit_matches", "scores"}, "invalid_score_fields")
    require(data["context"] == expected_context, "score_context_mismatch")
    require(data["environment"] in ("adspower", "iphone_wifi", "iphone_cellular", "android_wifi", "android_cellular"), "invalid_score_environment")
    at = datetime.datetime.fromisoformat(data["observed_at"])
    require(at.tzinfo is not None, "score_timezone_required")
    age = (datetime.datetime.now(datetime.timezone.utc) - at).total_seconds()
    require(age >= -300, "score_observation_in_future")
    require(type(data["exit_matches"]) is bool, "invalid_exit_observation")
    require(set(data["scores"]) == set(SITES), "three_score_sites_required")
    results = {}
    for name, obj in data["scores"].items():
        require(isinstance(obj, dict) and set(obj) == {"value", "evidence"}, "score_evidence_required")
        value = obj["value"]
        require(value is None or (type(value) in (int, float) and 0 <= value <= 100), "invalid_score_value")
        require(isinstance(obj["evidence"], str) and (value is None or bool(obj["evidence"].strip())), "score_evidence_required")
        # Explicitly a local workflow tolerance, not a validated account-risk model.
        band = "unverified"
        if value is not None:
            ideal = value >= 80 if name == "netcoffee" else value < (30 if name == "ping0" else 10)
            close = value >= 75 if name == "netcoffee" else value <= (35 if name == "ping0" else 15)
            band = "reference_met" if ideal else "near_reference" if close else "recheck_recommended"
        results[name] = {"value": value, "assessment": band, "site": SITES[name]}
    return {"status": "recorded", "environment": data["environment"], "observed_at": data["observed_at"],
            "exit_matches": data["exit_matches"], "scores": results, "advisory_only": True,
            "freshness": "recheck_recommended" if age > 86400 else "recent"}


def execute(args, c, state):
    action = args.action
    step = action + ("_" + args.route if action == "probe" else "")
    if action == "status":
        return state.write_report()
    if action == "invalidate":
        state.invalidate()
        return state.write_report()
    state.begin(step)
    try:
        if action in ("preflight", "deploy", "export"):
            if action == "deploy":
                remote("deploy", c)
            if action == "preflight":
                result = remote("preflight", c)
            else:
                # New SSH connection after mutation; never equate the POST with success.
                verified = remote("verify", c)
                private_file(state.folder / "node.txt", verified.pop("uri") + "\n")
                save(state.folder / "panel-private.json", verified.pop("panel"))
                result = verified
                result["status"] = "configured" if action == "deploy" else "exported"
                result["node_file"] = ".local/network/node.txt"
        elif action == "probe":
            result = probe(c, args.route)
        elif action == "scores":
            require(args.input, "scores_input_required")
            source = Path(args.input).resolve()
            require(state.root / ".local" in source.parents, "scores_input_must_be_private")
            data = read_json(source)
            environment = data.get("environment") if isinstance(data, dict) else None
            if environment in ("adspower", "iphone_wifi", "iphone_cellular", "android_wifi", "android_cellular"):
                step = "scores_" + environment
                state.begin(step)
                state.data["steps"].pop("scores", None)
            result = scores(data, c["context"])
            # Keep raw evidence private, report only allowlisted assessment fields.
            save(state.folder / ("scores-" + result["environment"] + ".json"), data)
            step = "scores_" + result["environment"]
            state.data["steps"].pop("scores", None)
        else:
            raise Failure("unsupported_action")
        state.finish(step, result)
        state.write_report()
        return result
    except (Exception, KeyboardInterrupt) as e:
        result = {"status": "interrupted" if isinstance(e, KeyboardInterrupt) else "failed",
                  "error": str(e) if isinstance(e, Failure) else type(e).__name__}
        state.finish(step, result)
        state.write_report()
        return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("preflight", "deploy", "export", "probe", "scores", "status", "invalidate"))
    p.add_argument("--config", default=str(ROOT / ".local/network/input.json"))
    p.add_argument("--route", choices=("proxy", "system"), default="proxy")
    p.add_argument("--input", help="Private JSON containing actual browser observations")
    args = p.parse_args()
    try:
        if args.action not in ('status', 'invalidate'):
            from workflow_guard import check
            operation = 'network:' + args.action
            if args.action == 'probe':
                operation += ':' + args.route
            try:
                check(ROOT, operation)
            except ValueError as exc:
                raise Failure(str(exc))
        source = Path(args.config).resolve()
        require(ROOT / ".local" in source.parents, "config_must_be_private")
        c = config(source)
        with lock(ROOT / ".local/network"):
            state = State(ROOT, c)
            result = execute(args, c, state)
    except Exception as e:
        result = {"status": "failed", "error": str(e) if isinstance(e, Failure) else type(e).__name__}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] in ("failed", "interrupted") else 0


if __name__ == "__main__":
    sys.exit(main())
