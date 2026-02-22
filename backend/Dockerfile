# Use Python 3.12 bookworm (needed for Playwright dependencies)
FROM python:3.12-bookworm

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium with all system dependencies
RUN playwright install chromium --with-deps

# Copy application code
COPY . .

# Create non-root user with access to Playwright browsers
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /ms-playwright

USER appuser

# Expose port (Cloud Run uses PORT env var, default to 8080)
EXPOSE 8080

# Run the application
CMD ["python", "-u", "run.py"]
