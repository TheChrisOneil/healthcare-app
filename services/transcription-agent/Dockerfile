FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Add this to your Dockerfile; this will create a directory in the container to store the audio recordings.
RUN mkdir -p /app/storage/recordings && chmod 777 /app/storage/recordings
RUN mkdir -p /app/storage/transcriptions && chmod 777 /app/storage/transcriptions
# debug
COPY test_audio.pcm /app/test_audio.pcm

EXPOSE 8000

CMD ["python", "transcription_agent.py"]
