import sys
from pathlib import Path

def inspect_and_clean(p: Path, do_clean=False):
    data = p.read_bytes()
    null_count = data.count(b'\x00')
    print(f"{p}: {len(data)} bytes, null bytes: {null_count}")
    if null_count:
        idxs = [i for i, b in enumerate(data) if b == 0][:10]
        print("First null byte positions (up to 10):", idxs)
        if do_clean:
            bak = p.with_suffix(p.suffix + '.bak')
            bak.write_bytes(data)
            cleaned = data.replace(b'\x00', b'')
            p.write_bytes(cleaned)
            print(f"Backup written to {bak}. Null bytes removed.")
    else:
        print("No null bytes found.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python clean_nulls.py <path> [--clean]")
        sys.exit(1)
    path = Path(sys.argv[1])
    inspect_and_clean(path, do_clean=('--clean' in sys.argv))