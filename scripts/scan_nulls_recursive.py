import sys
from pathlib import Path

def scan_dir(root: Path):
    bad = []
    for p in root.rglob('*.py'):
        data = p.read_bytes()
        nuls = data.count(b'\x00')
        if nuls:
            bad.append((p, len(data), nuls))
    return bad

if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    bad = scan_dir(root)
    if not bad:
        print("No .py files with null bytes found.")
        sys.exit(0)
    for p, size, nuls in bad:
        print(f"{p}: {size} bytes, null bytes: {nuls}")
    print("If you find corrupted files, restore from git or replace the files.")