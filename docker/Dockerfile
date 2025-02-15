# Use the official Python base image
FROM python:3
# Set environment variables to prevent Python from writing .pyc files and to ensure stdout/stderr are logged
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file first to install dependencies early and take advantage of Docker layer caching
COPY requirements.txt /app/

# Install any required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application into the container
COPY . /app/

# Expose port 8000 for Django development server
EXPOSE 8000

# Define the default command to run when the container starts
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
