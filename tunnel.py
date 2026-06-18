#!/usr/bin/env python3
import subprocess, sys, os, re, threading, time, urllib.request, shutil, platform

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 7860
BINARY = "cloudflared"

def is_installed():
    return shutil.which(BINARY) is not None

def install():
    print("Installing cloudflared...")
    arch = platform.machine()
    if "aarch64" in arch or "arm64" in arch:
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
    else:
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    subprocess.run(["wget", "-q", url, "-O", f"/usr/local/bin/{BINARY}"], check=True)
    subprocess.run(["chmod", "+x", f"/usr/local/bin/{BINARY}"], check=True)
    print("cloudflared installed")

def run_tunnel():
    proc = subprocess.Popen(
        [BINARY, "tunnel", "--url", f"http://127.0.0.1:{PORT}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        universal_newlines=True, bufsize=1
    )
    url_found = False
    for line in iter(proc.stdout.readline, ''):
        print(line, end='')
        sys.stdout.flush()
        if not url_found:
            m = re.search(r'https://[a-zA-Z0-9_-]+\.trycloudflare\.com', line)
            if m:
                url_found = True
                print(f"\n{'='*60}")
                print(f"  PUBLIC URL: {m.group(0)}")
                print(f"{'='*60}\n")
    proc.wait()

if not is_installed():
    install()
print(f"Connecting tunnel to http://127.0.0.1:{PORT} ...")
run_tunnel()
