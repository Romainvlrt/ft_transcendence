from django.core.management.base import BaseCommand
from Transcendance.models import GameHistory, PFC_Game_ID, User
from django.core.exceptions import ObjectDoesNotExist



class Command(BaseCommand):
    help = 'Erase gamehistory and pfc_game_id from id' 

    def add_arguments(self, parser):
        parser.add_argument('--id', type=str, help='id of the game', nargs='?')
        parser.add_argument('--players', type=str, help='players_name', nargs='?')

    def handle(self, *args, **options):
        id = options['id']
        players = options['players']
        if id is not None:
            try:
                game = GameHistory.objects.get(game_id=id)
                game.delete()
            except game.DoesNotExist:
                print(f"La game {id} n'existe pas 🔥")
                return
            
            try:
                game_id = PFC_Game_ID.objects.get(game_id=id)
                game_id.delete()
            except game_id.DoesNotExist:
                print(f"La game_id {id} n'existe pas dans PFC_game_id 🔥")
                return
        
        elif players is not None:
            players = players.split('_')
            players.sort()
            try:
                games = GameHistory.get_games_between(User.objects.get(username=players[0]), User.objects.get(username=players[1]))
                games.delete()
            except GameHistory.DoesNotExist:
                print(f"Aucune game {players[0]} vs {players[1]} n'existe 🔥")
            try:
                game_ids = PFC_Game_ID.objects.filter(room_id=f"{players[0]}_{players[1]}")
                game_ids.delete()
            except PFC_Game_ID.DoesNotExist:
                print(f"Aucun game_id {players[0]} vs {players[1]} n'existe dans PFC_game_id 🔥")

        print(f"Tous les historiques ont ete delete ✅")