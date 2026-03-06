#!/usr/bin/env python3
"""
Local voice dispatch test using Modulate Velma-2.

Flow:
  1. Reads the dispatch script aloud via macOS `say`
  2. Records your microphone response (script + 20s silence window)
  3. Sends audio to Modulate Velma-2 for transcription + emotion
  4. Supports "can you repeat", confirms acceptance/decline by voice

Requirements (install once):
  pip install sounddevice soundfile requests
  brew install portaudio
"""

import os
import sys
import subprocess
import tempfile
import time
import wave

import numpy as np
import requests
import sounddevice as sd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.voice_dispatch_agent import VoiceDispatchAgent
from mock_data import get_mock_drivers, get_mock_order
from models import CallOutcome, OrderRequest, RankingScore, VoiceCallResult
from config import settings

# ── Config ────────────────────────────────────────────────────────────────────
SAMPLE_RATE     = 16_000   # 16 kHz — good for speech
SILENCE_TIMEOUT = 20       # seconds to wait after script ends for a response
WARMUP_DELAY    = 0.8      # seconds between mic start and say, so mic is ready
MAX_REPEATS     = 2        # max times driver can ask to repeat
MODULATE_URL    = "https://modulate-developer-apis.com/api/velma-2-stt-batch"

ACCEPT_KEYWORDS  = {"yes", "yeah", "yep", "sure", "accept", "okay", "ok",
                    "will do", "absolutely", "affirmative", "i will", "i can"}
DECLINE_KEYWORDS = {"no", "nope", "nah", "decline", "can't", "cannot",
                    "won't", "busy", "unavailable", "negative", "not available"}
REPEAT_KEYWORDS  = {"repeat", "again", "say again", "come again", "pardon",
                    "didn't catch", "what was that", "one more time"}

EMOTION_SCORES = {
    "happy": 0.90, "excited": 0.85, "satisfied": 0.80,
    "calm": 0.65,  "neutral": 0.60,
    "confused": 0.40, "fearful": 0.35,
    "sad": 0.30,   "frustrated": 0.25, "angry": 0.20,
}


# ── Audio helpers ─────────────────────────────────────────────────────────────

def estimate_say_duration(text: str, rate: int = 185) -> float:
    """Rough estimate of how long `say` will take (seconds)."""
    return (len(text.split()) / rate) * 60 + 1.0


def speak(text: str) -> None:
    """Read text aloud and block until finished."""
    subprocess.run(["say", "-r", "185", text], check=True)


