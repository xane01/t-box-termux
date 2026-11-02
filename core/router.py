"""Command routing for T-BOX commands and modules."""
import argparse
import json
import runpy
import sys
from pathlib import Path

from .registry import discover_modules
from .config_manager import load_config, set_value
from .paths import ensure_dirs, CONFIG_FILE, DATA_DIR
from .diagnostics import run_doctor
from . import package_manager as pm

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
        source = " [plugin]" if (Path(item.get("_directory", "")).parent == pm.PLUGIN_DIR) else ""
        print("  {:<16} {} [{}]{}".format(key, item.get("name", key),
              item.get("category", "general"), source))
    if not modules:
        print("  No modules found.")
    return 0


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
    return 0


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
    item = discover_modules().get(args.module_id)
    if not item:
        print("Unknown module: {}".format(args.module_id))
        print("Run 'tbox list' to see available modules.")
        return 2
    script = item["_script"]
    sys.argv = [str(script)] + args.module_args
    runpy.run_path(str(script), run_name="__main__")
    return 0


def cmd_repo(args):
    try:
        if args.repo_action == "list":
            repos = pm.list_repositories()
            if not repos:
                print("No repositories configured.")
            for name, url in sorted(repos.items()):
                print("{}  {}".format(name, url))
        elif args.repo_action == "add":
            count = pm.add_repository(args.name, args.index_url)
            print("Repository '{}' added ({} indexed entries).".format(args.name, count))
        elif args.repo_action == "remove":
            pm.remove_repository(args.name)
            print("Repository '{}' removed.".format(args.name))
        return 0
    except pm.PackageError as exc:
        print("Package manager:", exc)
        return 2


def cmd_package(args):
    try:
        if args.package_action == "search":
            results = pm.search_modules(args.query or "")
            if not results:
                print("No matching modules.")
            for item in results:
                print("{:<18} {:<12} {} (repo: {})".format(
                    item["id"], item.get("version", "?"),
                    item.get("description", item.get("name", "")),
                    item.get("_repository", "?")))
        elif args.package_action == "install":
            item = pm.install_module(args.module_id)
            print("Installed {} {}.".format(item["id"], item["version"]))
            print("Review plugin code before running it: tbox run {}".format(item["id"]))
        elif args.package_action == "remove":
            pm.remove_module(args.module_id)
            print("Removed plugin '{}'.".format(args.module_id))
        elif args.package_action == "update":
            updated, failed = pm.update_modules(args.module_id)
            for module_id, version in updated:
                print("Updated {} to {}.".format(module_id, version))
            for module_id, reason in failed:
                print("Could not update {}: {}".format(module_id, reason))
            if failed:
                return 1
            if not updated:
                print("No installed plugins to update.")
        elif args.package_action == "info":
            item = pm._find_package(args.module_id)
            print(json.dumps({key: value for key, value in item.items()
                              if not key.startswith("_")}, indent=2, ensure_ascii=False))
        return 0
    except pm.PackageError as exc:
        print("Package manager:", exc)
        return 2


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
            print("Commands: tbox list, info, doctor, run MODULE, search, install, remove, update, repo")
        elif choice == "0":
            print("Goodbye.")
            return 0
        else:
            print("Invalid choice.")
        input("\nPress Enter to continue...")


def main(argv=None):
    ensure_dirs()
    parser = argparse.ArgumentParser(prog="tbox", description="T-BOX Termux Toolbox")
    version_file = Path(__file__).resolve().parents[1] / "VERSION"
    version = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "unknown"
    parser.add_argument("--version", action="version", version="T-BOX " + version)
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

    repo_parser = sub.add_parser("repo", help="Manage plugin repositories")
    repos = repo_parser.add_subparsers(dest="repo_action", required=True)
    repos.add_parser("list")
    repo_add = repos.add_parser("add")
    repo_add.add_argument("name")
    repo_add.add_argument("index_url")
    repo_remove = repos.add_parser("remove")
    repo_remove.add_argument("name")

    search = sub.add_parser("search", help="Search plugin repositories")
    search.add_argument("query", nargs="?")
    for action in ("install", "remove", "plugin-info"):
        command = sub.add_parser(action, help="Show plugin metadata" if action == "plugin-info" else "{} a plugin".format(action.capitalize()))
        command.add_argument("module_id")
        command.set_defaults(package_action="info" if action == "plugin-info" else action)
    update = sub.add_parser("update", help="Update installed plugins")
    update.add_argument("module_id", nargs="?")
    update.set_defaults(package_action="update")
    search.set_defaults(package_action="search")

    args = parser.parse_args(argv)
    if not args.command:
        return interactive_menu()
    if args.command == "list": return cmd_list(args)
    if args.command == "info": return cmd_info(args)
    if args.command == "doctor": return cmd_doctor(args)
    if args.command == "run": return cmd_run(args)
    if args.command == "config": return cmd_config(args)
    if args.command == "repo": return cmd_repo(args)
    if args.command in ("search", "install", "remove", "update"): return cmd_package(args)
    return 0
