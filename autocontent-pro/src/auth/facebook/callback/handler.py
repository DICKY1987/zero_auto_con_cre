import os, boto3, requests, time

ssm = boto3.client("ssm")
ddb = boto3.resource("dynamodb")
tokens = ddb.Table(os.getenv("TOKENS_TABLE"))

def _param(n): return ssm.get_parameter(Name=n, WithDecryption=True)["Parameter"]["Value"]

def lambda_handler(event, context):
    qs = event.get("queryStringParameters") or {}
    code = qs.get("code")
    if not code: return {"statusCode":400, "body":"Missing code"}

    app_id = _param("/autocontent/facebook/app_id")
    app_secret = _param("/autocontent/facebook/app_secret")
    proto = event['headers'].get("x-forwarded-proto", "https")
    host = event['headers']['host']
    redirect_uri = f"{proto}://{host}/auth/facebook/callback"

    # Exchange code for short-lived token
    tok = requests.get("https://graph.facebook.com/v17.0/oauth/access_token", params={
        "client_id": app_id, "redirect_uri": redirect_uri, "client_secret": app_secret, "code": code
    }, timeout=15).json()

    user_token = tok.get("access_token")
    # Long-lived token
    long = requests.get("https://graph.facebook.com/v17.0/oauth/access_token", params={
        "grant_type": "fb_exchange_token", "client_id": app_id, "client_secret": app_secret, "fb_exchange_token": user_token
    }, timeout=15).json()
    long_token = long.get("access_token")

    # Get pages and take the first page (customize or extend portal to choose)
    pages = requests.get("https://graph.facebook.com/v17.0/me/accounts", params={
        "access_token": long_token
    }, timeout=15).json()

    page_id = None
    page_token = None
    data = pages.get("data", [])
    if data:
        page_id = data[0]["id"]
        page_token = data[0]["access_token"]

    tokens.put_item(Item={
        "provider": "facebook",
        "tokens": {"user_access_token": long_token, "page_id": page_id, "page_access_token": page_token},
        "updated": int(time.time())
    })

    return {"statusCode": 200, "headers": {"Content-Type":"text/html"}, "body": "<h3>Facebook connected. Page selected automatically.</h3>"}
