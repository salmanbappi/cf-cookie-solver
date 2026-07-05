FROM cloakhq/cloakbrowser

ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 10000

# Use their entrypoint (starts Xvfb + sets DISPLAY=:99), pass uvicorn as CMD
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
