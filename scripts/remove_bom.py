from pathlib import Path
p = Path(r"c:\Users\aadhi\OneDrive\Desktop\Assignment 3\frontdesk-ai-supervisor\ai_agent\simple_groq_agent.py")
data = p.read_bytes()
if data.startswith(b'\xef\xbb\xbf'):
    bak = p.with_suffix(p.suffix + '.bom.bak')
    bak.write_bytes(data)
    p.write_bytes(data[3:])
    print(f"Removed BOM, backup written to {bak}")
else:
    print("No BOM found")