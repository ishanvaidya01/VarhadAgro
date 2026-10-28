FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files and buffer outputs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and dataset
COPY . .

# Expose port
EXPOSE 5000

# Run the web application
CMD ["python", "app.py"]
