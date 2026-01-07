FROM python:3.11

WORKDIR /app

# Copy requirements FIRST
COPY requirements.txt .

# Install requirements BEFORE copying code
RUN pip install --no-cache-dir -r requirements.txt

# THEN copy everything else
COPY . .

# Set Python path
ENV PYTHONPATH=/app

EXPOSE 8000

# Run FastAPI
CMD ["python", "-m", "uvicorn", "FastApi.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]