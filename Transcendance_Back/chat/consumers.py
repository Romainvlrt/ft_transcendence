import json  # Importe le module json pour manipuler les données JSON
from channels.db import database_sync_to_async  # Importe l'utilitaire pour exécuter du code synchrone dans un contexte asynchrone
from channels.generic.websocket import AsyncWebsocketConsumer  # Importe la classe de base pour les consommateurs WebSocket asynchrones
from Transcendance.models import Message, User, Conversation, GameHistory, GameStats, PFC_Game_ID  # Importe le modèle Message de votre application
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from Transcendance.serializers import GameHistorySerializer
import random

#! ATTENTION A L'HORODATAGE CE N'EST PAS LE BON FUSEAU HORAIRE


'''
#!-------------------------------------------------------------------------------------------------------
    async --> permet de définir une fonction asynchrone

    await --> permet de suspendre l'exécution de la coroutine jusqu'à ce que le résultat soit prêt

    @database_sync_to_async --> permet d'exécuter une fonction asynchrone dans un contexte synchrone
#!-------------------------------------------------------------------------------------------------------
'''



class PrivateChatConsumer(AsyncWebsocketConsumer):  # Définit une nouvelle classe de consommateur WebSocket
    async def connect(self):  # Méthode appelée lorsqu'un client se connecte
        self.room_name = self.scope['url_route']['kwargs']['room_name']  # Récupère le nom de la salle à partir des paramètres de l'URL
        self.room_group_name = f'private_{self.room_name}'  # Utilise le nom de la salle comme nom du groupe
        await self.channel_layer.group_add(  # Ajoute le canal du client au groupe
            self.room_group_name, self.channel_name
        )
        await self.accept()  # Accepte la connexion WebSocket
    
    async def disconnect(self, code):  # Méthode appelée lorsqu'un client se déconnecte
        await self.channel_layer.group_discard(  # Retire le canal du client du groupe
            self.room_group_name, self.channel_name
        )
    
    async def receive(self, text_data):  # Méthode appelée lorsqu'un message est reçu du client
        json_text = json.loads(text_data)  # Convertit le texte en JSON
        message = json_text["message"].strip()  # Récupère le message du JSON and remove leading/trailing whitespaces

        if not message:  # Si le message est vide, ne rien faire
            return

        user = self.scope['user']  # Récupère l'utilisateur de la portée
        username = user.username if user.is_authenticated else  "Anonyme"  # Récupère le nom d'utilisateur de l'utilisateur ou "Anonyme" si l'utilisateur n'est pas authentifié

        room_name = self.room_name  # Récupère le nom de la salle
        await self.save_message(room_name, user, message)  # Sauvegarde le message dans la base de données

        timestamp = datetime.now()  # Récupère le timestamp actuel
        formatted_timestamp = timestamp.strftime('%b. %d, %Y, %I:%M %p')  # Format the timestamp
        formatted_timestamp = formatted_timestamp.replace("AM", "a.m.").replace("PM", "p.m.")  # Change AM/PM to a.m./p.m.
        await self.channel_layer.group_send(  # Envoie le message à tous les clients du groupe
            self.room_group_name, 
            {
                "type": "chat_message", 
                "message": message,
                "username": username,
                "timestamp": formatted_timestamp
            }
        )
    
    async def chat_message(self, event):  # Méthode appelée lorsqu'un message de chat est reçu du groupe
        message = event['message']  # Récupère le message de l'événement
        timestamp = event.get("timestamp", "")  # Récupère le timestamp de l'événement
        username = event.get("username", "Anonyme")  # Récupère le nom d'utilisateur de l'événement
        await self.send(text_data=json.dumps({"message": message, "username" : username, "timestamp" : timestamp}))  # Envoie le message au client
    
    @database_sync_to_async
    def save_message(self, room_name, user, message):  # Méthode pour sauvegarder un message dans la base de données
        try:
            conversation = Conversation.objects.get(conversation=room_name)  # Récupère la conversation générale
        except Conversation.DoesNotExist:
            print(f"❌ {room_name} conversation not found ❌")
            return
        new_message = Message(conversation=conversation, user=user, content=message)  # Crée un nouveau message
        new_message.save()  # Sauvegarde le message

