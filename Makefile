# Démarrer les services Docker
start:
	docker-compose up -d

# Arrêter les services Docker
stop:
	docker-compose down

# Arrêter les services Docker et supprimer les volumes persistants
clean:
	docker-compose down -v

# Afficher les journaux des services Docker
logs:
	docker-compose logs -f
