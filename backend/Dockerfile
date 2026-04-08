FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY certs/ /usr/local/share/ca-certificates/extra/
RUN if [ -f /usr/local/share/ca-certificates/extra/corporate-ca.pem ]; then \
      apt-get update && apt-get install -y --no-install-recommends ca-certificates && \
      cp /usr/local/share/ca-certificates/extra/corporate-ca.pem /usr/local/share/ca-certificates/corporate-ca.crt && \
      update-ca-certificates && \
      rm -rf /var/lib/apt/lists/*; \
    fi
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
