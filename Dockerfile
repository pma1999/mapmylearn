FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=.

# Set working directory
WORKDIR /app

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libgirepository1.0-dev \
    pkg-config \
    fontconfig \
    libfreetype6-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    libtiff-dev \
    libxml2-dev \
    libxslt-dev \
    libglib2.0-0 \
    libglib2.0-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Install the project
RUN pip install -e .

# Create startup script with proper environment variable handling
RUN echo '#!/bin/bash\n\
echo "Starting application with environment:"\n\
echo "PORT=$PORT"\n\
echo "PYTHONPATH=$PYTHONPATH"\n\
python bootstrap.py\n\
' > /app/startup.sh && chmod +x /app/startup.sh

# Use shell form to ensure environment variables are expanded
# Use the startup script to add an extra layer of environment variable handling
CMD ["/bin/bash", "/app/startup.sh"] 