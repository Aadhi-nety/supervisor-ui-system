import sys
from pathlib import Path
import traceback
def hexdump(b, n=160):
    return " ".join(f"{x:02x}" for x in b[:n])

if len(sys.argv) < 2:
    print("Usage: python diag_import.py <path-to-py>")
    sys.exit(1)

p = Path(sys.argv[1])
if not p.exists():
    print("File not found:", p)
    sys.exit(2)

data = p.read_bytes()
print(f"{p}: {len(data)} bytes")
nulls = data.count(b'\\x00')
print("null bytes:", nulls)
if nulls:
    idxs = [i for i, b in enumerate(data) if b == 0][:20]
    print("first null positions (up to 20):", idxs)

try:
    s = data.decode('utf-8')
    print("Decoded as utf-8 OK")
except Exception as e:
    print("utf-8 decode error:", e)
    s = data.decode('latin-1', errors='replace')
    print("Decoded with latin-1 (lossless mapping).")

print("hex preview (first 160 bytes):")
print(hexdump(data, 160))
print("\nrepr preview (first 400 chars):")
print(repr(s[:400]))

print("\nAttempting compile() of source (will raise if syntax/source problem)...")
try:
    compile(s, str(p), 'exec')
    print("compile() succeeded")
except Exception as e:
    print("compile() failed:", type(e).__name__, e)
    traceback.print_exc()
    # show the bytes around an example error position if available
    # no further assumptions here