# modules/normalize.py
import numpy as np
import pyloudnorm as pyln

from .helpers import load_audio, save_audio_stereo, db_to_lin


def normalize_lufs(input_path: str, output_path: str, target_lufs: float = -14.0):
    audio, sr = load_audio(input_path)  # (channels, samples)

    # Для измерения делаем моно
    mono = np.mean(audio, axis=0)

    meter = pyln.Meter(sr)
    loudness = meter.integrated_loudness(mono)

    # Нормализация по громкости
    loudness_normalized = pyln.normalize.loudness(mono, loudness, target_lufs)

    # Применяем коэффициент к всем каналам, рассчитанный по отношению
    gain = np.max(np.abs(loudness_normalized)) / (np.max(np.abs(mono)) + 1e-9)

    audio_norm = audio * gain
    save_audio_stereo(audio_norm, sr, output_path)


def normalize_peak(input_path: str, output_path: str, target_dbfs: float = -6.0):
    audio, sr = load_audio(input_path)

    peak = np.max(np.abs(audio)) + 1e-9
    target_lin = db_to_lin(target_dbfs)

    gain = target_lin / peak
    audio_norm = audio * gain

    save_audio_stereo(audio_norm, sr, output_path)
