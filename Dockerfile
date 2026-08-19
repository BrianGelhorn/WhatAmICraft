FROM node:22-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip ca-certificates libnss3 libdbus-1-3 libatk1.0-0 libgbm-dev \
    libasound2 libxrandr2 libxkbcommon-dev libxfixes3 libxcomposite1 \
    libxdamage1 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages --no-cache-dir "yt-dlp[default]==2026.7.4"

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci && npx remotion browser ensure
COPY src ./src
COPY public ./public
COPY data ./data
COPY schemas ./schemas
COPY templates ./templates
COPY scripts ./scripts
COPY dashboard ./dashboard
COPY tsconfig.json remotion.config.ts ./

ENTRYPOINT ["python3", "scripts/produce_quiz_copy.py"]
CMD ["--all", "--render"]
