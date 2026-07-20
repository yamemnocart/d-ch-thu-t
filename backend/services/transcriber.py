import whisper
from pathlib import Path
from config import settings

model = whisper.load_model(settings.WHISPER_MODEL)

def transcribe_and_translate(audio_path: Path) -> str:
    # Nhận diện + dịch trực tiếp sang tiếng Việt
    result = model.transcribe(
        str(audio_path),
        task="translate",
        language="en",
        target_language="vi"
    )

    # Tạo định dạng SRT chuẩn
    srt_content = ""
    for idx, seg in enumerate(result["segments"], 1):
        start = f"{int(seg['start']//3600):02d}:{int((seg['start']%3600)//60):02d}:{int(seg['start']%60):02d},{int((seg['start']%1)*1000):03d}"
        end = f"{int(seg['end']//3600):02d}:{int((seg['end']%3600)//60):02d}:{int(seg['end']%60):02d},{int((seg['end']%1)*1000):03d}"
        srt_content += f"{idx}\n{start} --> {end}\n{seg['text'].strip()}\n\n"
    
    return srt_content, result["segments"]
