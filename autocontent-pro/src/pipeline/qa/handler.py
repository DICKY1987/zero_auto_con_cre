def lambda_handler(event, context):
    s=(event or {}).get('script',{}).get('script_text','')
    return {'ok': len(s.split())>10}
