# ==========================================
# STAGE 1: Builder
# ==========================================
# Use a standard slim image to build our dependencies
FROM python:3.11-slim-bookworm AS builder

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a virtual environment
RUN python -m venv /venv
# Make sure we use the virtualenv
ENV PATH="/venv/bin:$PATH"

# Install dependencies into the virtual environment
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# STAGE 2: Distroless (Final Image)
# ==========================================
# Use the official Google Distroless Python 3 image based on Debian 12
FROM gcr.io/distroless/python3-debian12

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /venv /venv

# Copy our application code
COPY main.py .

# Expose the port FastAPI will run on
EXPOSE 8000

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# The distroless python3 image has an ENTRYPOINT of ["/usr/bin/python3"]
# So we pass the path to the uvicorn executable inside our venv as the first argument,
# followed by the arguments for uvicorn itself.
CMD ["/venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
