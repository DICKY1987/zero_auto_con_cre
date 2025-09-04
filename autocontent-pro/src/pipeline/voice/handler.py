import os, boto3, uuid
ASSETS_BUCKET=os.getenv("ASSETS_BUCKET"); polly=boto3.client("polly"); s3=boto3.client("s3")
def lambda_handler(event, context):
    script=(event or {}).get("script",{}).get("script_text","Hello")
    r=polly.synthesize_speech(Text=script, VoiceId="Joanna", OutputFormat="mp3")
    key=f"audio/{uuid.uuid4()}.mp3"; s3.upload_fileobj(r["AudioStream"], ASSETS_BUCKET, key); return {"audio_s3_key": key}
