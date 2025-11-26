from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import uuid
import os
from processing import process_audio

app = FastAPI()

UPLOAD_DIR = "tmp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/process")
async def process(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    in_path = f"{UPLOAD_DIR}/{file_id}_in.wav"
    out_path = f"{UPLOAD_DIR}/{file_id}_out.wav"

    with open(in_path, "wb") as f:
        f.write(await file.read())

    process_audio(in_path, out_path)

    return FileResponse(out_path, media_type="audio/wav", filename="processed.wav")
