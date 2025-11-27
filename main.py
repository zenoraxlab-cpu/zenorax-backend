# main.py
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

from modules.normalize import normalize_lufs, normalize_peak
from modules.analyzer import analyze_file
from modules.channels import (
    to_mono,
    to_stereo,
    swap_lr,
    ms_encode,
    ms_decode,
)
from modules.trim_silence import trim_silence
from modules.format_converter import convert_format

app = FastAPI(title="Zenorax Backend – Utilities")

TMP_DIR = "/tmp/zenorax"
os.makedirs(TMP_DIR, exist_ok=True)


def save_upload_to_tmp(file: UploadFile) -> str:
    ext = Path(file.filename).suffix or ".bin"
    tmp_path = os.path.join(TMP_DIR, f"in_{uuid.uuid4().hex}{ext}")
    with open(tmp_path, "wb") as f:
        f.write(file.file.read())
    return tmp_path


# ---------- 1. Normalization ----------

@app.post("/normalize")
async def normalize(
    file: UploadFile = File(...),
    mode: str = Form("lufs"),          # "lufs" | "peak"
    target: float = Form(-14.0),       # -14 LUFS или -6/-12 dBFS
):
    input_path = save_upload_to_tmp(file)
    output_path = os.path.join(TMP_DIR, f"out_{uuid.uuid4().hex}.wav")

    if mode == "lufs":
        normalize_lufs(input_path, output_path, target_lufs=target)
    else:
        normalize_peak(input_path, output_path, target_dbfs=target)

    return FileResponse(
        output_path,
        media_type="audio/wav",
        filename="normalized.wav",
    )


# ---------- 2. Format Converter ----------

@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    format: str = Form("wav"),
    bitrate: int | None = Form(None),
):
    input_path = save_upload_to_tmp(file)
    tmp_out_base = os.path.join(TMP_DIR, f"out_{uuid.uuid4().hex}")

    final_path = convert_format(input_path, tmp_out_base, codec=format, bitrate_kbps=bitrate)

    # media_type можно уточнять по формату, пока используем generic
    return FileResponse(
        final_path,
        media_type="application/octet-stream",
        filename=f"converted.{format}",
    )


# ---------- 3. File Analyzer ----------

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    input_path = save_upload_to_tmp(file)
    result = analyze_file(input_path)
    return JSONResponse(result)


# ---------- 4. Stereo / Mono & Channels ----------

@app.post("/channels")
async def channels(
    file: UploadFile = File(...),
    mode: str = Form("mono"),   # "mono" | "stereo" | "swap" | "ms_encode" | "ms_decode"
):
    input_path = save_upload_to_tmp(file)
    output_path = os.path.join(TMP_DIR, f"out_{uuid.uuid4().hex}.wav")

    if mode == "mono":
        to_mono(input_path, output_path)
    elif mode == "stereo":
        to_stereo(input_path, output_path)
    elif mode == "swap":
        swap_lr(input_path, output_path)
    elif mode == "ms_encode":
        ms_encode(input_path, output_path)
    elif mode == "ms_decode":
        ms_decode(input_path, output_path)
    else:
        # по умолчанию вернём исходный
        output_path = input_path

    return FileResponse(
        output_path,
        media_type="audio/wav",
        filename=f"channels_{mode}.wav",
    )


# ---------- 5. Trim Silence ----------

@app.post("/trim")
async def trim(
    file: UploadFile = File(...),
    preset: str = Form("voice"),   # "voice" | "music" | "aggressive"
):
    input_path = save_upload_to_tmp(file)
    output_path = os.path.join(TMP_DIR, f"out_{uuid.uuid4().hex}.wav")

    trim_silence(input_path, output_path, preset=preset)

    return FileResponse(
        output_path,
        media_type="audio/wav",
        filename=f"trimmed_{preset}.wav",
    )
    # ---------- 6. Universal PROCESS endpoint (for Next.js frontend) ----------

from pydantic import BaseModel
from datetime import datetime
import uuid

class HistoryItem(BaseModel):
    id: str
    filename: str
    tool: str
    date: str
    status: str
    download_url: str | None

HISTORY = {}


@app.post("/process")
async def process_file(
    file: UploadFile = File(...),
    tool: str = Form("basic"),
    mode: str = Form(None),
    preset: str = Form(None),
    bitrate: int | None = Form(None),
    user_id: str = Form("guest"),
):
    """
    UNIVERSAL ENTRY POINT
    Этот endpoint вызывается frontend'ом.
    Он перенаправляет файл в нужный модуль.
    """

    input_path = save_upload_to_tmp(file)
    output_path = os.path.join(TMP_DIR, f"out_{uuid.uuid4().hex}.wav")

    # --- ROUTES FOR TOOLS ---

    # Normalization
    if tool == "normalization":
        if mode == "peak":
            normalize_peak(input_path, output_path, target_dbfs=-6)
        else:
            normalize_lufs(input_path, output_path, target_lufs=-14)

    # Trim Silence
    elif tool == "trim":
        trim_silence(input_path, output_path, preset=preset or "voice")

    # Channels
    elif tool == "channels":
        if mode == "mono":
            to_mono(input_path, output_path)
        elif mode == "stereo":
            to_stereo(input_path, output_path)
        elif mode == "swap":
            swap_lr(input_path, output_path)
        elif mode == "ms_encode":
            ms_encode(input_path, output_path)
        elif mode == "ms_decode":
            ms_decode(input_path, output_path)

    # Format convert
    elif tool == "convert":
        final_path = convert_format(input_path, output_path.replace(".wav", ""), codec=mode or "wav", bitrate_kbps=bitrate)
        output_path = final_path

    # Simple copy for tools "basic"
    else:
        # если инструмент неизвестен — возвращаем файл как есть
        output_path = input_path

    # --- HISTORY SAVE ---
    item = HistoryItem(
        id=str(uuid.uuid4()),
        filename=file.filename,
        tool=tool,
        date=datetime.utcnow().isoformat(),
        status="done",
        download_url=None,   # TODO: когда сделаем CDN
    )

    if user_id not in HISTORY:
        HISTORY[user_id] = []
    HISTORY[user_id].append(item)

    return FileResponse(
        output_path,
        media_type="audio/wav",
        filename=f"{tool}.wav"
    )
@app.get("/history/{user_id}")
def get_history(user_id: str):
    return HISTORY.get(user_id, [])

@app.get("/")
def root():
    return {"status": "ok"}
