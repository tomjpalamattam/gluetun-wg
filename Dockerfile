FROM python:3.12-slim-bookworm

# System deps for Playwright + Xvfb + Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    curl \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    wget \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright's Chromium browser + its OS deps
RUN playwright install chromium
RUN playwright install-deps chromium

COPY download_config.py watchdog.py entrypoint.sh ./
RUN chmod +x entrypoint.sh

# /output is where the freshly downloaded wg0.conf gets written;
# mount this to the same host path gluetun's wireguard volume uses.
VOLUME ["/output"]

ENTRYPOINT ["./entrypoint.sh"]
