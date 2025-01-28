# Use a base Python image
FROM python:3.8-slim

# Install necessary build tools
RUN apt-get update && apt-get install -y \
    binutils \
    && rm -rf /var/lib/apt/lists/*


# Create a directory for your project (adjust as needed)
WORKDIR /srv/abrowser

# Copy the project files into the container
COPY . /srv/abrowser/

# Install any Python dependencies (adjust the path if necessary)
RUN pip install -r requirements.txt

# Run PyInstaller to generate the executable
RUN pyinstaller --onefile ABrowser.py

