from pathlib import Path

src = Path(__file__).parent / "app" / "services" / "ai_analyzer.py"
text = src.read_text(encoding="utf-8")
start = text.index("SYSTEM_PROMPT = ")
end = text.index("VALID_BANDS")
chunk = text[start:end]
out_dir = Path(__file__).parent / "app" / "prompts"
out_dir.mkdir(parents=True, exist_ok=True)
header = '"""Hinglish (hi-IN) roast persona — native WhatsApp-style Hinglish, not a translation."""\n\n'
(out_dir / "hi_IN.py").write_text(header + chunk, encoding="utf-8")
print("ok", len(chunk))
