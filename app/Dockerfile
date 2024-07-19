# Use the official Python image from the Debian-based version
FROM python:3.11-slim-buster AS build-stage
WORKDIR /app

# Install necessary build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    libglib2.0-0

# Copy requirements and install them
COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Copy the application code
COPY . .

# Expose the necessary port
EXPOSE 5007

# Run the application
CMD ["python", "app.py"]

# build command: docker build -t rehab .
# run command: docker run -p 5007:5007 rehab
## with camera permissions: 
# docker run --device=/dev/video0:/dev/video0 -p 5007:5007 rehab