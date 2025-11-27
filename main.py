# main.py
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

# modules (твои модули)
from modules.normalize import normalize_lufs, normalize_peak
from modules.analyzer import analyze_file
from modules.channels import to_mono, to_stereo, swap_lr, ms_encode, ms_decode
from modules.trim_silence import trim_silence
from modules.format_converter import convert_format

# ========== HISTORY ==========
from pydantic import BaseModel
from datetime import datetime

class HistoryItem(BaseModel):
    id: str
    filename: str
    tool: str
    date: str
    status: str
    download_url: str | None

HISTORY = {}

# ========== APP INIT ==========
app = FastAPI(title="Zenorax Backend – Utilities")
TMP_DIR = "/tmp/zenorax"
os.makedirs(TMP_DIR, exist_ok=True)


# ========== UTILS ==========
def save_upload_to_tmp(file: UploadFile) -> str:
    ext = Path(file.filename).suffix or ".bin"
    tmp_path = os.path.join(TMP_DIR, f"in_{uuid.uuid4().hex}{ext}")
    with open(tmp_path, "wb") as f:
        f.write(file.file.read())
    return tmp_path


# =====================================================
# 6. UNIVERSAL PROCESS ENDPOINT (Frontend → Backend)
# =====================================================

@app.post("/process")
async def process_file(
    file: UploadFile = File(...),
    tool: str = Form("basic"),    # инструмент
    mode: str = Form(None),       # режимы внутри инструмента
    preset: str = Form(None),     # пресеты
    bitrate: int | None = Form(None),
    user_id: str = Form("guest"), # later replace with real auth
):
    input_path = save_upload_to_tmp(file)
    output_path = os.path.join(TMP_DIR, f"out_{uuid.uuid4().hex}.wav")

    # --- Normalization ---
    if tool == "normalization":
        if mode == "peak":
            normalize_peak(input_path, output_path, target_dbfs=-6)
        else:
            normalize_lufs(input_path, output_path, target_lufs=-14)

    # --- Trim Silence ---
    elif tool == "trim":
        trim_silence(input_path, output_path, preset=preset or "voice")

    # --- Channels ---
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

    # --- Format convert ---
    elif tool == "convert":
        final_path = convert_format(
            input_path,
            output_path.replace(".wav", ""),
            codec=mode or "wav",
            bitrate_kbps=bitrate
        )
        output_path = final_path

    # --- Basic (copy input) ---
    else:
        output_path = input_path

    # ========== SAVE HISTORY ==========
    item = HistoryItem(
        id=str(uuid.uuid4()),
        filename=file.filename,
        tool=tool,
        date=datetime.utcnow().isoformat(),
        status="done",
        download_url=None,
    )

    if user_id not in HISTORY:
        HISTORY[user_id] = []
    HISTORY[user_id].append(item)

    return FileResponse(
        output_path,
        media_type="audio/wav",
        filename=f"{tool}.wav"
    )


# =====================================================
# 7. HISTORY ENDPOINT
# =====================================================

@app.get("/history/{user_id}")
def get_history(user_id: str):
    return HISTORY.get(user_id, [])


# =====================================================
# 0. ROOT
# =====================================================

@app.get("/")
def root():
    return {"status": "ok"}
