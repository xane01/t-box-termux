"""Command routing for built-in commands and modules."""
import argparse
import json
import runpy
import sys
from pathlib import Path
from .registry import discover_modules
from .config_manager import load_config, set_value
from .paths import ensure_dirs, CONFIG_FILE, DATA_DIR
from .diagnostics import run_doctor

BANNER = r"""
 _____        ____   ____  __
|_   _|      | __ ) / ___| \ \
  | |   _____|  _ \| |      \ \
  | |  |_____| |_) | |___   / /
  |_|        |____/ \____| /_/
        TERMUX TOOLBOX
"""

def print_banner():
    print("\033[1;32m" + BANNER + "\033[0m")
    print(" Modular command-line toolkit for Termux\n")

def cmd_list(_args=None):
    modules = discover_modules()
    print("Available modules:")
    for key, item in sorted(modules.items()):
        print("  {:<16} {} [{}]".format(key, item.get("name", key), item.get("category", "general")))
    if not modules:
        print("  No modules found.")

def cmd_info(_args=None):
    root = Path(__file__).resolve().parents[1]
    version_file = root / "VERSION"
    version = version_file.read_text().strip() if version_file.exists() else "unknown"
    print("T-BOX version :", version)
    print("Python        :", sys.version.split()[0])
    print("Platform      :", sys.platform)
    print("Config        :", CONFIG_FILE)
    print("Data          :", DATA_DIR)
    print("Modules       :", len(discover_modules()))

def cmd_doctor(_args=None):
    results = run_doctor()
    failed = False
    print("T-BOX Doctor")
    for label, ok, detail in results:
        print("[{}] {} — {}".format("OK" if ok else "WARN", label, detail))
        failed = failed or not ok
    return 1 if failed else 0

def cmd_config(args):
    cfg = load_config()
    if args.config_action == "show":
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
    elif args.config_action == "set":
        try:
            set_value(args.key, args.value)
            print("Updated {}.".format(args.key))
        except KeyError as exc:
            print(exc)
            return 2
    return 0

def cmd_run(args):
    modules = discover_modules()
    item = modules.get(args.module_id)
    if not item:
        print("Unknown module: {}".format(args.module_id))
        print("Run 'tbox list' to see available modules.")
        return 2
    script = item["_script"]
    sys.argv = [str(script)] + args.module_args
    runpy.run_path(str(script), run_name="__main__")
    return 0

def interactive_menu():
    while True:
        print_banner()
        print("  [1] List modules")
        print("  [2] System information")
        print("  [3] Run diagnostics")
        print("  [4] Configuration")
        print("  [5] Help")
        print("  [0] Exit")
        choice = input("\nT-BOX > ").strip()
        if choice == "1":
            cmd_list()
        elif choice == "2":
            cmd_info()
        elif choice == "3":
            cmd_doctor()
        elif choice == "4":
            print(json.dumps(load_config(), indent=2))
        elif choice == "5":
            print("Commands: tbox, tbox list, tbox info, tbox doctor, tbox run MODULE [ARGS]")
        elif choice == "0":
            print("Goodbye.")
            return 0
        else:
            print("Invalid choice.")
        input("\nPress Enter to continue...")

def main(argv=None):
    ensure_dirs()
    parser = argparse.ArgumentParser(prog="tbox", description="T-BOX Termux Toolbox")
    parser.add_argument("--version", action="version", version="T-BOX 0.1.0")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("list", help="List available modules")
    sub.add_parser("info", help="Show T-BOX information")
    sub.add_parser("doctor", help="Check environment and installation")
    runp = sub.add_parser("run", help="Run a module")
    runp.add_argument("module_id")
    runp.add_argument("module_args", nargs=argparse.REMAINDER)
    cp = sub.add_parser("config", help="Manage configuration")
    cps = cp.add_subparsers(dest="config_action", required=True)
    cps.add_parser("show")
    setp = cps.add_parser("set")
    setp.add_argument("key")
    setp.add_argument("value")
    args = parser.parse_args(argv)
    if not args.command:
        return interactive_menu()
    if args.command == "list": return cmd_list(args)
    if args.command == "info": return cmd_info(args)
    if args.command == "doctor": return cmd_doctor(args)
    if args.command == "run": return cmd_run(args)
    if args.command == "config": return cmd_config(args)
    return 0
