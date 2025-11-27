# modules/helpers.py
import numpy as np
import soundfile as sf
import librosa
from pathlib import Path


def load_audio(path: str):
    """
    Загружает аудио любым форматом в numpy.
    Возвращает (audio: np.ndarray[channels, samples], sr: int).
    """
    # librosa.load с mono=False → (n,) или (channels, n)
    audio, sr = librosa.load(path, sr=None, mono=False)

    if audio.ndim == 1:
        audio = np.expand_dims(audio, axis=0)  # (1, N)

    return audio.astype(np.float32), sr


def save_audio_stereo(audio: np.ndarray, sr: int, path: str):
    """
    Сохраняет (channels, samples) как стерео/моно WAV float32.
    """
    if audio.ndim == 1:
        audio = np.expand_dims(audio, axis=0)

    # (channels, samples) → (samples, channels)
    audio_out = audio.T.astype(np.float32)
    sf.write(path, audio_out, sr, subtype="FLOAT")


def ensure_stereo(audio: np.ndarray) -> np.ndarray:
    """
    Если сигнал моно (1, N) → дублируем в стерео.
    """
    if audio.ndim == 1:
        audio = np.expand_dims(audio, axis=0)

    if audio.shape[0] == 1:
        audio = np.vstack([audio, audio])
    return audio


def calc_peak_dbfs(audio: np.ndarray) -> float:
    peak = np.max(np.abs(audio)) + 1e-9
    return 20.0 * np.log10(peak)


def db_to_lin(db: float) -> float:
    return 10.0 ** (db / 20.0)
