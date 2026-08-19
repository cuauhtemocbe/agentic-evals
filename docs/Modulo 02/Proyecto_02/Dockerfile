FROM python:3.13-slim AS base

WORKDIR /app

# --- Builder stage: resuelve e instala dependencias de runtime en un venv.
# Solo este stage necesita poetry — production copia el venv ya armado. ---
FROM base AS builder

RUN pip install --no-cache-dir poetry==1.8.4
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main --no-interaction

# --- Production image: solo artefactos de runtime, sin poetry. ---
FROM python:3.13-slim AS production

WORKDIR /app

RUN addgroup --system appuser \
    && adduser --system --ingroup appuser --home /home/appuser appuser \
    && mkdir -p /home/appuser \
    && chown -R appuser:appuser /home/appuser

# pip viene en la imagen base pero no se usa en runtime (las deps ya están
# instaladas en el venv copiado de builder) — sacarlo evita cargar sus CVEs.
RUN python -m pip uninstall -y pip

COPY --from=builder /app/.venv /app/.venv
COPY --chown=appuser:appuser . .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    HOME=/home/appuser \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8501}/_stcore/health')" || exit 1

CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless true"]