class SystemConsumer(AsyncWebsocketConsumer):  # Définit une nouvelle classe de consommateur WebSocket
    async def connect(self):  # Méthode appelée lorsqu'un §client se connecte
        self.room_name = 'system_room'  # Définit le nom de la salle
        self.room_group_name = self.room_name # Utilise le nom de la salle comme nom du groupe
        await self.channel_layer.group_add(  # Ajoute le canal du client au groupe
            self.room_group_name, self.channel_name
        )
        await self.accept()  # Accepte la connexion WebSocket
    
    async def disconnect(self, code):  # Méthode appelée lorsqu'un client se déconnecte
        await self.channel_layer.group_discard(  # Retire le canal du client du groupe
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data):  # Méthode appelée lorsqu'un message est reçu du client
        json_text = json.loads(text_data)  # Convertit le texte en JSON

        command = None
        original_user = None
        user_to_add = None
        friend_to_delete = None
        already_friend = None

        current_user = self.scope['user']

        if not current_user.is_authenticated:
            return

        if "command" in json_text:
            command = json_text["command"]
            print(f"🔱 command : {command}")

        if "original_user" in json_text:
            original_user = json_text["original_user"]
            original_user = await self.get_user(original_user)
            print(f"🔱 original_user : {original_user}")
    
        if "user_to_add" in json_text:
            user_to_add = json_text["user_to_add"]
            user_to_add = await self.get_user(user_to_add)
            print(f"🔱 user_to_add : {user_to_add}")

        if "friend_to_delete" in json_text:
            friend_to_delete = json_text["friend_to_delete"]
            friend_to_delete = await self.get_user(friend_to_delete)
            print(f"🔱 friend_to_delete : {friend_to_delete}")

        if "already_friend" in json_text:
            already_friend = json_text["already_friend"]
            print(f"🔱 already_friend : {already_friend}")

        print('\n')
    
        if original_user is not None and user_to_add is not None or "get" in command or friend_to_delete is not None or already_friend is not None:
            await self.command_handler(command, original_user, user_to_add, current_user, friend_to_delete, already_friend)
    
    async def command_handler(self, command, original_user, user_to_add, current_user, friend_to_delete, already_friend):
        if command == 'add_friend':
            if current_user == original_user and user_to_add not in current_user.block_list and current_user.username not in user_to_add.block_list:
                add_friend = await self.add_friend_request(original_user, user_to_add)
                if add_friend:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "system_message",
                            'message': {
                                'command': "add_friend",
                                'original_user': original_user.username,
                                'user_to_add': user_to_add.username
                            }
                        }
                    )
                print(f'✅ add_friend : {original_user} -> {user_to_add}')

        if command == 'accept_friend':
            if current_user == user_to_add and not original_user in current_user.block_list:
                await self.accept_friend_request(original_user, user_to_add)
                await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "system_message",
                            'message': {
                                'command': "friend_accepted",
                                'user_to_add': user_to_add.username,
                                'original_user': original_user.username
                            }
                        }
                    )


        if command == 'reject_friend':
            if current_user == user_to_add and not original_user in current_user.block_list:
                await self.reject_friend_request(original_user, user_to_add)
                await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "system_message",
                            'message': {
                                'command': "friend_rejected",
                                'user_to_add': user_to_add.username,
                                'original_user': original_user.username
                            }
                        }
                    )
            
        if command == 'delete_friend':
            if current_user == original_user and not friend_to_delete in current_user.block_list:
                await self.delete_friend_request(friend_to_delete, original_user)
                await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "system_message",
                            'message': {
                                'command': "friend_deleted",
                                'friend_to_delete': friend_to_delete.username,
                                'original_user': original_user.username
                            }
                        }
                    )
        
        if command == 'block_friend':
            if current_user == original_user:
                await self.block_friend_request(original_user, user_to_add)
                await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "system_message",
                            'message': {
                                'command': "friend_blocked",
                                'user_to_add': user_to_add.username,
                                'original_user': original_user.username,
                                'already_friend': already_friend
                            }
                        }
                    )
                
        if command == 'unblock_friend':
            if current_user == original_user:
                await self.unblock_friend_request(original_user, user_to_add)
                await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "system_message",
                            'message': {
                                'command': "friend_unblocked",
                                'user_to_add': user_to_add.username,
                                'original_user': original_user.username
                            }
                        }
                    )
        
        if command == 'pfc_request':
            if current_user == original_user:
                await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "system_message",
                            'message': {
                                'command': "pfc_asked",
                                'user_to_add': user_to_add.username,
                                'original_user': original_user.username
                            }
                        }
                    )
                
        if command == 'pfc_accepted':
            if current_user == user_to_add:
                await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "system_message",
                            'message': {
                                'command': "pfc_accepted",
                                'user_to_add': user_to_add.username,
                                'original_user': original_user.username
                            }
                        }
                    )
        
        if command == 'pfc_rejected':
            if current_user == user_to_add:
                await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "system_message",
                            'message': {
                                'command': "pfc_rejected",
                                'user_to_add': user_to_add.username,
                                'original_user': original_user.username
                            }
                        }
                    )
    
        if command == 'get_friends_infos':
            if current_user == user_to_add:
                friends_infos = await self.get_friends_infos_request(user_to_add)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "system_message",
                        'message': friends_infos
                    }
                )

        if command == 'get_user_infos':
            user_infos = await self.get_user_infos_request(original_user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "system_message",
                    'message': user_infos
                }
            )

        if command == 'get_user_history':
            history = await self.get_user_history_request(original_user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "system_message",
                    'message': history
                }
            )

