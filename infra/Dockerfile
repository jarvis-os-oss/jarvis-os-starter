# JARVIS-OS cockpit dashboard container.
# Minimal, dependency-light image for the Flask cockpit skeleton. Agent
# gateways run via the Hermes runtime (out of scope for this image); this
# container serves the read-only cockpit UI + API.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    AIOS_HOME=/opt/aios \
    COCKPIT_PORT=8517

WORKDIR /opt/aios

# System deps kept minimal: curl for the healthcheck only.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY dashboard/requirements.txt /opt/aios/dashboard/requirements.txt
RUN pip install --no-cache-dir -r /opt/aios/dashboard/requirements.txt

COPY . /opt/aios

EXPOSE 8517

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${COCKPIT_PORT}/api/health" || exit 1

CMD ["python", "dashboard/app.py"]
