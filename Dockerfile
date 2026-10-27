FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py crypto.py ./
COPY templates/ templates/
COPY static/ static/

RUN useradd --system --uid 10001 app \
    && mkdir -p /app/instance \
    && chown app:app /app/instance

USER app
EXPOSE 5000

CMD ["python", "app.py"]
