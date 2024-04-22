FROM python:3.9-slim

# Installer les dépendances nécessaires pour psycopg2
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# Créez un répertoire de travail
WORKDIR /app

# Copiez le fichier des dépendances et installez-les
COPY requirements.txt .

# Installez les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copiez le code source de l'application dans le conteneur
COPY . .

# Exécutez les migrations et lancez l'application Django
CMD ["sh", "-c", "python manage.py migrate && daphne -b 0.0.0.0 -p 4000 Transcendance_Back.asgi:application"]
