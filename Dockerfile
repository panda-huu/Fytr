# Use latest Alpine with Python 3.11 (or upgrade to 3.12 if you prefer)
FROM python:3.11-alpine3.20

# Install required system packages (ffmpeg + opus + sodium + build tools)
RUN apk update && apk upgrade && \
    apk add --no-cache \
        ffmpeg \
        opus-dev \
        libsodium-dev \
        gcc \
        musl-dev \
        python3-dev \
        libffi-dev \
        make \
    && rm -rf /var/cache/apk/*

WORKDIR /app

# Upgrade pip & install the correct packages
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
        pyrogram \
        tgcrypto \
        py-tgcalls \
    && pip cache purge

# Copy your bot code
COPY main.py .

# Environment variables (fill these via docker-compose or --env)
ENV API_ID="" \
    API_HASH="" \
    SESSION_STRING="" \
    TZ=Asia/Kolkata

CMD ["python", "main.py"]
