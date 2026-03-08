import os
import tempfile


def check_voice_dependencies() -> bool:
    """Returns True only if ALL voice packages are installed."""
    try:
        import sounddevice  # noqa: F401
        import faster_whisper  # noqa: F401
        import scipy  # noqa: F401
        import numpy  # noqa: F401

        return True
    except Exception:
        return False


def get_voice_dependency_status() -> dict:
    """
    Returns a dict with per-module import status for debugging environment issues.
    Example:
      {
        "sounddevice": "ok" / "ImportError: ...",
        "faster_whisper": "...",
        "scipy": "...",
        "numpy": "..."
      }
    """
    status = {}
    for mod in ["sounddevice", "faster_whisper", "scipy", "numpy"]:
        try:
            __import__(mod)
            status[mod] = "ok"
        except Exception as e:
            status[mod] = f"{type(e).__name__}: {str(e)}"
    return status


def record_and_transcribe(duration_seconds: int = 15) -> str:
    """
    Records audio from microphone and transcribes with local Whisper.
    Returns transcript string or error string starting with 'Error:'.
    100% local — no API key, no internet needed.
    """
    try:
        import numpy as np
        import scipy.io.wavfile as wav
        import sounddevice as sd
        from faster_whisper import WhisperModel
    except ImportError as e:
        return f"Error: Missing package — {str(e)}"

    sample_rate = 16000

    try:
        audio_data = sd.rec(
            int(duration_seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio_int16 = (audio_data * 32767).astype(np.int16)
            wav.write(tmp.name, sample_rate, audio_int16)
            tmp_path = tmp.name

        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(tmp_path, language="en")
        transcript = " ".join(seg.text for seg in segments)

        os.unlink(tmp_path)
        return transcript.strip()

    except Exception as e:
        return f"Error: {str(e)}"

