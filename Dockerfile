# Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependency files
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY ./app /app/app

# Expose the port the app runs on
EXPOSE 8000

ENV PYTHONUNBUFFERED=1

# Command to run the application using Uvicorn
# We use 'gunicorn' with 'uvicorn.workers.UvicornWorker' for production-ready async handling
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]