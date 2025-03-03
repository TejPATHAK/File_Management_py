# Use official Python image
FROM python:3.10

# Set working directory inside the container
WORKDIR /app

# Copy all project files into the container
COPY . .

# Install dependencies (if any)
RUN pip install --no-cache-dir -r requirements.txt

# Set the default command to run the script
CMD ["python", "file_management.py"]
