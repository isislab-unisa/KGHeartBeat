FROM python:3.11-slim-bookworm AS wheels
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY docker/requirements.txt ./requirements.txt
COPY assessment_service/requirements.txt ./assessment-requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt -r assessment-requirements.txt

FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/src NLTK_DATA=/usr/local/share/nltk_data
COPY --from=wheels /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels \
    && python -m nltk.downloader -d /usr/local/share/nltk_data punkt punkt_tab
WORKDIR /app
COPY src/ ./src/
COPY monitoring_requests/ ./monitoring_requests/
COPY assessment_service/ ./assessment_service/
COPY ["Analysis results/csv_to_json.py", "/app/docker/csv_to_json.py"]
COPY docker/import_results.py ./docker/import_results.py
RUN mkdir -p '/app/Analysis results' /app/var \
    && python -c "import analyses, evaluate_fairness, evaluate_human_centered_acc, fromCSV_to_KG"
WORKDIR /app/src
CMD ["python", "manager.py"]
