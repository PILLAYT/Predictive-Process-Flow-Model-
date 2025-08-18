import base64, pathlib, textwrap
data = base64.b64encode(pathlib.Path("background.png").read_bytes()).decode()
# save as a single uninterrupted line
pathlib.Path("background_b64.txt").write_text(data, encoding="utf-8")
print("✅  Wrote background_b64.txt")
