# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir: Disables the cache to keep the image size smaller
# --compile: Compiles Python source files to bytecode
RUN pip install --no-cache-dir --compile -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 5000 available to the world outside this container
# App Runner will use the PORT environment variable, but EXPOSE is good practice
EXPOSE 5000

# Define environment variable (App Runner will override this, but good for local testing)
ENV PORT=5000
ENV AWS_REGION_NAME=us-east-1

# Run run.py when the container launches using Gunicorn
# Use the PORT environment variable provided by App Runner
CMD ["gunicorn", "--bind", ":$PORT", "--workers", "4", "run:app"]
