import asyncio
import json
import os
import subprocess
import tempfile
import time
import wave
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

import httpx
import numpy as np
import sounddevice as sd
import structlog
from websockets.sync.client import connect

from config import settings
from database.neo4j_client import neo4j_client
from models import CallOutcome, DriverInfo, OrderRequest, RankingScore, VoiceCallResult

logger = structlog.get_logger()

# ── Constants ─────────────────────────────────────────────────────────────────

SAMPLE_RATE        = 16_000   # Hz — good for speech
SILENCE_TIMEOUT    = 20       # seconds to wait after script ends
MIC_PRIME_DURATION = 0.5      # seconds — short pre-roll to wake the mic before main recording
WARMUP_DELAY       = 2.0      # seconds between mic start and `say`, so mic is ready
MAX_REPEATS        = 2
STREAMING_CHUNK_MS = 100      # ms of audio per WebSocket chunk for Velma-2 streaming
STREAMING_RECV_S   = 30       # max seconds to wait for final transcript

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


class VoiceDispatchAgent:

    def __init__(self):
        self.modulate_base_url = settings.modulate_base_url
        self.api_key = settings.modulate_api_key
        self.neo4j = neo4j_client

    # ── Public dispatch loop ───────────────────────────────────────────────────

    async def dispatch_to_drivers(
        self,
        drivers: List[DriverInfo],
        rankings: List[RankingScore],
        order: OrderRequest,
    ) -> Optional[VoiceCallResult]:
        driver_map = {d.driver_id: d for d in drivers}

        for ranking in rankings:
            driver = driver_map.get(ranking.driver_id)
            if not driver:
                continue

            logger.info(
                "Calling driver",
                driver_id=driver.driver_id,
                driver_name=driver.name,
                rank=rankings.index(ranking) + 1,
            )

            call_result = await self._call_driver(driver, order, ranking)

            self.neo4j.log_voice_call_outcome(
                order_id=order.order_id,
                driver_id=driver.driver_id,
                call_result={
                    "outcome": call_result.outcome.value,
                    "sentiment_score": call_result.sentiment_score,
                    "decline_reason": call_result.decline_reason,
                    "call_duration_seconds": call_result.call_duration_seconds,
                },
            )

            if call_result.outcome == CallOutcome.ACCEPTED:
                logger.info("Driver accepted", driver_id=driver.driver_id)
                return call_result

            logger.info(
                "Driver declined / unavailable",
                driver_id=driver.driver_id,
                outcome=call_result.outcome.value,
                reason=call_result.decline_reason,
            )

        logger.warning("No driver accepted", order_id=order.order_id)
        return None

    # ── Core call — runs local audio flow via thread executor ─────────────────

    async def _call_driver(
        self,
        driver: DriverInfo,
        order: OrderRequest,
        ranking: RankingScore,
    ) -> VoiceCallResult:
        script = self._generate_call_script(driver, order, ranking)
        logger.info("Placing voice call", driver_id=driver.driver_id, phone=driver.phone)

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = await loop.run_in_executor(
                executor,
                self._local_voice_call,
                driver,
                script,
            )
        return result

    def _local_voice_call(self, driver: DriverInfo, script: str) -> VoiceCallResult:
        """Blocking: speak script → record → transcribe via Velma-2 Streaming (WebSocket) → parse."""
        try:
            default_input = sd.query_devices(kind="input")
            logger.info(
                "Using default input device for recording",
                device=default_input.get("name"),
                sample_rate=default_input.get("default_samplerate"),
            )
        except Exception as e:
            logger.warning("Could not query default input device", error=str(e))

        self._prime_microphone()

        script_duration = (len(script.split()) / 185) * 60 + 1.0
        total_duration  = script_duration + SILENCE_TIMEOUT
        repeat_count    = 0
        transcript      = ""
        response        = {}
        call_start      = time.time()

        while True:
            recording = sd.rec(
                int(total_duration * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
            )
            time.sleep(WARMUP_DELAY)
            say_proc = subprocess.Popen(["say", "-r", "185", script])

            sd.wait()
            say_proc.terminate()

            wav_path = self._save_wav(recording)
            try:
                response = self._transcribe(wav_path)
            except Exception as e:
                logger.error("Velma-2 transcription error", error=str(e))
                return VoiceCallResult(
                    driver_id=driver.driver_id,
                    outcome=CallOutcome.FAILED,
                    decline_reason=f"Transcription error: {str(e)}",
                )
            finally:
                os.unlink(wav_path)

            transcript = response.get("text", "")

            # Driver asked to repeat
            if self._wants_repeat(transcript) and repeat_count < MAX_REPEATS:
                repeat_count += 1
                subprocess.run(["say", "-r", "185", "Sure, let me repeat that."], check=False)
                continue

            break

        call_duration              = time.time() - call_start
        outcome, decline_reason    = self._parse_outcome(transcript)
        sentiment                  = self._extract_sentiment(response)

        # Voice acknowledgment
        response_message = self.get_response_message(driver.name, outcome)
        subprocess.run(["say", "-r", "185", response_message], check=False)

        logger.info(
            "Voice call complete",
            driver_id=driver.driver_id,
            outcome=outcome.value,
            transcript=transcript,
            sentiment=sentiment,
        )

        return VoiceCallResult(
            driver_id=driver.driver_id,
            outcome=outcome,
            sentiment_score=sentiment,
            decline_reason=decline_reason,
            transcript=transcript,
            call_duration_seconds=round(call_duration, 1),
        )

    # ── Velma-2 Streaming STT ─────────────────────────────────────────────────

    def _streaming_url(self) -> str:
        """WebSocket URL for Velma-2 streaming (https → wss)."""
        base = self.modulate_base_url.strip().rstrip("/")
        if base.startswith("https://"):
            base = "wss://" + base[8:]
        elif base.startswith("http://"):
            base = "ws://" + base[7:]
        else:
            base = "wss://" + base
        return f"{base}/api/velma-2-stt-streaming"

    def _transcribe_batch(self, audio_path: str) -> dict:
        """POST WAV to Modulate Velma-2 batch STT. Used when streaming returns 403 or fails."""
        with open(audio_path, "rb") as f:
            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    f"{self.modulate_base_url}/api/velma-2-stt-batch",
                    headers={"X-API-Key": self.api_key},
                    files={"upload_file": ("response.wav", f, "audio/wav")},
                    data={"speaker_diarization": "true", "emotion_signal": "true"},
                )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _pcm_from_wav(wav_path: str) -> bytes:
        """Read raw PCM bytes from a WAV file (skip header)."""
        with wave.open(wav_path, "rb") as wf:
            return wf.readframes(wf.getnframes())

    def _transcribe(self, audio_path: str) -> dict:
        """Transcribe WAV via Velma-2. Tries streaming first; falls back to batch on 403 or error."""
        try:
            return self._transcribe_streaming(audio_path)
        except Exception as e:
            err_str = str(e).lower()
            if "403" in err_str or "forbidden" in err_str or "websocket" in err_str or "rejected" in err_str:
                logger.info("Velma-2 streaming unavailable, using batch API", error=str(e))
            else:
                logger.warning("Velma-2 streaming failed, falling back to batch", error=str(e))
            return self._transcribe_batch(audio_path)

    def _transcribe_streaming(self, audio_path: str) -> dict:
        """Stream WAV to Modulate Velma-2 Streaming (WebSocket) and return full response."""
        pcm = self._pcm_from_wav(audio_path)
        wss_uri = self._streaming_url()
        chunk_bytes = int(SAMPLE_RATE * (STREAMING_CHUNK_MS / 1000.0)) * 2  # 16-bit = 2 bytes/sample
        text_parts: List[str] = []
        utterances: List[dict] = []

        with connect(
            wss_uri,
            additional_headers={"X-API-Key": self.api_key},
            open_timeout=15,
            close_timeout=10,
        ) as ws:
            config = {
                "sample_rate": SAMPLE_RATE,
                "speaker_diarization": True,
                "emotion_signal": True,
            }
            try:
                ws.send(json.dumps(config))
            except Exception:
                pass

            for i in range(0, len(pcm), chunk_bytes):
                chunk = pcm[i : i + chunk_bytes]
                if chunk:
                    ws.send(chunk)

            try:
                while True:
                    msg = ws.recv(timeout=STREAMING_RECV_S)
                    if isinstance(msg, bytes):
                        continue
                    try:
                        data = json.loads(msg)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(data, dict):
                        t = data.get("text") or data.get("transcript") or ""
                        if t:
                            text_parts.append(t)
                        if "utterances" in data:
                            utterances.extend(data["utterances"] if isinstance(data["utterances"], list) else [])
                        if data.get("is_final") or data.get("final"):
                            break
            except TimeoutError:
                pass
            except Exception:
                pass

        full_text = " ".join(t for t in text_parts if t).strip()
        return {"text": full_text, "utterances": utterances}

    # ── Audio helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _prime_microphone() -> None:
        """Run a short recording so the default input device is open and ready for the main recording."""
        try:
            prime = sd.rec(
                int(MIC_PRIME_DURATION * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
            )
            sd.wait()
            _ = prime
        except Exception as e:
            logger.warning("Mic prime failed (continuing anyway)", error=str(e))

    @staticmethod
    def _save_wav(recording: np.ndarray) -> str:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(recording.tobytes())
        return tmp.name

    # ── Parsing helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _wants_repeat(transcript: str) -> bool:
        lower = transcript.lower()
        return any(kw in lower for kw in REPEAT_KEYWORDS)

    @staticmethod
    def _parse_outcome(transcript: str):
        if not transcript.strip():
            return CallOutcome.DECLINED, "No response received"
        lower = transcript.lower()
        for kw in ACCEPT_KEYWORDS:
            if kw in lower:
                return CallOutcome.ACCEPTED, None
        for kw in DECLINE_KEYWORDS:
            if kw in lower:
                return CallOutcome.DECLINED, transcript.strip()
        return CallOutcome.DECLINED, "No clear response received"

    @staticmethod
    def _extract_sentiment(modulate_response: dict) -> float:
        utterances = modulate_response.get("utterances", [])
        if not utterances:
            return 0.5
        scores = [
            EMOTION_SCORES.get((u.get("emotion") or "neutral").lower(), 0.5)
            for u in utterances
        ]
        return round(sum(scores) / len(scores), 3)

    # ── Script generator ──────────────────────────────────────────────────────

    def _generate_call_script(
        self,
        driver: DriverInfo,
        order: OrderRequest,
        ranking: RankingScore,
    ) -> str:
        instructions = f" Note: {order.special_instructions}." if order.special_instructions else ""
        return (
            f"Hi {driver.name}, Cheetah Express here. "
            f"New job: pick up at {order.pickup.address}, "
            f"drop off at {order.dropoff.address}. "
            f"{ranking.eta_to_pickup_minutes:.0f} minutes to pickup, "
            f"{ranking.total_trip_time_minutes:.0f} minute trip."
            f"{instructions} "
            f"Say yes to accept or no to decline."
        )

    def get_response_message(self, driver_name: str, outcome: CallOutcome) -> str:
        """Return the acknowledgment phrase we would speak for this outcome."""
        if outcome == CallOutcome.ACCEPTED:
            return "Order confirmed."
        return "You have declined."

    def process_user_audio(
        self, audio_path: str, driver_name: str
    ) -> dict:
        """Transcribe user audio, parse outcome, return transcript + outcome + response message.
        Used for live demo when audio is captured in the browser and sent to the backend."""
        try:
            response = self._transcribe(audio_path)
        except Exception as e:
            logger.error("Velma-2 transcription error", error=str(e))
            return {
                "transcript": "",
                "outcome": CallOutcome.FAILED.value,
                "decline_reason": f"Transcription error: {str(e)}",
                "sentiment_score": 0.5,
                "response_message": (
                    "Sorry, we couldn't process your response. Please try again."
                ),
            }
        transcript = response.get("text", "")
        outcome, decline_reason = self._parse_outcome(transcript)
        sentiment = self._extract_sentiment(response)
        response_message = self.get_response_message(driver_name, outcome)
        return {
            "transcript": transcript,
            "outcome": outcome.value,
            "decline_reason": decline_reason,
            "sentiment_score": sentiment,
            "response_message": response_message,
        }
