import os
import asyncio
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from utils.helpers import generate_unique_id, cleanup_temp_files, task_status
from services.video_processor import extract_audio, merge_audio_video, download_youtube_video
from services.transcriber import transcribe_and_translate
from services.voice_synthesizer import generate_dub_audio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo tác vụ dọn dẹp tự động
    cleanup_task = asyncio.create_task(cleanup_temp_files())
    yield
    cleanup_task.cancel()
    await cleanup_task

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"]
)

async def process_video_task(task_id: str, video_path: Path):
    try:
        task_status[task_id] = {"status": "processing", "step": "Đang trích xuất âm thanh..."}
        
        audio_path = settings.UPLOAD_DIR / f"{task_id}_audio.wav"
        extract_audio(video_path, audio_path)

        task_status[task_id]["step"] = "Đang tạo phụ đề & dịch tiếng Việt..."
        srt_content, segments = transcribe_and_translate(audio_path)
        srt_path = settings.OUTPUT_DIR / f"{task_id}_subtitle.srt"
        srt_path.write_text(srt_content, encoding="utf-8")

        task_status[task_id]["step"] = "Đang tạo giọng lồng tiếng AI..."
        dub_path = settings.UPLOAD_DIR / f"{task_id}_dub.aac"
        await generate_dub_audio(segments, dub_path)

        task_status[task_id]["step"] = "Đang ghép video & âm thanh..."
        final_path = settings.OUTPUT_DIR / f"{task_id}_dubbed.mp4"
        merge_audio_video(video_path, dub_path, final_path)

        task_status[task_id] = {
            "status": "completed",
            "video_url": f"/api/download/{final_path.name}",
            "srt_url": f"/api/download/{srt_path.name}"
        }

    except Exception as e:
        task_status[task_id] = {"status": "error", "message": str(e)}
    finally:
        # Xóa file tạm xử lý
        for f in [audio_path, dub_path, video_path]:
            f.unlink(missing_ok=True)

# Endpoint tải lên file
@app.post("/api/upload")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(400, "File không được vượt quá 100MB")
    if not file.filename.lower().endswith((".mp4", ".mkv", ".mov", ".avi")):
        raise HTTPException(400, "Chỉ hỗ trợ định dạng MP4, MKV, MOV, AVI")

    task_id = generate_unique_id()
    save_path = settings.UPLOAD_DIR / f"{task_id}_orig{Path(file.filename).suffix}"
    
    with save_path.open("wb") as f:
        f.write(await file.read())

    background_tasks.add_task(process_video_task, task_id, save_path)
    return {"task_id": task_id}

# Endpoint xử lý link YouTube/Drive
@app.post("/api/process-url")
async def process_url(background_tasks: BackgroundTasks, url: str = Form(...)):
    if not any(x in url for x in ["youtube.com", "youtu.be", "drive.google.com"]):
        raise HTTPException(400, "Chỉ hỗ trợ link YouTube hoặc Google Drive công khai")

    task_id = generate_unique_id()
    save_path = settings.UPLOAD_DIR / f"{task_id}_orig.mp4"
    
    try:
        download_youtube_video(url, save_path)
    except Exception as e:
        raise HTTPException(400, f"Không tải được video: {str(e)}")

    background_tasks.add_task(process_video_task, task_id, save_path)
    return {"task_id": task_id}

# Kiểm tra trạng thái
@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    return task_status.get(task_id, {"status": "error", "message": "Không tìm thấy tác vụ"})

# Tải kết quả
@app.get("/api/download/{filename}")
async def download_file(filename: str):
    file_path = settings.OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(404, "File không tồn tại")
    return FileResponse(file_path, filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
