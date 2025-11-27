# modules/channels.py
import numpy as np

from .helpers import load_audio, save_audio_stereo, ensure_stereo


def to_mono(input_path: str, output_path: str):
    audio, sr = load_audio(input_path)  # (channels, samples)
    mono = np.mean(audio, axis=0, keepdims=True)  # (1, samples)
    save_audio_stereo(mono, sr, output_path)


def to_stereo(input_path: str, output_path: str):
    audio, sr = load_audio(input_path)  # (channels, samples)
    if audio.shape[0] == 1:
        audio = np.vstack([audio, audio])
    save_audio_stereo(audio, sr, output_path)


def swap_lr(input_path: str, output_path: str):
    audio, sr = load_audio(input_path)
    audio = ensure_stereo(audio)

    L, R = audio[0].copy(), audio[1].copy()
    audio_swapped = np.vstack([R, L])
    save_audio_stereo(audio_swapped, sr, output_path)


def ms_encode(input_path: str, output_path: str):
    audio, sr = load_audio(input_path)
    audio = ensure_stereo(audio)
    L, R = audio[0], audio[1]

    M = (L + R) / 2.0
    S = (L - R) / 2.0

    out = np.vstack([M, S])
    save_audio_stereo(out, sr, output_path)


def ms_decode(input_path: str, output_path: str):
    audio, sr = load_audio(input_path)
    audio = ensure_stereo(audio)
    M, S = audio[0], audio[1]

    L = M + S
    R = M - S

    out = np.vstack([L, R])
    # Нормализация, чтобы не вылететь по пику
    peak = np.max(np.abs(out)) + 1e-9
    if peak > 1.0:
        out = out / peak
    save_audio_stereo(out, sr, output_path)
