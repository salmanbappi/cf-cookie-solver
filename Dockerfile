FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    wget gnupg2 xvfb curl \
    fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnspr4 libnss3 libvulkan1 libxcomposite1 libxdamage1 libxfixes3 \
    libxkbcommon0 libxrandr2 xdg-utils \
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb || apt-get -f install -y \
    && rm google-chrome-stable_current_amd64.deb \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD Xvfb :99 -screen 0 1280x800x24 -ac &>/dev/null & sleep 2 && uvicorn app:app --host 0.0.0.0 --port 10000
