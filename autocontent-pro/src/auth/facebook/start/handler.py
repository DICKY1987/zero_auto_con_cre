import os, urllib.parse, boto3, secrets

ssm = boto3.client("ssm")
def _param(n): return ssm.get_parameter(Name=n, WithDecryption=True)["Parameter"]["Value"]

def lambda_handler(event, context):
    app_id = _param("/autocontent/facebook/app_id")
    proto = event['headers'].get("x-forwarded-proto", "https")
    host = event['headers']['host']
    redirect_uri = f"{proto}://{host}/auth/facebook/callback"
    state = secrets.token_urlsafe(16)
    scope = ",".join(["pages_show_list","pages_read_engagement","pages_manage_posts","pages_read_user_content","instagram_basic","instagram_content_publish"])
    auth_url = "https://www.facebook.com/v17.0/dialog/oauth?" + urllib.parse.urlencode({
        "client_id": app_id, "redirect_uri": redirect_uri, "state": state, "scope": scope
    })
    return {"statusCode": 302, "headers": {"Location": auth_url}}
