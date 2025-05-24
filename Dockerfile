FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg pkg-config libsystemd-dev build-essential \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy only requirements first (to leverage Docker cache)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Set display port to avoid issues with headless Chrome
ENV DISPLAY=:99
ENV CHROMIUM_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver


# Default command
CMD ["python", "franka_bot.py"]
