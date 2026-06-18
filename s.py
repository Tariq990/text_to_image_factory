import subprocess, sys, os
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
