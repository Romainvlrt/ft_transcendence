# Utiliser une image de base Nginx
FROM nginx:latest

# Supprimer le fichier de configuration par défaut de Nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copier votre fichier de configuration personnalisé Nginx dans le conteneur
COPY nginx.conf /etc/nginx/conf.d/

# Exposer le port 80 pour le serveur Nginx
EXPOSE 80

# Commande par défaut pour démarrer Nginx
CMD ["nginx", "-g", "daemon off;"]
