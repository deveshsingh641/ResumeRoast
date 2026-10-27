"""
Voice Note Roast Service — WhatsApp-Style Audio Generator.
Builds natural spoken Hinglish script from existing roast analysis,
synthesizes voice audio with gTTS / ElevenLabs, and caches MP3 files on disk.
"""
from __future__ import annotations

import io
import math
import os
import re
import struct
import wave
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "voice_notes")
os.makedirs(STORAGE_DIR, exist_ok=True)


from app.i18n.mapping import DEFAULT_LANGUAGE, normalize_language


def build_voice_roast_script(
    one_line_verdict: str,
    issues: list[dict],
    overall_score: int,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """
    Composes a natural, conversational 3-4 sentence spoken script
    in the requested language (English or Hinglish) optimized for 25-40 seconds of playback.
    Strips raw emojis and markdown so TTS engine speaks cleanly.
    """
    lang = normalize_language(language)

    # Clean text from emojis and markdown formatting (covers SMP and BMP emoji ranges)
    def _clean(t: str) -> str:
        t = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27BF\u2300-\u23FF\u2B50\u200D\uFE0F]", "", t)
        t = re.sub(r"[\*\_\#\`\"]", "", t)
        return " ".join(t.split())

    clean_verdict = _clean(one_line_verdict)

    # Pick top 2 roasts
    roast_points = []
    for issue in issues[:2]:
        r_text = _clean(issue.get("roast", ""))
        if r_text:
            roast_points.append(r_text)

    if lang == "hi-IN":
        openers = [
            "Arre bhai, maine tera resume poora check kiya.",
            "Sun bhai, tere resume ka official post-mortem taiyar hai.",
            "Arey yaar, resume desk pe aate hi maine padhna shuru kiya.",
        ]
        opener = openers[overall_score % len(openers)]

        if len(roast_points) >= 2:
            roast_body = f"Pehli baat: {roast_points[0]} Aur doosri baat: {roast_points[1]}"
        elif len(roast_points) == 1:
            roast_body = f"Sabse bada issue: {roast_points[0]}"
        else:
            roast_body = f"Verdict ye hai: {clean_verdict}."

        closers = [
            f"Score mila hai {overall_score} out of 100. Jaldi se fixes check kar aur group chat mein share kar de!",
            f"Overall score {overall_score} hai. Thoda metrics daalo boss, tabhi shortlist aayega. All the best!",
            f"Score {overall_score} out of 100 bana hai. Bullet points rewrite karo aur agle round ke liye ready ho jao!",
        ]
        closer = closers[overall_score % len(closers)]
    else:
        openers = [
            "Look, I just went through your entire resume.",
            "Alright, here is the honest post-mortem on your resume.",
            "Okay, I just pulled your resume off the stack.",
        ]
        opener = openers[overall_score % len(openers)]

        if len(roast_points) >= 2:
            roast_body = f"First off: {roast_points[0]}. And second: {roast_points[1]}."
        elif len(roast_points) == 1:
            roast_body = f"The single biggest issue: {roast_points[0]}."
        else:
            roast_body = f"The bottom line: {clean_verdict}."

        closers = [
            f"You scored {overall_score} out of 100. Check the suggested fixes and give your bullets some real numbers!",
            f"Overall score is {overall_score}. Add concrete metrics so recruiters have something to believe. Good luck!",
            f"That's a score of {overall_score} out of 100. Tighten up the phrasing, cut the fluff, and get ready for interviews!",
        ]
        closer = closers[overall_score % len(closers)]

    script = f"{opener} {clean_verdict}. {roast_body} {closer}"
    return script.strip()


def _synthesize_with_gtts(script_text: str, output_path: str, language: str = DEFAULT_LANGUAGE) -> bool:
    """Synthesize voice using gTTS with language-appropriate accent."""
    lang = normalize_language(language)
    try:
        from gtts import gTTS
        if lang == "hi-IN":
            tts = gTTS(text=script_text, lang="en", tld="co.in", slow=False)
        else:
            tts = gTTS(text=script_text, lang="en", tld="com", slow=False)
        tts.save(output_path)
        return True
    except Exception as e:
        print(f"[WARN] gTTS primary failed: {e}. Trying fallback...")
        try:
            from gtts import gTTS
            tts = gTTS(text=script_text, lang="en", slow=False)
            tts.save(output_path)
            return True
        except Exception as e2:
            print(f"[WARN] gTTS en fallback failed: {e2}")
            return False


def _generate_synthetic_tone_mp3(output_path: str, duration_sec: int = 15) -> bool:
    """
    Fallback audio generator: generates a valid MP3 bitstream
    if network TTS fails completely, ensuring HTML5 audio player never errors out.
    """
    try:
        # Valid MPEG-1 Layer 3 128kbps 44.1kHz frame (417 bytes per frame)
        frame_header = b"\xff\xfb\x90\x64"
        frame_payload = b"\x00" * 413
        single_frame = frame_header + frame_payload
        # ~38.28 frames per second
        total_frames = int(38.28 * max(1, duration_sec))
        with open(output_path, "wb") as wf:
            for _ in range(total_frames):
                wf.write(single_frame)
        return True
    except Exception as e:
        print(f"[ERROR] Synthetic audio generator error: {e}")
        return False


def generate_voice_roast_audio(roast_id: str, script_text: str, language: str = DEFAULT_LANGUAGE) -> str:
    """
    Generates and caches MP3 audio for a given roast and language.
    Returns the absolute path to the cached MP3 file.
    """
    lang = normalize_language(language)
    cache_key = f"{roast_id}_{lang}"
    out_file = os.path.join(STORAGE_DIR, f"{cache_key}.mp3")
    if os.path.exists(out_file) and os.path.getsize(out_file) > 1000:
        return out_file

    # 1. Try ElevenLabs if API key configured
    eleven_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if eleven_key:
        try:
            import httpx
            voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default friendly voice
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "xi-api-key": eleven_key,
                "Content-Type": "application/json",
            }
            payload = {
                "text": script_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            }
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    with open(out_file, "wb") as f:
                        f.write(res.content)
                    return out_file
        except Exception as e:
            print(f"[WARN] ElevenLabs TTS failed: {e}. Falling back to gTTS...")

    # 2. Try gTTS
    success = _synthesize_with_gtts(script_text, out_file, language=lang)
    if success and os.path.exists(out_file) and os.path.getsize(out_file) > 500:
        return out_file

    # 3. Fallback tone audio
    _generate_synthetic_tone_mp3(out_file, duration_sec=12)
    return out_file


def get_cached_voice_audio_path(roast_id: str, language: str = DEFAULT_LANGUAGE) -> Optional[str]:
    """Returns path to cached audio file if present."""
    lang = normalize_language(language)
    cache_key = f"{roast_id}_{lang}"
    path = os.path.join(STORAGE_DIR, f"{cache_key}.mp3")
    if os.path.exists(path) and os.path.getsize(path) > 500:
        return path
    base_path = os.path.join(STORAGE_DIR, f"{roast_id}.mp3")
    if os.path.exists(base_path) and os.path.getsize(base_path) > 500:
        return base_path
    return None
