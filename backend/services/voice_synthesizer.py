import edge_tts
import asyncio
from pathlib import Path
from config import settings

async def generate_dub_audio(segments: list, output_path: Path):
    communicate = edge_tts.Communicate(voice=settings.VOICE_NAME)
    audio_chunks = []
    temp_mp3 = output_path.with_suffix(".mp3")

    for seg in segments:
        if not seg["text"].strip():
            continue
        temp_chunk = output_path.parent / f"chunk_{seg['id']}.mp3"
        await communicate.save(seg["text"], str(temp_chunk))
        audio_chunks.append((temp_chunk, seg["start"]))

    # Ghép audio khớp thời gian
    with open(output_path.parent / "concat.txt", "w", encoding="utf-8") as f:
        for idx, (chunk, start) in enumerate(audio_chunks):
            f.write(f"file '{chunk.resolve()}'\n")
            if idx < len(audio_chunks)-1:
                next_start = audio_chunks[idx+1][1]
                silence = next_start - start - 2  # Trừ thời gian nói ước tính
                if silence > 0:
                    f.write(f"file 'anullsrc=cl=mono=r=24000:d={silence}'\n")

    import ffmpeg
    ffmpeg.input(
        str(output_path.parent / "concat.txt"),
        format="concat", safe=0
    ).output(str(output_path), acodec="aac", ar="24000").overwrite_output().run(quiet=True)

    # Dọn file tạm
    for chunk, _ in audio_chunks:
        chunk.unlink(missing_ok=True)
    (output_path.parent / "concat.txt").unlink(missing_ok=True)
