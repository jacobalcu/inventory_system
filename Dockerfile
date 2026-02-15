# Use an official Python runtime as a parent image
# Slim version is used to reduce the image size and unnecessary build tools
FROM python:3.11-slim

# ENV variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk (useless in containers
# PYTHONUNBUFFERED: Ensures that Python output is sent straight to the terminal without buffering (useful for logging in containers)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /code

# Dependencies: Copy requirements first to leverage Docker cache
# If change code but not requirements, Docker will use cached layer for dependencies
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r /code/requirements.txt

# Application Code: Copy rest of the app
COPY ./app /code/app

# Command: Run application
# --host 0.0.0.0 is req. for Docker to expose port outside container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]