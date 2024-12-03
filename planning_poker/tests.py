from django.test import TestCase
from channels.testing import WebsocketCommunicator
from asgiref.sync import sync_to_async
from planning_poker.models import PokerRoom, Player
from planning_poker.consumers import PokerConsumer
from django.urls import reverse

# Tests pour les modèles
class TestModels(TestCase):
    def test_create_poker_room(self):
        room = PokerRoom.objects.create(name="RoomTest", creator="Aymene")
        self.assertEqual(room.name, "RoomTest")
        self.assertEqual(room.creator, "Aymene")
        self.assertIsNotNone(room.created_at)

    def test_create_player(self):
        room = PokerRoom.objects.create(name="RoomTest", creator="Aymene")
        player = Player.objects.create(room=room, name="Eren", vote=None)
        self.assertEqual(player.name, "Eren")
        self.assertEqual(player.room, room)

# Tests pour les vues
class TestViews(TestCase):
    def test_home_view(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planning Poker")

    def test_create_room(self):
        response = self.client.post(reverse("create_room"), {
            "room_name": "RoomTest",
            "pseudo": "Aymene"
        })
        self.assertEqual(response.status_code, 302)  # Redirection après création
        self.assertTrue(PokerRoom.objects.filter(name="RoomTest").exists())

# Tests pour les WebSocket Consumers
class TestPokerConsumer(TestCase):
    async def asyncSetUp(self):
        self.room = await sync_to_async(PokerRoom.objects.create)(
            name="RoomTest", creator="Aymene"
        )
        await sync_to_async(Player.objects.create)(
            room=self.room, name="Aymene", vote=None
        )

    async def test_websocket_connect(self):
        communicator = WebsocketCommunicator(PokerConsumer.as_asgi(), "/ws/poker/RoomTest/")
        communicator.scope["session"] = {"pseudo": "Aymene"}
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "not_voted_update")
        await communicator.disconnect()
