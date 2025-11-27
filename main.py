import os
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

from modules.normalize import normalize_lufs, normalize_peak
from modules.analyzer import analyze_file
from modules.channels import to_mono, to_stereo, swap_lr, ms_encode, ms_decode
from modules.trim_silence import trim_silence
from modules.format_converter import convert_format

app = FastAPI(title="Zenorax Backend API")
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Zenorax Backend API")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # можно потом сузить до конкретных доменов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


TMP_DIR = "/tmp/zenorax"
os.makedirs(TMP_DIR, exist_ok=True)


# -------- SAVE TEMP FILE --------
def save_upload_to_tmp(file: UploadFile) -> str:
    ext = Path(file.filename).suffix or ".bin"
    tmp_path = os.path.join(TMP_DIR, f"in_{uuid.uuid4().hex}{ext}")
    with open(tmp_path, "wb") as f:
        f.write(file.file.read())
    return tmp_path


# -------- ROOT --------
@app.get("/")
def root():
    return {"status": "ok", "service": "Zenorax Backend"}


# -------- NORMALIZE --------
@app.post("/normalize")
async def normalize(
    file: UploadFile = File(...),
    mode: str = Form("lufs"),
    target: float = Form(-14.0),
):
    input_path = save_upload_to_tmp(file)
    output_path = os.path.join(TMP_DIR, f"norm_{uuid.uuid4().hex}.wav")

    if mode == "lufs":
        normalize_lufs(input_path, output_path, target_lufs=target)
    else:
        normalize_peak(input_path, output_path, target_dbfs=target)

    return FileResponse(output_path, media_type="audio/wav", filename="normalized.wav")


# -------- FORMAT CONVERT --------
@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    format: str = Form("wav"),
    bitrate: int | None = Form(None),
):
    input_path = save_upload_to_tmp(file)
    tmp_out_base = os.path.join(TMP_DIR, f"conv_{uuid.uuid4().hex}")

    final_path = convert_format(input_path, tmp_out_base, codec=format, bitrate_kbps=bitrate)

    return FileResponse(final_path, filename=f"converted.{format}")


# -------- ANALYZE --------
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    input_path = save_upload_to_tmp(file)
    result = analyze_file(input_path)
    return JSONResponse(result)


# -------- CHANNELS --------
@app.post("/channels")
async def channels(
    file: UploadFile = File(...),
    mode: str = Form("mono"),
):
    input_path = save_upload_to_tmp(file)
    output_path = os.path.join(TMP_DIR, f"ch_{uuid.uuid4().hex}.wav")

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
        output_path = input_path

    return FileResponse(output_path, media_type="audio/wav")


# -------- TRIM SILENCE --------
@app.post("/trim")
async def trim(
    file: UploadFile = File(...),
    preset: str = Form("voice"),
):
    input_path = save_upload_to_tmp(file)
    output_path = os.path.join(TMP_DIR, f"trim_{uuid.uuid4().hex}.wav")

    trim_silence(input_path, output_path, preset=preset)

    return FileResponse(output_path, media_type="audio/wav", filename=f"trimmed.wav")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

