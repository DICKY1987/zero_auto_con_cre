import os, uuid, boto3, tempfile
from moviepy.editor import TextClip, CompositeVideoClip, ColorClip, AudioFileClip
ASSETS_BUCKET=os.getenv("ASSETS_BUCKET"); s3=boto3.client("s3")
def _compose(script, audio_path, size):
    w,h=size; bg=ColorClip(size=(w,h), color=(10,10,10), duration=60)
    txt=TextClip(script, fontsize=48, color='white', size=(w-120,h-120), method='caption').set_duration(60).set_position('center')
    v=CompositeVideoClip([bg,txt])
    if audio_path and os.path.exists(audio_path):
        a=AudioFileClip(audio_path); v=v.set_audio(a).set_duration(min(v.duration,a.duration))
    return v
def _render(v):
    out=os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp4")
    v.write_videofile(out, fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None); return out
def lambda_handler(event, context):
    script=(event or {}).get("script",{}).get("script_text","Hello")
    audio_key=(event or {}).get("voice",{}).get("audio_s3_key")
    ap=None
    if audio_key:
        ap=os.path.join(tempfile.gettempdir(),"voice.mp3"); s3.download_file(ASSETS_BUCKET, audio_key, ap)
    v916=_compose(script,ap,(1080,1920)); p916=_render(v916); k916=f"videos/{os.path.basename(p916)}"; s3.upload_file(p916,ASSETS_BUCKET,k916)
    v169=_compose(script,ap,(1920,1080)); p169=_render(v169); k169=f"videos/{os.path.basename(p169)}"; s3.upload_file(p169,ASSETS_BUCKET,k169)
    return {"video_portrait_s3_key": k916, "video_landscape_s3_key": k169}
