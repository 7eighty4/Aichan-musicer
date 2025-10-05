# Dockerfile

# Start with a clean, official Python base image
FROM python:3.11-slim

# Set the working directory inside the server
WORKDIR /app

# Update the server's package list and install our system dependencies
# This is where we manually install FFmpeg and Opus
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    libopus-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the Python requirements file into the server
COPY requirements.txt .

# Install the Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your bot's code into the server
COPY . .

# The command to run when the server starts

CMD ["python", "Echo.py"]
