# Enterprise Support World Model v2.0 - Hugging Face Spaces Deployment
FROM python:3.11-slim

WORKDIR /app

# Copy and install requirements first to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the environment code
COPY . .

# Set Python path to recognize the server module
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

# Run the Uvicorn server using the server.app path
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]