def record_and_speak(script: str) -> tuple[np.ndarray, float]:
    """Start mic, warm up briefly, then play script.
    Keeps recording for SILENCE_TIMEOUT seconds after script ends.
    Returns (recording array, total duration in seconds)."""
    script_duration = estimate_say_duration(script)
    total_duration  = script_duration + SILENCE_TIMEOUT

    print("\n  Connecting call...", flush=True)

    # Start mic first, then wait for warm-up before speaking
    recording = sd.rec(
        int(total_duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
    )
    time.sleep(WARMUP_DELAY)

    # Start script playback (non-blocking)
    say_proc = subprocess.Popen(["say", "-r", "185", script])

    print("  Call connected — respond any time\n", flush=True)

    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed >= total_duration:
            break
        print(f"  Recording... ({int(elapsed)}s)", end="\r", flush=True)
        time.sleep(0.5)

    sd.wait()
    say_proc.terminate()
    print("  Call ended.            ")
    return recording, total_duration


def save_wav(recording: np.ndarray) -> str:
    """Write recording to a temp WAV file and return its path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(recording.tobytes())
    return tmp.name


# ── Modulate Velma-2 ──────────────────────────────────────────────────────────

def transcribe(audio_path: str) -> dict:
    """Send WAV to Modulate Velma-2 and return the full JSON response."""
    print("\n  Analysing response...", flush=True)
    with open(audio_path, "rb") as f:
        resp = requests.post(
            MODULATE_URL,
            headers={"X-API-Key": settings.modulate_api_key},
            files={"upload_file": f},
            data={"speaker_diarization": "true", "emotion_signal": "true"},
            timeout=60,
        )
    resp.raise_for_status()
    return resp.json()


# ── Parsing helpers ───────────────────────────────────────────────────────────

def wants_repeat(transcript: str) -> bool:
    lower = transcript.lower()
    return any(kw in lower for kw in REPEAT_KEYWORDS)


def parse_outcome(transcript: str) -> tuple[CallOutcome, str | None]:
    """Return (CallOutcome, decline_reason). Silence → DECLINED."""
    if not transcript.strip():
        return CallOutcome.DECLINED, "No response received"
    lower = transcript.lower()
    for kw in ACCEPT_KEYWORDS:
        if kw in lower:
            return CallOutcome.ACCEPTED, None
    for kw in DECLINE_KEYWORDS:
        if kw in lower:
            return CallOutcome.DECLINED, transcript.strip()
    # Heard something but couldn't classify → treat as no response
    return CallOutcome.DECLINED, "No clear response received"


def extract_sentiment(modulate_response: dict) -> float:
    utterances = modulate_response.get("utterances", [])
    if not utterances:
        return 0.5
    scores = [
        EMOTION_SCORES.get((u.get("emotion") or "neutral").lower(), 0.5)
        for u in utterances
    ]
    return round(sum(scores) / len(scores), 3)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n" + "=" * 60)
    print("  CHEETAH EXPRESS — LOCAL VOICE DISPATCH TEST")
    print("=" * 60)

    driver  = get_mock_drivers()[0]
    order   = OrderRequest(**get_mock_order("ORD001"))
    ranking = RankingScore(
        driver_id=driver.driver_id,
        score=92.0,
        eta_to_pickup_minutes=7.0,
        total_trip_time_minutes=22.0,
        vehicle_match=True,
        license_expiry_buffer_days=365,
        remaining_km_budget=200.0,
        reasoning="Top ranked driver",
    )

    agent  = VoiceDispatchAgent()
    script = agent._generate_call_script(driver, order, ranking)

    print(f"\n  Driver : {driver.name}  ({driver.driver_id})")
    print(f"  Order  : {order.order_id}  {order.pickup.address} → {order.dropoff.address}")
    print(f"\n  Script : {script}\n")

    input("  Press Enter to place the call...")

    # ── Call loop (supports repeat requests) ──────────────────────────────────
    call_start  = time.time()
    repeat_count = 0
    response    = {}
    transcript  = ""
    outcome     = CallOutcome.DECLINED
    decline_reason = "No response received"

    while True:
        recording, duration = record_and_speak(script)
        wav_path = save_wav(recording)

        try:
            response = transcribe(wav_path)
        except requests.HTTPError as e:
            print(f"\n  Modulate API error: {e.response.status_code} — {e.response.text}")
            return
        except Exception as e:
            print(f"\n  Error: {e}")
            return
        finally:
            os.unlink(wav_path)

        transcript = response.get("text", "")

        # Driver asked to repeat — replay up to MAX_REPEATS times
        if wants_repeat(transcript) and repeat_count < MAX_REPEATS:
            repeat_count += 1
            speak("Sure, let me repeat that.")
            continue

        outcome, decline_reason = parse_outcome(transcript)
        break

    call_duration = time.time() - call_start

    # ── Voice acknowledgment ──────────────────────────────────────────────────
    if outcome == CallOutcome.ACCEPTED:
        speak("Order confirmed.")
    else:
        speak("You have declined.")

    # ── Build result ──────────────────────────────────────────────────────────
    result = VoiceCallResult(
        driver_id=driver.driver_id,
        outcome=outcome,
        sentiment_score=extract_sentiment(response),
        decline_reason=decline_reason,
        transcript=transcript,
        call_duration_seconds=round(call_duration, 1),
    )

    # ── Print summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  RESULT")
    print("=" * 60)
    print(f"  Outcome       : {result.outcome.value.upper()}")
    print(f"  Transcript    : {transcript or '(nothing heard)'}")
    print(f"  Sentiment     : {result.sentiment_score}")
    print(f"  Decline reason: {result.decline_reason or 'N/A'}")
    print(f"  Call duration : {result.call_duration_seconds}s")
    print(f"  Repeat asks   : {repeat_count}")
    if response.get("utterances"):
        print(f"\n  Utterances ({len(response['utterances'])}):")
        for u in response["utterances"]:
            print(f"    {u}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
