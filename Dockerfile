# Use Python 3.11 on Debian Bookworm instead of Alpine
FROM python:3.11-bookworm

LABEL org.opencontainers.image.title="darc-opencti" \
      org.opencontainers.image.description="OpenCTI Connector" \
      org.opencontainers.image.url="https://rado-solutions.com/" \
      org.opencontainers.image.source="https://github.com/s3llh0lder/darc-opencti" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses='BSD 3-Clause "New" or "Revised" License'

# Environment variable
ENV CONNECTOR_TYPE=EXTERNAL_IMPORT

# Install required packages
# - apt-get update & upgrade
# - Install Git, build-essential, libmagic, libffi-dev, libxml2-dev, libxslt-dev
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

# Now install Python dependencies
# (Adjust to your project's requirements, e.g., `pip install -r requirements.txt`)

# Copy your connector source code
COPY src /opt/opencti-connector-darc

WORKDIR /opt/opencti-connector-darc
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose and entrypoint
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
