FROM python:3.13.4-slim

# Set working directory to project app root so `backend` package is importable
WORKDIR /app

# Copy backend requirements and install dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend source code into /app/backend so imports like `backend.config` work
COPY backend ./backend

# Default command to run the backend (module path includes package)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
