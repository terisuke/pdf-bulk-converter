FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1
ENV PORT 8080

WORKDIR /app

# 必要なパッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y \
  poppler-utils \
  tesseract-ocr \
  libgl1-mesa-glx \
  libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

COPY ./config /app/config
# アプリケーションコードのコピー
COPY app/ ./app/

# テンプレートとスタティックファイルのコピー
COPY templates/ ./templates/
COPY static/ ./static/

# 環境変数の設定
ENV PYTHONPATH=/app

# ポートの公開
# EXPOSE 8080

# アプリケーションの起動
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips='*'"] 