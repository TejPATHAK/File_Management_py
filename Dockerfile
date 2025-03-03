# Use official Python image
FROM python:3.10

# Set working directory inside the container
WORKDIR /app

# Copy all project files
COPY . .

# Install dependencies (if any)
RUN pip install -r requirements.txt

# Set the default command to run the script
CMD ["python", "file_management.py"]