#! add_friend : original_user, user_to_add
#! accept_friend : original_user, user_to_add
#! reject_friend : original_user, user_to_add
    async def system_message(self, event):
        # Extract the message from the event
        message = event['message']

        # Send the message to the WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    @database_sync_to_async
    def get_user(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        return user

    @database_sync_to_async
    def add_friend_request(self, original_user, user_to_add):
        if not user_to_add.friends.filter(username=original_user.username).exists() and not original_user.username in user_to_add.friend_request:
            user_to_add.friend_request.append(original_user.username)
            user_to_add.save()
            return True
        return False

    @database_sync_to_async
    def accept_friend_request(self, original_user, user_to_add):
        if not original_user.friends.filter(username=user_to_add.username).exists():
            original_user.friends.add(user_to_add)
            original_user.save()
            if original_user.username in user_to_add.friend_request:
                user_to_add.friend_request.remove(original_user.username)
                user_to_add.save()
            

    @database_sync_to_async
    def reject_friend_request(self, original_user, user_to_add):
        if original_user.username in user_to_add.friend_request:
            user_to_add.friend_request.remove(original_user.username)
            user_to_add.save()


    @database_sync_to_async
    def delete_friend_request(self, friend_to_delete, original_user):
        if original_user.friends.filter(username=friend_to_delete.username).exists():
            original_user.friends.remove(friend_to_delete)
            original_user.save()

    
    @database_sync_to_async
    def block_friend_request(self, original_user, user_to_add):
        if user_to_add.username in original_user.friend_request:
            original_user.friend_request.remove(user_to_add.username)
        
        if original_user.friends.filter(username=user_to_add.username).exists():
            original_user.friends.remove(user_to_add)

        if user_to_add.username not in original_user.block_list:
            original_user.block_list.append(user_to_add.username)
        
        original_user.save()

    @database_sync_to_async
    def unblock_friend_request(self, original_user, user_to_add):
        if user_to_add.username in original_user.block_list:
            original_user.block_list.remove(user_to_add.username)
            original_user.save()


    @database_sync_to_async
    def get_friends_infos_request(self, user):
        data = {
            'command': 'get_friends_infos',
            'user_to_add': user.username,
            'original_user': 'None',
            'friends': [friend.username for friend in user.friends.all()],
            'friend_request': list(user.friend_request),
            'block_list': list(user.block_list)
        }
        return data


    @database_sync_to_async
    def get_user_infos_request(self, user):
        try:
            user_stats = GameStats.objects.get(user=user)
            data = {
                'command': 'user_infos_sent',
                'total_pong_win': user_stats.total_pong_win,
                'total_pong_los': user_stats.total_pong_los,
                'total_pong_win_tie': user_stats.total_pong_win_tie,
                'total_pong_los_tie': user_stats.total_pong_los_tie,
                'total_scissors': user_stats.total_scissors,
                'total_paper': user_stats.total_paper,
                'total_rock': user_stats.total_rock,
                'total_spr_win': user_stats.total_spr_win,
                'total_spr_los': user_stats.total_spr_los,
                'total_spr_win_tie': user_stats.total_spr_win_tie,
                'total_spr_los_tie': user_stats.total_spr_los_tie,
                'username' : user.username
            }
        except GameStats.DoesNotExist:
            data = {
                'command': 'user_not_found',
            }
        return data
        
    @database_sync_to_async
    def get_user_history_request(self, user):
        try:
            game_history = GameHistory.get_games_for_user(user)
            serializer = GameHistorySerializer(game_history, many=True)
            data = {
                'command': 'user_history_sent',
                'game_history': serializer.data
            }
        except GameHistory.DoesNotExist:
            data = {
                'command': 'user_history_not_found',
            }
        return data


class ChatConsumer(AsyncWebsocketConsumer):  # Définit une nouvelle classe de consommateur WebSocket
    async def connect(self):  # Méthode appelée lorsqu'un client se connecte
        self.room_name = 'public_room'  # Définit le nom de la salle
        self.room_group_name = self.room_name  # Utilise le nom de la salle comme nom du groupe
        await self.channel_layer.group_add(  # Ajoute le canal du client au groupe
            self.room_group_name, self.channel_name
        )

        self.user = self.scope["user"]  # Récupère l'utilisateur de la portée

        await self.accept()  # Accepte la connexion WebSocket

    async def disconnect(self, code):  # Méthode appelée lorsqu'un client se déconnecte
        await self.channel_layer.group_discard(  # Retire le canal du client du groupe
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data):  # Méthode appelée lorsqu'un message est reçu du client
        json_text = json.loads(text_data)  # Convertit le texte en JSON
        message = json_text["message"].strip()  # Récupère le message du JSON and remove leading/trailing whitespaces

        if not message: # Si le message est vide, ne rien faire
            return
        
        user = self.scope['user']  # Récupère l'utilisateur de la portée
        username = user.username if user.is_authenticated else "Anonyme"  # Récupère le nom d'utilisateur de l'utilisateur ou "Anonyme" si l'utilisateur n'est pas authentifié

        
        await self.save_message('General', user, message)  # Sauvegarde le message dans la base de données

        timestamp = datetime.now()  # Récupère le timestamp actuel
        formatted_timestamp = timestamp.strftime('%b. %d, %Y, %I:%M %p')  # Format the timestamp
        formatted_timestamp = formatted_timestamp.replace("AM", "a.m.").replace("PM", "p.m.")  # Change AM/PM to a.m./p.m.
        await self.channel_layer.group_send(  # Envoie le message à tous les clients du groupe
            self.room_group_name, 
            {
                "type": "chat_message", 
                "message": message,
                "username": username,
                "timestamp": formatted_timestamp
            }
        )
    
    async def chat_message(self, event):  # Méthode appelée lorsqu'un message de chat est reçu du groupe
        message = event['message']  # Récupère le message de l'événement
        timestamp = event.get("timestamp", "")  # Récupère le timestamp de l'événement
        username = event.get("username", "Anonyme")  # Récupère le nom d'utilisateur de l'événement
        await self.send(text_data=json.dumps({"message": message, "username" : username, "timestamp" : timestamp}))  # Envoie le message au client

    @database_sync_to_async
    def save_message(self, room_name, user, message):  # Méthode pour sauvegarder un message dans la base de données
        try:
            conversation = Conversation.objects.get(conversation=room_name)  # Récupère la conversation générale
        except Conversation.DoesNotExist:
            print(f"❌ {room_name} conversation not found ❌")
            return
        new_message = Message(conversation=conversation, user=user, content=message)  # Crée un nouveau message
        new_message.save()  # Sauvegarde le message

class PFCConsumer(AsyncWebsocketConsumer): # Définit une nouvelle classe de consommateur WebSocket

    

    async def connect(self):  # Méthode appelée lorsqu'un client se connecte
        self.room_name = self.scope['url_route']['kwargs']['room_name']  # Récupère le nom de la salle à partir des paramètres de l'URL
        self.room_group_name = f'pfc_{self.room_name}'  # Utilise le nom de la salle comme nom du groupe
        await self.channel_layer.group_add(  # Ajoute le canal du client au groupe
            self.room_group_name, self.channel_name
        )
        await self.accept()  # Accepte la connexion WebSocket
        self.players = self.room_name.split('_')
        self.player1 = self.players[0]
        self.player2 = self.players[1]
        self.game_id = None


    async def disconnect(self, code):  # Méthode appelée lorsqu'un client se déconnecte
        current_user = self.scope['user']
        winner = None
        if current_user.username == self.player1:
            winner = self.player2
        else:
            winner = self.player1
        await self.clean_db()
        await self.channel_layer.group_discard(  # Retire le canal du client du groupe
            self.room_group_name, self.channel_name
        )
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "PFC_message",
                'message': {
                    'command': "game_aborted",
                    'winner': winner
                }
            }
        )


    async def receive(self, text_data):  # Méthode appelée lorsqu'un message est reçu du client
        json_text = json.loads(text_data)

        command = None
        action = None
        player = None
        current_user = self.scope['user']

        if "command" in json_text:
            command = json_text["command"]
            print(f"🔱 command : {command}")

        if "action" in json_text:
            action = json_text["action"]
            print(f"🔱 action : {action}")

        if "player" in json_text:
            player = json_text["player"]
            print(f"🔱 player : {player}")
        print('\n')

        if (command is not None and player is not None) and (player in self.players) and (current_user.username == player) or (command == "have_played" and player is not None and action is not None and current_user.username == player):
            await self.commandHandler(command, action, player)
        else:
            print(f"❌ {current_user.username} tried to cheat ❌")
            return
        
        print(f'✅ game_id : {self.game_id}')
        print('\n')

    



    async def commandHandler(self, command, action, player):
        
        if command == "have_played":
            await self.add_action(player, action)
            if await self.attribute_point():
                updated_game = await self.get_updated_game()
                print(f"💬 SCORE --> {updated_game.player1_score} - {updated_game.player2_score}")
                print(f"💬 PENALTIES --> {updated_game.player1_penalties} - {updated_game.player2_penalties}")
                print(f"💬 ROUND --> {updated_game.round_count}")
                print('\n')
                winner = await self.check_if_game_is_finished()
                if winner is not None:
                    await self.update_user_pfc_stats(winner)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "PFC_message",
                            'message': {
                                'command': "game_finished",
                                'winner': winner
                            }
                        }
                    )
                else:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "PFC_message",
                            'message': {
                                'command': "round_finished",
                                'player1_score': updated_game.player1_score,
                                'player2_score': updated_game.player2_score,
                                'round_count': updated_game.round_count,
                                'player1_penalties': updated_game.player1_penalties,
                                'player2_penalties': updated_game.player2_penalties
                            }
                        }
                    )

            
        if command == "generate_game_id":
            await self.generate_game_id()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "PFC_message",
                    'message': {
                        'command': "game_id_generated",
                    }
                }
            )
        
        if command == "get_game_id":
            await self.get_game_id()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "PFC_message",
                    'message': {
                        'command': "start_game",
                    }
                }
            )


    async def PFC_message(self, event):
        # Extract the message from the event
        message = event['message']

        # Send the message to the WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))


    @database_sync_to_async
    def generate_game_id(self):
        game_id_generated = random.randint(10000000000, 99999999999)
        game_id = PFC_Game_ID()
        game_id.game_id = game_id_generated
        game_id.room_id = self.room_name
        self.game_id = game_id_generated
        game_id.save()
        
        game_history = GameHistory()
        game_history.game_id = game_id_generated
        game_history.player1 = User.objects.get(username=self.player1)
        game_history.player2 = User.objects.get(username=self.player2)
        game_history.save()

    
    @database_sync_to_async
    def get_game_id(self):
        try:
            game_id_object = PFC_Game_ID.objects.get(room_id=self.room_name)
        except PFC_Game_ID.DoesNotExist:
            return None
        self.game_id = game_id_object.game_id


    @database_sync_to_async
    def add_action(self, player, action):
        game = GameHistory.objects.get(game_id=self.game_id)
        if player == self.player1:
            game.player1_moves.append(action)
        if player == self.player2:
            game.player2_moves.append(action)
        game.save()

    
    @database_sync_to_async
    def attribute_point(self):
        game = GameHistory.objects.get(game_id=self.game_id)
        if len(game.player1_moves) != len(game.player2_moves):
            return False
        else:
            p1 = game.player1_moves[-1]
            p2 = game.player2_moves[-1]

            if p1 == "rock" and p2 == "scissors":
                game.player1_score += 1
            if p1 == "rock" and p2 == "paper":
                game.player2_score += 1

            if p1 == "scissors" and p2 == "rock":
                game.player2_score += 1
            if p1 == "scissors" and p2 == "paper":
                game.player1_score += 1

            if p1 == "paper" and p2 == "rock":
                game.player1_score += 1
            if p1 == "paper" and p2 == "scissors":
                game.player2_score += 1
            
            if p1 == "timeout":
                game.player1_penalties += 1
            if p2 == "timeout":
                game.player2_penalties += 1
            
            game.round_count += 1
            game.save()
        return True

    @database_sync_to_async
    def check_if_game_is_finished(self):
        game = GameHistory.objects.get(game_id=self.game_id)

        if game.player1_penalties == 3 and game.player2_penalties == 3:
            return "null match"
        if game.player1_penalties == 3:
            return self.player2
        if game.player2_penalties == 3:
            return self.player1
        
        if game.player1_score == 7:
            return self.player1
        if game.player2_score == 7:
            return self.player2
        return None

    @database_sync_to_async
    def get_updated_game(self):
        game = GameHistory.objects.get(game_id=self.game_id)
        return game

    @database_sync_to_async
    def clean_db(self):
        try:
            game = PFC_Game_ID.objects.get(game_id=self.game_id)
            game.delete()
        except PFC_Game_ID.DoesNotExist:
            return

        try:
            game_history = GameHistory.objects.get(game_id=self.game_id)
            if (game_history.player1_score != 7 and game_history.player2_score != 7) and (game_history.player1_penalties != 3 and game_history.player2_penalties != 3) or (game_history.player1_penalties == 3 and game_history.player2_penalties == 3):
                game_history.delete()
        except GameHistory.DoesNotExist:
            return
        
    @database_sync_to_async
    def update_user_pfc_stats(self, winner):
        game = GameHistory.objects.get(game_id=self.game_id)

        if winner == self.player1:
            winner = User.objects.get(username=winner)
            #! get or create renvoie 2 valeur, le premier est l'objet et le deuxième est un booléen qui indique si l'objet a été créé ou non
            #! Je fais , _ pour ne pas stocker le booléen car je n'en ai pas besoin
            winner_stats, _ = GameStats.objects.get_or_create(user=winner)
            winner_stats.total_spr_win += 1
            winner_stats.total_spr_win_tie += game.player1_score
            winner_stats.total_spr_los_tie += game.player2_score
            winner_stats.total_rock += game.player1_moves.count("rock")
            winner_stats.total_paper += game.player1_moves.count("paper")
            winner_stats.total_scissors += game.player1_moves.count("scissors")
            winner_stats.save()

            loser = User.objects.get(username=self.player2)
            loser_stats, _ = GameStats.objects.get_or_create(user=loser)
            loser_stats.total_rock += game.player2_moves.count("rock")
            loser_stats.total_paper += game.player2_moves.count("paper")
            loser_stats.total_scissors += game.player2_moves.count("scissors")
            loser_stats.total_spr_los += 1
            loser_stats.total_spr_win_tie += game.player2_score
            loser_stats.total_spr_los_tie += game.player1_score
            loser_stats.save()

        else:
            winner = User.objects.get(username=winner)
            winner_stats, _ = GameStats.objects.get_or_create(user=winner)
            winner_stats.total_spr_win += 1
            winner_stats.total_spr_win_tie += game.player2_score
            winner_stats.total_spr_los_tie += game.player1_score
            winner_stats.total_rock += game.player2_moves.count("rock")
            winner_stats.total_paper += game.player2_moves.count("paper")
            winner_stats.total_scissors += game.player2_moves.count("scissors")
            winner_stats.save()

            loser = User.objects.get(username=self.player1)
            loser_stats, _ = GameStats.objects.get_or_create(user=loser)
            loser_stats.total_rock += game.player1_moves.count("rock")
            loser_stats.total_paper += game.player1_moves.count("paper")
            loser_stats.total_scissors += game.player1_moves.count("scissors")
            loser_stats.total_spr_los += 1
            loser_stats.total_spr_win_tie += game.player1_score
            loser_stats.total_spr_los_tie += game.player2_score
            loser_stats.save()

            
