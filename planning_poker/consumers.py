import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from .models import PokerRoom, Player

class PokerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"poker_{self.room_name}"

        try:
            self.room = await sync_to_async(PokerRoom.objects.get)(name=self.room_name)
        except ObjectDoesNotExist:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"Connexion acceptée pour la salle : {self.room_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"Utilisateur déconnecté de la salle : {self.room_name}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            print("Message JSON invalide")
            return

        if data.get('type') == 'vote':
            await self.handle_vote(data)
        elif data.get('type') == 'reveal':
            await self.handle_reveal()

    async def handle_vote(self, data):
        player_name = data.get('player')
        vote = data.get('vote')

        if not player_name or vote is None:
            print("Données de vote invalides")
            return

        player, created = await sync_to_async(Player.objects.get_or_create)(
            room=self.room,
            name=player_name
        )
        player.vote = vote
        await sync_to_async(player.save)()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "player_vote",
                "player": player_name,
                "vote": vote,
            }
        )

    async def handle_reveal(self):
        votes = await sync_to_async(list)(
            Player.objects.filter(room=self.room).values('name', 'vote')
        )
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "reveal_votes",
                "votes": votes,
            }
        )

    async def player_vote(self, event):
        await self.send(text_data=json.dumps({
            "type": "vote",
            "player": event["player"],
            "vote": event["vote"],
        }))

    async def reveal_votes(self, event):
        await self.send(text_data=json.dumps({
            "type": "reveal",
            "votes": event["votes"],
        }))
