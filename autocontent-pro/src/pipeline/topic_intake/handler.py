import os, time, random, boto3

TABLE = os.getenv("CONTENT_TABLE")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE)

SEED = [
    "History of the Printing Press",
    "What is Quantum Entanglement?",
    "Top 5 Facts about Black Holes",
    "The Rise of Electric Vehicles",
    "Beginner's Guide to Healthy Sleep"
]

def lambda_handler(event, context):
    topic = random.choice(SEED)
    now = int(time.time())
    # De-dupe: do not repeat the same topic within ~3 days
    recent_cut = now - 3*24*3600
    # (Simplified: assume not repeating here)
    sk = f"req#{now}"
    table.put_item(Item={"topic": topic, "sk": sk, "status": "queued", "ts": now})
    return {"topic": topic, "request_id": sk}
