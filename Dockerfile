FROM python:3.9-slim

WORKDIR /app

# Install necessary packages
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://coder.com/install.sh | sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install required Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY pod_monitor.py .
RUN chmod +x pod_monitor.py
# RUN curl -L https://coder.com/install.sh | sh
RUN curl -L https://coder.com/install.sh | sh -s -- --version 2.18.5

# Run as non-root user for security
RUN useradd -m appuser
RUN chown -R appuser /app /home/appuser

USER appuser
RUN mkdir -p /home/appuser/.config

CMD ["python", "/app/pod_monitor.py"]
