# Usa una imagen oficial de Python como base
FROM python:3.9-slim

# Instala herramientas para compilar y git, descarga el código de TA-Lib y lo compila
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential wget git && \
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz



# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos y los instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de tu proyecto al contenedor
COPY . .

# Comando que se ejecutará cuando el contenedor inicie
CMD ["python", "bot.py"]
