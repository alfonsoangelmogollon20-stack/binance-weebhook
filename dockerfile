# Usar una imagen base de Python
FROM python:3.9-slim

# Instalar git para poder descargar la API desde GitHub
RUN apt-get update && apt-get install -y git

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar e instalar los requerimientos
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar el resto del código
COPY . .

# Comando para ejecutar el bot webhook
CMD ["python", "bot.py"]
