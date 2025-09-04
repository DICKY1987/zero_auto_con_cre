def lambda_handler(event, context):
    script = (event or {}).get("script", {}).get("script_text", "")
    ok = len(script.split()) > 12 and script.count("—") >= 2
    return {"ok": ok, "reason": None if ok else "Script too short or lacks facts bullets"}
