import os, urllib.parse, boto3

ssm = boto3.client("ssm")

def _param(name):
    return ssm.get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"]

def lambda_handler(event, context):
    client_id = _param("/autocontent/youtube/client_id")
    proto = event['headers'].get("x-forwarded-proto", "https")
    host = event['headers']['host']
    redirect_uri = f"{proto}://{host}/auth/youtube/callback"
    scope = "https://www.googleapis.com/auth/youtube.upload"
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "access_type": "offline",
        "prompt": "consent"
    })
    return {"statusCode": 302, "headers": {"Location": auth_url}}
