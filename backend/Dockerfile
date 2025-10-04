FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Cloud Run uses PORT env var)
ENV PORT=8080

# Run the application
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}

