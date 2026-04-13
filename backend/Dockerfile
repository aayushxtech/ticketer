FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy dependency manifest first (Docker layer caching optimisation —
# dependencies are only re-installed when requirements.txt changes)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Expose the port uvicorn will listen on
EXPOSE 8000

# Start the ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
