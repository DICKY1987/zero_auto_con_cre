def simple_script(facts, duration_sec=60):
    intro = "Welcome! Today we explore: "
    body = "\n".join(f"- {f}" for f in facts)
    outro = "\nThanks for watching!"
    return f"{intro}\n{body}\n{outro}"

def lambda_handler(event, context):
    facts = (event or {}).get("research", {}).get("facts", [])
    script = simple_script(facts, 60)
    return {"script_text": script, "estimated_duration_sec": 60}
