def lambda_handler(event, context):
    topic = (event or {}).get("topic", {}).get("topic", "General Topic")
    facts = [f"{topic} — fact 1 (placeholder).", f"{topic} — fact 2 (placeholder).", f"{topic} — fact 3 (placeholder)."]
    return {"facts": facts, "sources": ["https://example.com/source1"]}
