"""Microphone input for JARVIS: records until you stop speaking."""
import numpy as np
import sounddevice as sd

import config

BLOCK_SECONDS = 0.1          # check the sound every 0.1 second
SILENCE_SECONDS = 1.2        # stop after this much silence
MAX_SECONDS = 15             # never record longer than this
WAIT_FOR_SPEECH_SECONDS = 6  # give up if you say nothing
MIN_THRESHOLD = 0.015        # smallest sound level counted as speech


def record_until_silence(on_ready=None, on_level=None):
    """Record from the microphone. Stops when you finish speaking.
    on_ready() is called when recording starts, on_level(level) many times
    a second with the current loudness (used by the waveform).
    Returns the audio, or None if nothing was heard."""
    rate = config.SAMPLE_RATE
    block = int(rate * BLOCK_SECONDS)
    silence_blocks = int(SILENCE_SECONDS / BLOCK_SECONDS)
    max_blocks = int(MAX_SECONDS / BLOCK_SECONDS)
    wait_blocks = int(WAIT_FOR_SPEECH_SECONDS / BLOCK_SECONDS)

    chunks = []
    started = False
    silent = 0

    with sd.InputStream(samplerate=rate, channels=1,
                        dtype="float32", blocksize=block) as stream:
        # Step 1: learn how noisy the room is (0.5 second)
        levels = []
        for _i in range(5):
            data, _over = stream.read(block)
            levels.append(float(np.sqrt(np.mean(data ** 2))))
        threshold = max(MIN_THRESHOLD, float(np.mean(levels)) * 3)

        if on_ready:
            on_ready()

        # Step 2: listen until you speak, then until you stop
        for i in range(max_blocks):
            data, _over = stream.read(block)
            chunks.append(data)
            level = float(np.sqrt(np.mean(data ** 2)))
            if on_level:
                on_level(level)

            if level > threshold:
                started = True
                silent = 0
            elif started:
                silent += 1

            if started and silent >= silence_blocks:
                break
            if not started and i >= wait_blocks:
                return None

    if not started:
        return None
    return np.concatenate(chunks).squeeze()


if __name__ == "__main__":
    from faster_whisper import WhisperModel

    print("Loading the listening model...")
    model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")

    print("Stay quiet for a second, then speak when you see SPEAK NOW.")
    audio = record_until_silence(on_ready=lambda: print(">>> SPEAK NOW"))

    if audio is None:
        print("I did not hear anything.")
    else:
        print(f"Recorded {len(audio) / config.SAMPLE_RATE:.1f} seconds.")
        segments, info = model.transcribe(audio)
        print("You said:", " ".join(s.text for s in segments).strip())
