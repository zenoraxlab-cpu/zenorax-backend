# modules/analyzer.py
import numpy as np
import soundfile as sf
import pyloudnorm as pyln


def analyze_file(path: str) -> dict:
    info = sf.info(path)
    data, sr = sf.read(path, always_2d=True)  # (samples, channels)

    samples, channels = data.shape
    duration = samples / sr

    # Преобразуем в float32 [-1, 1] на всякий случай
    x = data.astype("float32").T  # (channels, samples)

    peak = float(np.max(np.abs(x)))
    peak_dbfs = 20 * np.log10(peak + 1e-9)

    rms = float(np.sqrt(np.mean(x**2)))
    rms_dbfs = 20 * np.log10(rms + 1e-9)

    # LUFS по моно-сумме
    mono = np.mean(x, axis=0)
    meter = pyln.Meter(sr)
    lufs = float(meter.integrated_loudness(mono))

    clipping = bool(peak >= 0.999)

    return {
        "format": info.format,
        "subtype": info.subtype,
        "sample_rate": info.samplerate,
        "channels": channels,
        "frames": samples,
        "duration_sec": duration,
        "peak": peak,
        "peak_dbfs": peak_dbfs,
        "rms": rms,
        "rms_dbfs": rms_dbfs,
        "lufs": lufs,
        "clipping": clipping,
    }
