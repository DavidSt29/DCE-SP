# ==========================================
# Dockerfile for Python Flask Backend
# ==========================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed for healthcheck and PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source code
COPY . ./

EXPOSE 5000

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:5000/api/health || exit 1

# Run Flask backend with Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--reload", "app:app"]
