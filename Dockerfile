FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --system mailstead && useradd --system --gid mailstead --create-home mailstead

WORKDIR /app

COPY pyproject.toml manage.py ./
COPY mailstead ./mailstead
COPY core ./core
COPY accounts ./accounts
COPY jobs ./jobs
COPY mail ./mail
COPY provider ./provider
COPY storage ./storage
COPY enterprise ./enterprise
COPY templates ./templates

RUN pip install --upgrade pip && pip install .

RUN mkdir -p /data && chown mailstead:mailstead /data

USER mailstead

ENV DATA_ROOT=/data \
    GUNICORN_BIND=0.0.0.0:8000

EXPOSE 8000

CMD ["python", "-m", "mailstead.run"]
