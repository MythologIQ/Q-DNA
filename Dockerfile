# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Copy application code
COPY . /app

# Install QoreLogic Gatekeeper package
WORKDIR /app/local_fortress
RUN pip install --prefix=/install .

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r qorelogic && useradd -r -g qorelogic qorelogic

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code (needed for DB fallback, though package is installed)
COPY . /app

# Set permissions
RUN chown -R qorelogic:qorelogic /app

# Switch to non-root user
USER qorelogic

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV QORELOGIC_DB_PATH=/app/ledger/qorelogic_soa_ledger.db

# Entrypoint
# Use the installed CLI entry point
ENTRYPOINT ["qorelogic-server"]
