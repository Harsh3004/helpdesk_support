# Use the official Python 3.10 image as a base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first (this caches dependencies to make future builds faster)
COPY requirements.txt .

# Install the Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the rest of your files (app.py, graders.py, openenv.yaml) into the container
COPY . .

# Hugging Face Spaces strictly requires apps to run on port 7860
ENV PORT=7860
EXPOSE $PORT

# The command that starts your server inside the container
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]