from django.contrib import admin
from .models import Message, User, Conversation, GameStats, GameHistory, PFC_Game_ID
admin.site.register(Message)
admin.site.register(User)
admin.site.register(Conversation)
admin.site.register(GameStats)
admin.site.register(GameHistory)
admin.site.register(PFC_Game_ID)
