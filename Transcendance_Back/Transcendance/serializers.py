from rest_framework import serializers
from .models import GameHistory

class GameHistorySerializer(serializers.ModelSerializer):
    player1_username = serializers.CharField(source='player1.username', read_only=True)
    player2_username = serializers.CharField(source='player2.username', read_only=True)

    class Meta:
        model = GameHistory
        fields = ['player1_username', 'player2_username'] + [f.name for f in GameHistory._meta.fields]