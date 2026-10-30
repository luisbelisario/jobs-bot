# JobsBot — Docker image para deploy em Fly.io / Railway
FROM python:3.12-slim

# Evita buffer do Python e arquivos .pyc
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependências do sistema (mínimo necessário)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY . .

# Cria diretório de dados (SQLite)
RUN mkdir -p /app/data

# Health check leve
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os; os.kill(1, 0)" || exit 1

CMD ["python", "main.py"]