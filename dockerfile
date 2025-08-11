# Usa una imagen oficial de Python como base
FROM python:3.9-slim

# Instala las dependencias del sistema, incluyendo la librería C de TA-Lib
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libta-lib-dev

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos y los instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de tu proyecto al contenedor
COPY . .

# Comando que se ejecutará cuando el contenedor inicie
CMD ["python", "bot.py"]
