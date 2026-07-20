import ffmpeg
from pathlib import Path
from config import settings

def extract_audio(video_path: Path, output_audio_path: Path):
    ffmpeg.input(str(video_path)).output(
        str(output_audio_path),
        acodec="pcm_s16le", ac=1, ar="16000"
    ).overwrite_output().run(quiet=True)

def merge_audio_video(video_path: Path, dub_audio_path: Path, output_path: Path):
    # Giảm âm thanh gốc xuống 15% khi có giọng lồng tiếng
    video = ffmpeg.input(str(video_path))
    orig_audio = video.audio.filter("volume", 0.15)
    dub_audio = ffmpeg.input(str(dub_audio_path)).audio
    mixed_audio = ffmpeg.filter([orig_audio, dub_audio], "amix", duration="shortest")
    
    ffmpeg.output(
        video.video, mixed_audio, str(output_path),
        vcodec="copy", acodec="aac", audio_bitrate="192k"
    ).overwrite_output().run(quiet=True)

def download_youtube_video(url: str, output_path: Path):
    import yt_dlp
    ydl_opts = {
        "format": "best[ext=mp4]",
        "outtmpl": str(output_path),
        "quiet": True,
        "no_warnings": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
