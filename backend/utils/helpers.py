import uuid
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from config import settings

def generate_unique_id() -> str:
    return str(uuid.uuid4())[:12]

async def cleanup_temp_files():
    while True:
        cutoff = datetime.now() - timedelta(minutes=settings.TEMP_FILE_EXPIRE_MINUTES)
        for folder in [settings.UPLOAD_DIR, settings.OUTPUT_DIR]:
            for file in folder.glob("*.*"):
                if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
                    try:
                        file.unlink()
                    except:
                        pass
        await asyncio.sleep(60)

# Lưu trạng thái tác vụ
task_status = {}
