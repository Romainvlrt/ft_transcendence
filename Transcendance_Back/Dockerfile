# Utiliser une image de base Python
FROM python:3.9-slim

# Répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier requirements.txt dans le conteneur
COPY requirements.txt .

# Installer les dépendances Python à partir du fichier requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copier le fichier .env dans le répertoire de travail du conteneur
COPY .env .

# Copier le code source de votre application Django dans le conteneur
COPY . .

# Exécuter les migrations Django
# RUN python manage.py migrate

# Exposer le port 8000 pour le serveur Django
EXPOSE 8000

# Commande par défaut pour exécuter le serveur Django avec Daphne
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "Transcendance_Back.asgi:application"]
