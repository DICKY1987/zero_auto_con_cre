FROM public.ecr.aws/lambda/python:3.12

# Minimal deps (moviepy pulls ffmpeg via image if present; we rely on container ffmpeg availability)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./

CMD [ "main.lambda_handler" ]
