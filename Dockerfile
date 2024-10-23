# Dockerfile to Deploy Yu-Gi-Oh Card Identification API on Render

# Base image with Python 3.7.6
FROM python:3.7.6

# Set working directory inside container
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install system dependencies required by OpenCV
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev

# Copy the cards_description.parquet file into container
COPY cards_description.parquet /app/cards_description.parquet

# Copy all project files into container
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]