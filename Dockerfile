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
FROM gcr.io/distroless/python3-debian12

WORKDIR /app

# Copiamos el entorno virtual de la fase de construcción
COPY --from=builder /venv /venv

# Copiamos nuestro código
COPY main.py .

EXPOSE 8000

# Añadimos la ruta de los paquetes del venv al PYTHONPATH
# Debian 12 (bookworm) usa Python 3.11 por defecto
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/venv/lib/python3.11/site-packages:/app

# La imagen distroless ya tiene ENTRYPOINT ["/usr/bin/python3"]
# Así que solo le pasamos los argumentos para ejecutar el módulo
CMD ["-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8012"]
