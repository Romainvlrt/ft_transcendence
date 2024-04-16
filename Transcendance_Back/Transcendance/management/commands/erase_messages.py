from django.core.management.base import BaseCommand
from Transcendance.models import Message
from Transcendance.models import Conversation
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Erase messages from a specific conversation'

    def add_arguments(self, parser):
        parser.add_argument('conversation', type=str, help='The name of the conversation')

    def handle(self, *args, **options):
        conversation_name = options['conversation']
        if conversation_name == 'General':
            Message.objects.all().delete()
        else:
            try:
                conversation = Conversation.objects.get(conversation=conversation_name)
                conversation.messages.all().delete()
            except Conversation.DoesNotExist:
                print(f"La conversation {conversation_name} n'existe pas 🔥")
                return

        print(f"Toutes les données de la conversation {conversation_name} ✅")