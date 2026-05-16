import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Render persistent disk path check
    RENDER_DISK = "/opt/render/project/src/data_storage"
    if os.path.exists(RENDER_DISK):
        DATA_DIR = os.path.join(RENDER_DISK, "data")
        OUTPUT_DIR = os.path.join(RENDER_DISK, "output")
        CHROMA_DB_DIR = os.path.join(RENDER_DISK, "chroma_db")
    else:
        DATA_DIR = str(BASE_DIR / "data")
        OUTPUT_DIR = str(BASE_DIR / "output")
        CHROMA_DB_DIR = str(BASE_DIR / "chroma_db")

    # Ensure directories exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
