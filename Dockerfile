# Dockerfile to Deploy Yu-Gi-Oh Card Identification API on Render

# Base image with Python 3.9
FROM python:3.9

# Set working directory inside container
WORKDIR /app

# Install system-level dependencies (including Rust and other needed packages)
RUN apt-get update && apt-get install -y libgl1-mesa-glx curl && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    . "$HOME/.cargo/env"

# Copy requirements.txt and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into container
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]
