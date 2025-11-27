# modules/trim_silence.py
import numpy as np
import librosa

from .helpers import load_audio, save_audio_stereo


PRESETS = {
    "voice": 30.0,
    "music": 40.0,
    "aggressive": 20.0,
}


def trim_silence(input_path: str, output_path: str, preset: str = "voice"):
    audio, sr = load_audio(input_path)  # (channels, samples)

    top_db = PRESETS.get(preset, 30.0)

    # Для определения границ используем моно
    mono = np.mean(audio, axis=0)

    intervals = librosa.effects.split(mono, top_db=top_db)
    if len(intervals) == 0:
        # Ничего не нашли, сохраняем как есть
        save_audio_stereo(audio, sr, output_path)
        return

    start = int(intervals[0][0])
    end = int(intervals[-1][1])

    trimmed = audio[:, start:end]
    save_audio_stereo(trimmed, sr, output_path)
