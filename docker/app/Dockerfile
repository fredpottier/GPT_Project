FROM python:3.11-slim

# Install build tools and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier requirements.txt (ATTENTION : ce fichier doit exister dans ./app lors du build)
COPY requirements.txt /app/requirements.txt

# Installation des dépendances Python
RUN pip install --no-cache-dir -r /app/requirements.txt

# forcage version zep-python et Identification des versions des composants
RUN pip install --force-reinstall --no-cache-dir zep-python==2.0.2

# Debug : lister les fichiers réellement présents dans zep_python
RUN echo "=== FICHIERS zep_python installés ===" && \
    find /usr/local/lib/python3.11/site-packages/zep_python -type f

# Vérification des versions installées
RUN pip list


# Copier le reste du code
COPY . /app

# Commande de lancement
CMD ["python", "main.py"]
