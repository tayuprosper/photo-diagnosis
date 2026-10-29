import os 
import tempfile

import anthropic
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from PIL import Image

from src.diagnose import diagnose

MAX_BYTES = 15 * 1024 * 1024

app = FastAPI()



@app.post("/diagnose")
def diagnose_photo(file: UploadFile = File(...), note: str = Form("")):
    raw = file.file.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, "This photos is larger than 5MB.")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".img") as tmp:
        tmp.write(raw)
        path = tmp.name
        
    try:
        try:
            Image.open(path).verify()
        except Exception:
            raise HTTPException(400, "That file is not JPG, PNG or WEBP photo.")
        try:
            return diagnose(path=path, note=note[:300])
        except RuntimeError as e:
            raise HTTPException(502, str(e))
        except anthropic.APIError:
            raise HTTPException(502, "The AI service returned and error. Check your key and credits.")
    finally:
        os.unlink(path)
        
        