import os, json, boto3

region = os.getenv("AWS_REGION") or os.getenv("ParamRegion", "us-east-1")

ssm = boto3.client("ssm", region_name=region)
cf = boto3.client("cloudformation", region_name=region)
sfn = boto3.client("stepfunctions", region_name=region)

stack_name = "autocontent-pro"
stacks = cf.describe_stacks(StackName=stack_name)["Stacks"][0]
outputs = {o["OutputKey"]: o["OutputValue"] for o in stacks.get("Outputs", [])}
state_machine_arn = outputs.get("StateMachineArn")

def put(name, val):
    if val:
        ssm.put_parameter(Name=name, Value=val, Type="SecureString", Overwrite=True)

put("/autocontent/youtube/client_id", os.getenv("YOUTUBE_CLIENT_ID", ""))
put("/autocontent/youtube/client_secret", os.getenv("YOUTUBE_CLIENT_SECRET", ""))

if state_machine_arn:
    sfn.start_execution(stateMachineArn=state_machine_arn, input=json.dumps({}))
    print("Started first execution:", state_machine_arn)
