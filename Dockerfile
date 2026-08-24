FROM python:3.11-slim

# Install system dependencies required for OpenCV, cmake, and dlib compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    g++ \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

EXPOSE 8000

ENV PORT=8000
ENV MONGO_URI="mongodb://localhost:27017/"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
