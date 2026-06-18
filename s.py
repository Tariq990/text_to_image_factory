import subprocess, sys, os, urllib.request

MODE = sys.argv[1] if len(sys.argv) > 1 else "smoke"

if MODE == "tunnel":
    port = sys.argv[2] if len(sys.argv) > 2 else "7860"
    url = "https://raw.githubusercontent.com/Tariq990/text_to_image_factory/master/tunnel.py"
    data = urllib.request.urlopen(url).read()
    with open("/content/tunnel.py", "wb") as f:
        f.write(data)
    subprocess.run([sys.executable, "/content/tunnel.py", port])
    sys.exit(0)

os.chdir("/content")
subprocess.run(["rm", "-rf", "/content/t2f"])
r = subprocess.run(["git", "clone", "--depth", "1",
    "https://github.com/Tariq990/text_to_image_factory.git",
    "/content/t2f"], capture_output=True)
if r.returncode != 0:
    print(f"Clone failed: {r.stderr.decode()}")
    sys.exit(1)
os.chdir("/content/t2f")
r = subprocess.run([sys.executable, "app.py",
    "--mode", "single",
    "--width", "768",
    "--height", "768",
    "--seed", "42",
    "--prompt", "A cat sitting on a stack of ancient books, cinematic lighting",
    "--style", "cinematic realistic"])
if r.returncode != 0:
    print(f"Smoke test failed with code {r.returncode}")
else:
    print("Smoke test complete!")
