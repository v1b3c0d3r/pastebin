FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# must be absolute path to a directory inside container
ENV DATA_DIR=/data
EXPOSE 5000
VOLUME /data
CMD ["python", "app.py"]

