from pathlib import Path

root = Path.cwd()
print("Scanning .py files under:", root)

found = []
for p in sorted(root.rglob("*.py")):
    try:
        b = p.read_bytes()
    except Exception as e:
        print("ERROR reading", p, e)
        continue
    nuls = b.count(b'\x00')
    bom = b.startswith(b'\xef\xbb\xbf')
    if nuls or bom:
        info = {"path": str(p), "size": len(b), "nulls": nuls, "bom": bom}
        # show a few positions and a small hex window around first null (if any)
        if nuls:
            idxs = [i for i, x in enumerate(b) if x == 0][:10]
            info["null_positions"] = idxs
            i0 = idxs[0]
            start = max(0, i0-16)
            end = min(len(b), i0+16)
            info["hex_window"] = " ".join(f"{x:02x}" for x in b[start:end])
        found.append(info)

if not found:
    print("No BOM or NUL bytes found in any .py files.")
else:
    for f in found:
        print(f"\n{f['path']}: size={f['size']} nulls={f['nulls']} bom={f['bom']}")
        if "null_positions" in f:
            print(" first null positions (up to 10):", f["null_positions"])
            print(" hex around first null:", f["hex_window"])