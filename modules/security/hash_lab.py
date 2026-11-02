import argparse, hashlib
from pathlib import Path

ALGORITHMS = ("md5", "sha1", "sha256", "sha512")

def digest_file(path, algorithm):
    digest = hashlib.new(algorithm)
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def main():
    parser = argparse.ArgumentParser(description="File hash calculator")
    parser.add_argument("file")
    parser.add_argument("-a", "--algorithm", choices=ALGORITHMS, default="sha256")
    parser.add_argument("--verify", help="Expected digest to compare")
    args = parser.parse_args()
    try:
        value = digest_file(args.file, args.algorithm)
    except OSError as exc:
        print("Cannot read file:", exc); raise SystemExit(2)
    print("{}  {}".format(value, args.file))
    if args.verify:
        ok = value.lower() == args.verify.lower()
        print("Verification:", "MATCH" if ok else "MISMATCH")
        raise SystemExit(0 if ok else 1)

if __name__ == "__main__": main()
