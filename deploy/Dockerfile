FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY bingomate /app/bingomate
COPY edge_lab /app/edge_lab
COPY apps /app/apps
COPY configs /app/configs
COPY scripts /app/scripts

RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -e .

EXPOSE 8090
CMD ["bingomate-api", "--host", "0.0.0.0", "--port", "8090"]
