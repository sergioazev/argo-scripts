FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    mediainfo \
    mediaconch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/ /app/
RUN pip install --no-cache-dir flask watchdog

EXPOSE 8787
CMD ["python", "server.py"]
