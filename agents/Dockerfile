FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV AGENTS_DATA_DIR=/data
ENV AGENTS_TMP_DIR=/tmp/agents
ENV TF_USE_LEGACY_KERAS=1

WORKDIR /srv/agents

RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /srv/agents/requirements.txt
RUN pip install --no-cache-dir -r /srv/agents/requirements.txt

COPY app /srv/agents/app

RUN mkdir -p /data /tmp/agents

EXPOSE 8010

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
