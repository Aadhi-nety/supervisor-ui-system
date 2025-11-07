from pathlib import Path

p = Path(r"c:\Users\aadhi\OneDrive\Desktop\Assignment 3\frontdesk-ai-supervisor\ai_agent\simple_groq_agent.py")
if not p.exists():
    print("ERROR: file not found:", p)
    raise SystemExit(1)

orig = p.read_bytes()
data = orig
removed_bom = False
removed_nulls = 0

# Remove UTF-8 BOM if present
if data.startswith(b'\xef\xbb\xbf'):
    data = data[3:]
    removed_bom = True

# Remove any NUL bytes
if b'\x00' in data:
    removed_nulls = data.count(b'\x00')
    data = data.replace(b'\x00', b'')

if removed_bom or removed_nulls:
    bak = p.with_suffix(p.suffix + '.clean.bak')
    bak.write_bytes(orig)
    p.write_bytes(data)
    print(f"Backup written to {bak}")
    print(f"Removed BOM: {removed_bom}, removed_nulls: {removed_nulls}, new size: {len(data)} bytes")
else:
    print("No BOM or NUL bytes found; file unchanged.")