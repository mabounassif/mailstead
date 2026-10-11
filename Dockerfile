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

RUN SECRET_KEY=build-only DEBUG=1 RESEND_API_KEY=re_build MAIL_DOMAIN=build.invalid \
    ADMIN_RECOVERY_EMAIL=build@invalid DJANGO_SETTINGS_MODULE=core.settings \
    python manage.py collectstatic --noinput

RUN mkdir -p /data && chown mailstead:mailstead /data

# Start as root so mailstead.run can chown a freshly mounted volume, then drop privileges.
USER root

ENV DATA_ROOT=/data

EXPOSE 8000

CMD ["python", "-m", "mailstead.run"]
