# Usa la imagen oficial de Python
FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los requerimientos e instálalos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# COPIA TODO EL CONTENIDO DE LA CARPETA ACTUAL (.) AL CONTENEDOR (.)
# Esto incluirá app.py y la carpeta templates/
COPY . .

# Expone el puerto de Flask
EXPOSE 5000

# Comando para arrancar
CMD ["python", "app.py"]