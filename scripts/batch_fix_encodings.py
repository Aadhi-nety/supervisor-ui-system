from pathlib import Path
import shutil

root = Path.cwd()
print("Scanning .py files under:", root)

changed = []
for p in sorted(root.rglob("*.py")):
    b = p.read_bytes()
    # detect common BOMs / encodings
    if b.startswith(b'\xef\xbb\xbf'):
        # UTF-8 with BOM
        text = b.decode('utf-8-sig')
        reason = "utf-8-bom"
    elif b.startswith(b'\xff\xfe') or b.startswith(b'\xfe\xff') or b.count(b'\x00') > 0:
        # likely UTF-16 or contains NULs -> try utf-16 then fall back
        try:
            text = b.decode('utf-16')
            reason = "utf-16-or-nuls"
        except Exception:
            try:
                text = b.decode('utf-8', errors='replace')
                reason = "had-nuls, forced-utf8-replace"
            except Exception:
                text = b.decode('latin-1', errors='replace')
                reason = "latin1-fallback"
    else:
        # already utf-8 no BOM: skip
        continue

    bak = p.with_suffix(p.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(p, bak)
    p.write_text(text, encoding='utf-8')  # writes UTF-8 without BOM
    changed.append((str(p), reason))

print(f"Fixed {len(changed)} files:")
for f, r in changed:
    print(" ", f, "->", r)
print("Backups saved as .py.bak next to each file.")
