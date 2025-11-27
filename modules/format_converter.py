# modules/format_converter.py
import subprocess
from pathlib import Path


def convert_format(input_path: str, output_path: str, codec: str, bitrate_kbps: int | None = None):
    """
    codec: "wav" | "mp3" | "flac" | "aac"
    bitrate_kbps: для сжатых форматов (mp3/aac)
    """
    out_ext = codec.lower()
    output_path = str(Path(output_path).with_suffix(f".{out_ext}"))

    cmd = ["ffmpeg", "-y", "-i", input_path]

    if codec in ("mp3", "aac") and bitrate_kbps is not None:
        cmd += ["-b:a", f"{bitrate_kbps}k"]

    # Простейший вариант: ffmpeg сам подберёт кодек по расширению
    cmd.append(output_path)

    subprocess.run(cmd, check=True)

    return output_path
