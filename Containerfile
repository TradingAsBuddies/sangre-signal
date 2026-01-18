# Containerfile for Sangre Signal
# Build: podman build -t sangre-signal .
# Run:   podman run --rm -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY sangre-signal --ticker AAPL

FROM python:3.11-slim

LABEL maintainer="David Duncan <tradingasbuddies@davidduncan.org>"
LABEL description="Sangre Signal - Advanced stock analysis with Claude AI"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Install system dependencies (needed for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY pyproject.toml README.md ./
COPY sangre_signal/ ./sangre_signal/

# Install the package
RUN pip install --no-cache-dir .

# Switch to non-root user
USER appuser

# Create cache directory for the app
RUN mkdir -p /home/appuser/.cache/sangre-signal

# Set entrypoint
ENTRYPOINT ["sangre-signal"]

# Default command (show help if no args provided)
CMD ["--help"]
