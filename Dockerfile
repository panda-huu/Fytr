# Use slim Alpine-based Python 3.11 (small + fast)
FROM python:3.11-alpine3.19

# Install system dependencies (ffmpeg, opus, libsodium + build tools)
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

# Set working directory
WORKDIR /app

# Upgrade pip & install core packages
# Use latest compatible versions (adjust if needed after pip check)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
        pyrogram \
        tgcrypto \
        pytgcalls \
        # Optional: if you use numpy/pydub/etc in filters
        # pydub \
        # numpy \
    && pip cache purge

# Copy only your code (don't copy session string in image!)
COPY main.py .

# Important: NEVER put SESSION_STRING in Dockerfile or image
# Instead → use environment variables or mounted file
ENV API_ID="" \
    API_HASH="" \
    SESSION_STRING="" \
    # Optional: timezone if you want logs in IST
    TZ=Asia/Kolkata

# For microphone input in Docker → host must share audio device (not always easy)
# If testing with test tone only → no extra flags needed

# Run the bot
CMD ["python", "main.py"]
