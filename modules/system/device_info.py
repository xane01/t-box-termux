import os, platform, shutil, subprocess

def main():
    print("Device / Runtime Information")
    print("Platform :", platform.platform())
    print("Machine  :", platform.machine())
    print("Python   :", platform.python_version())
    print("Termux   :", os.environ.get("PREFIX", "not detected"))
    for cmd, label in [("uname", "Kernel"), ("df", "Storage")]:
        path = shutil.which(cmd)
        if not path: continue
        try:
            args = [path, "-a"] if cmd == "uname" else [path, "-h", "."]
            result = subprocess.run(args, capture_output=True, text=True, timeout=5, check=False)
            print("\n{}:\n{}".format(label, result.stdout.strip()))
        except (OSError, subprocess.TimeoutExpired) as exc:
            print("{}: {}".format(label, exc))

if __name__ == "__main__": main()
