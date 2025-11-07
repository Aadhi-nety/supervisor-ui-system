import importlib.util
from pathlib import Path
import binascii
import sys, traceback

name = "ai_agent.simple_groq_agent"
spec = importlib.util.find_spec(name)
print("find_spec:", spec)
if spec is None:
    print("Module spec not found on sys.path. sys.path[:10]:", sys.path[:10])
    raise SystemExit(1)

origin = getattr(spec, "origin", None)
print("origin:", origin)
if origin is None:
    print("No origin for spec; loader:", getattr(spec, "loader", None))
    raise SystemExit(1)

p = Path(origin)
if not p.exists():
    print("Origin file does not exist:", p)
    raise SystemExit(1)

data = p.read_bytes()
nulls = data.count(b'\x00')
print(f"file: {p}  size: {len(data)} bytes  null bytes: {nulls}")

# show BOM if present
if data.startswith(b'\xef\xbb\xbf'):
    print("UTF-8 BOM present (EF BB BF)")

# hex preview
print("hex preview (first 160 bytes):")
print(" ".join(f"{b:02x}" for b in data[:160]))

# text preview (try utf-8 then latin-1)
try:
    text = data.decode('utf-8')
    print("decoded utf-8 OK")
except Exception as e:
    print("utf-8 decode failed:", e)
    text = data.decode('latin-1', errors='replace')
print("repr preview (first 300 chars):")
print(repr(text[:300]))

# try compile to reproduce Python error
print("\nAttempting compile() of source (may raise SyntaxError):")
try:
    compile(text, str(p), 'exec')
    print("compile() succeeded")
except Exception as e:
    print("compile() failed:", type(e).__name__, e)
    traceback.print_exc()