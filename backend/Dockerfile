FROM python:3.12
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY backend/ .
COPY data /app/data
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram_backend.wsgi"]
