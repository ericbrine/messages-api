FROM python:3.14-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv sync --no-dev

COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
