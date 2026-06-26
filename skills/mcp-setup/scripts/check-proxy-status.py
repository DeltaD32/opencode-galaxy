#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "psutil>=5.9.0",
# ]
# ///
"""
Proxy Configuration Status Check Script
This script checks the current proxy configuration and outputs JSON for AI parsing

Cross-platform compatible: Linux, macOS, Windows
Uses psutil for reliable cross-platform process and port detection

Usage: uv run scripts/check-proxy-status.py
"""

import json
import os
import platform
import re
import subprocess
import sys
from typing import Dict

import psutil  # type: ignore


def check_proxydetox_status() -> Dict[str, str]:
    """Check if Proxydetox service is running."""
    status = "not_running"
    manager = "none"

    os_type = platform.system()

    # Check systemd user service (Linux only)
    if os_type == "Linux":
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", "proxydetox"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                status = "running"
                manager = "systemd"
                return {"status": status, "manager": manager}
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    # Check if running as standalone process (cross-platform)
    try:
        for proc in psutil.process_iter(["name", "cmdline"]):
            try:
                if proc.info["name"] and "proxydetox" in proc.info["name"].lower():
                    status = "running"
                    manager = "standalone"
                    break
                if proc.info["cmdline"]:
                    cmdline = " ".join(proc.info["cmdline"])
                    if "proxydetox" in cmdline.lower():
                        status = "running"
                        manager = "standalone"
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):  # type: ignore
                continue
    except ImportError:
        # Fallback to platform-specific commands if psutil not available
        try:
            if os_type == "Windows":
                result = subprocess.run(["tasklist"], capture_output=True, text=True, timeout=2)
            else:
                result = subprocess.run(
                    ["ps", "aux"] if os_type != "Darwin" else ["ps", "-ax"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
            if "proxydetox" in result.stdout.lower():
                status = "running"
                manager = "standalone"
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    return {"status": status, "manager": manager}


def test_port(port: int) -> str:
    """Test if a port is accessible."""
    try:
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("localhost", port))
        sock.close()
        return "ok" if result == 0 else "failed"
    except Exception:
        return "failed"


def check_port_listeners(port: int) -> int:
    """Check how many listeners are on a port."""
    import platform

    os_type = platform.system()

    # Try psutil first (most reliable cross-platform method)
    try:
        import psutil  # type: ignore

        count = 0
        for conn in psutil.net_connections(kind="inet"):
            if conn.status == "LISTEN" and hasattr(conn.laddr, "port") and conn.laddr.port == port:  # type: ignore
                count += 1
        return count
    except ImportError:
        pass
    except (PermissionError, Exception):
        # psutil may need elevated permissions on some systems
        # Catch generic Exception to handle psutil.AccessDenied when psutil is available
        pass

    # Fallback to OS-specific commands
    try:
        if os_type == "Windows":
            result = subprocess.run(["netstat", "-an"], capture_output=True, text=True, timeout=2)
            count = 0
            for line in result.stdout.split("\n"):
                if f":{port}" in line and "LISTENING" in line:
                    count += 1
            return count
        elif os_type == "Darwin":  # macOS
            result = subprocess.run(
                ["lsof", "-i", f":{port}"], capture_output=True, text=True, timeout=2
            )
            count = result.stdout.count("LISTEN")
            return count
        else:  # Linux
            result = subprocess.run(
                ["ss", "-ln", f"sport = :{port}"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode != 0:
                # Fallback to lsof if ss not available
                result = subprocess.run(
                    ["lsof", "-i", f":{port}"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                count = result.stdout.count("LISTEN")
            else:
                count = result.stdout.count("LISTEN")
            return count
    except (subprocess.SubprocessError, FileNotFoundError):
        return 0


def test_proxy_connectivity() -> str:
    """Test proxy connectivity using curl or native Python."""
    import shutil

    # Try curl if available (cross-platform)
    curl_path = shutil.which("curl")
    if curl_path:
        try:
            result = subprocess.run(
                [
                    curl_path,
                    "-s",
                    "--max-time",
                    "5",
                    "-x",
                    "http://127.0.0.1:3128",
                    "http://example.com",
                ],
                capture_output=True,
                timeout=6,
            )
            return "passed" if result.returncode == 0 else "failed"
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    # Fallback to Python urllib (cross-platform)
    try:
        import urllib.request

        proxy_handler = urllib.request.ProxyHandler({"http": "http://127.0.0.1:3128"})
        opener = urllib.request.build_opener(proxy_handler)
        opener.addheaders = [("User-agent", "Mozilla/5.0")]
        urllib.request.install_opener(opener)
        with urllib.request.urlopen("http://example.com", timeout=5) as response:
            return "passed" if response.status == 200 else "failed"
    except Exception:
        return "failed"


def extract_port_from_proxy(proxy_url: str) -> str:
    """Extract port number from proxy URL."""
    match = re.search(r":(\d+)", proxy_url)
    return match.group(1) if match else ""


def check_configured_port(port_str: str) -> str:
    """Check if configured port is listening."""
    if not port_str:
        return "not_set"

    try:
        port = int(port_str)
        listeners = check_port_listeners(port)
        return "listening" if listeners > 0 else "not_listening"
    except ValueError:
        return "not_set"


def get_os_type() -> str:
    """Get operating system type."""
    import platform

    return platform.system()


def main():
    # Get environment variables
    http_proxy = os.environ.get("HTTP_PROXY", "")
    https_proxy = os.environ.get("HTTPS_PROXY", "")
    no_proxy = os.environ.get("NO_PROXY", "")

    # Check Proxydetox status
    proxydetox = check_proxydetox_status()

    # Test port 3128
    port_3128_test = test_port(3128)
    port_3128_listeners = check_port_listeners(3128)
    proxy_connectivity = test_proxy_connectivity()

    # Extract and check configured port
    configured_port = extract_port_from_proxy(http_proxy)
    configured_port_status = check_configured_port(configured_port)

    # Get OS type
    os_type = get_os_type()

    # Build result JSON
    result = {
        "environment": {
            "HTTP_PROXY": http_proxy,
            "HTTPS_PROXY": https_proxy,
            "NO_PROXY": no_proxy,
        },
        "proxydetox": proxydetox,
        "ports": {
            "standard_3128": {
                "test": port_3128_test,
                "listeners": port_3128_listeners,
                "connectivity": proxy_connectivity,
            },
            "configured": {"port": configured_port, "status": configured_port_status},
        },
        "system": {"os": os_type},
    }

    # Output JSON
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
