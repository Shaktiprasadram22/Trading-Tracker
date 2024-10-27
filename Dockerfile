# Use an official Python image as the base
FROM python:3.8-slim

# Install Node.js
RUN apt-get update && apt-get install -y nodejs npm

# Set the working directory
WORKDIR /app

# Copy all files to the container
COPY . /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Install Node.js dependencies
RUN npm install

# Expose the port the app runs on
EXPOSE 5000

# Run both Flask (Python) and Node.js servers
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:5000 & node server.js"]
