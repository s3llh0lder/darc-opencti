# Use Python 3.11 on Debian Bookworm instead of Alpine
FROM python:3.11-bookworm

# Environment variable
ENV CONNECTOR_TYPE=EXTERNAL_IMPORT

# Copy your connector source code
COPY src /opt/opencti-connector-darc

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
WORKDIR /opt/opencti-connector-darc
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose and entrypoint
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
