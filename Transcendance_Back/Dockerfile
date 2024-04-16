# Utiliser une image de base Python
FROM python:3.9-slim

# Répertoire de travail dans le conteneur
WORKDIR /app

# Installer les dépendances Python directement dans le Dockerfile
RUN pip install --no-cache-dir Django==3.2.12 django-environ==0.7.0

# Copier le code source de votre application Django dans le conteneur
COPY . .

# Exposer le port 8000 pour le serveur Django
EXPOSE 8000

# Commande par défaut pour exécuter le serveur Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
