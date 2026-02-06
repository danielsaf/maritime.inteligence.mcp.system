# 1. Base Image: Use the latest stable Python 3.13
FROM python:3.13-slim

# 2. Environment Variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. System Dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 4. Install Dependencies
# Because our context is ./backend, Docker looks for requirements.txt there
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy Source Code
# Copy everything from the context (./backend) into /app in the container
COPY . .

EXPOSE 8000

# 6. Entry Point
CMD ["python", "-m", "src.main"]