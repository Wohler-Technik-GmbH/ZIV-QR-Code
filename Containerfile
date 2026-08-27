# Use the NiceGUI base image
FROM zauberzeug/nicegui:latest

# Set the working directory in the container
WORKDIR /app

# Copy the used files into the working directory
COPY main.py .
COPY field_name/field_names_en.json ./field_names.json

# Start the application
CMD ["python", "main.py"]