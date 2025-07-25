# ---- Build image for Flux Image Generator ----
FROM python:3.10-slim

# Prevents Python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Ensures stdout/stderr are sent straight to terminal without buffering
ENV PYTHONUNBUFFERED=1

# Working dir
WORKDIR /app

# Copy requirements first for cache efficiency
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose default port
EXPOSE 8000

# Entry point – start FastAPI with Uvicorn
# Default command for RunPod serverless; it will call our worker.handler
CMD ["python", "-u", "worker.py"]
