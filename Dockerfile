# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Set environment variables (override in runtime or with .env file bind)
ENV PYTHONUNBUFFERED=1

# Command to run the script
CMD ["python", "main.py"]
