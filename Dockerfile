FROM cloakhq/cloakbrowser

ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 10000

CMD Xvfb :99 -screen 0 1280x800x24 -ac &>/dev/null & sleep 1 && uvicorn app:app --host 0.0.0.0 --port 10000
