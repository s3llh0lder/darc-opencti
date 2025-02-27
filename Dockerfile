# Use Python 3.11 on Debian Bookworm
FROM python:3.11-bookworm

LABEL org.opencontainers.image.title="darc-opencti" \
      org.opencontainers.image.description="OpenCTI Connector" \
      org.opencontainers.image.url="https://rado-solutions.com/" \
      org.opencontainers.image.source="https://github.com/s3llh0lder/darc-opencti" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses='BSD 3-Clause "New" or "Revised" License'

# Environment variables
ENV CONNECTOR_TYPE=EXTERNAL_IMPORT \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/opencti-connector-darc

# Install system dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        libmagic-dev \
        libffi-dev \
        libxml2-dev \
        libxslt-dev && \
    rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /opt/opencti-connector-darc

# Clone txt2stix directly into the project directory
RUN git clone https://github.com/muchdogesec/txt2stix ./txt2stix

# Copy application files
COPY src/ ./src/
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint and set permissions
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]