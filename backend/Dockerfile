FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run sets PORT env var, default to 8080
ENV PORT=8080

# Run the application (must use $PORT not ${PORT} for shell substitution)
CMD uvicorn main:app --host 0.0.0.0 --port $PORT

