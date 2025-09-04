import os, uuid, boto3, tempfile, math
from moviepy.editor import TextClip, CompositeVideoClip, ColorClip, AudioFileClip

ASSETS_BUCKET = os.getenv("ASSETS_BUCKET")
s3 = boto3.client("s3")

def _compose(script, audio_path, size):
    w, h = size
    duration = 60
    bg = ColorClip(size=(w, h), color=(10, 10, 10), duration=duration)
    txt = TextClip(script, fontsize=48, color='white', size=(w-120, h-120), method='caption').set_duration(duration).set_position('center')
    video = CompositeVideoClip([bg, txt])
    if audio_path and os.path.exists(audio_path):
        audio = AudioFileClip(audio_path)
        duration = min(video.duration, audio.duration)
        video = video.set_audio(audio).set_duration(duration)
    return video

def _render_and_upload(video):
    out_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp4")
    video.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
    key = f"videos/{os.path.basename(out_path)}"
    s3.upload_file(out_path, ASSETS_BUCKET, key)
    return key

def lambda_handler(event, context):
    script = (event or {}).get("script", {}).get("script_text", "Hello from AutoContent Pro.")
    audio_key = (event or {}).get("voice", {}).get("audio_s3_key")

    audio_path = None
    if audio_key:
        audio_path = os.path.join(tempfile.gettempdir(), "voice.mp3")
        s3.download_file(ASSETS_BUCKET, audio_key, audio_path)

    video_916 = _compose(script, audio_path, (1080, 1920))
    key_916 = _render_and_upload(video_916)

    video_169 = _compose(script, audio_path, (1920, 1080))
    key_169 = _render_and_upload(video_169)

    return {"video_portrait_s3_key": key_916, "video_landscape_s3_key": key_169}
