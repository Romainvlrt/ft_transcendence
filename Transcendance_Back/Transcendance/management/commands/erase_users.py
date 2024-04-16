from django.core.management.base import BaseCommand
from Transcendance.models import User

class Command(BaseCommand):
    def handle(self, *args, **options):
        User.objects.all().delete()
        print("Toutes les données de la table User ont été supprimées avec succès ✅")