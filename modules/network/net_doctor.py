import argparse, socket, time, urllib.request, urllib.error

def main():
    parser = argparse.ArgumentParser(description="Basic network diagnostics")
    parser.add_argument("host", nargs="?", default="example.com", help="Hostname to resolve")
    parser.add_argument("--https", action="store_true", help="Also test HTTPS reachability")
    args = parser.parse_args()
    print("DNS lookup:", args.host)
    try:
        start = time.monotonic()
        records = sorted({item[4][0] for item in socket.getaddrinfo(args.host, None)})
        print("Resolved :", ", ".join(records))
        print("DNS time :", "{:.1f} ms".format((time.monotonic()-start)*1000))
    except socket.gaierror as exc:
        print("DNS failed:", exc)
        return
    if args.https:
        url = "https://" + args.host
        request = urllib.request.Request(url, method="HEAD", headers={"User-Agent":"T-BOX/0.1"})
        try:
            start = time.monotonic()
            with urllib.request.urlopen(request, timeout=8) as response:
                print("HTTPS    :", response.status)
                print("Latency  :", "{:.1f} ms".format((time.monotonic()-start)*1000))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print("HTTPS failed:", exc)

if __name__ == "__main__": main()
