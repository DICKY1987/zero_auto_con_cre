def lambda_handler(event, context):
    facts = (event or {}).get("research", {}).get("facts", [])
    script = "Welcome! Today we explore:\n" + "\n".join(f"- {f}" for f in facts) + "\nThanks for watching!"
    return {"script_text": script, "estimated_duration_sec": 60}
