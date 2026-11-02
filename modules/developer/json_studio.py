import argparse, json, sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Validate and format JSON")
    parser.add_argument("file", nargs="?", help="JSON file; reads stdin when omitted")
    parser.add_argument("-o", "--output", help="Write formatted JSON to this file")
    args = parser.parse_args()
    try:
        raw = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
        data = json.loads(raw)
        rendered = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
            print("Valid JSON. Written to", args.output)
        else:
            print(rendered, end="")
    except FileNotFoundError:
        print("File not found:", args.file, file=sys.stderr); raise SystemExit(2)
    except json.JSONDecodeError as exc:
        print("Invalid JSON at line {}, column {}: {}".format(exc.lineno, exc.colno, exc.msg), file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__": main()
