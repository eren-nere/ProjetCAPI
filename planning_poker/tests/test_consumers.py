import json
from channels.testing import WebsocketCommunicator
from django.test import TestCase
from planningpoker.asgi import application
from planning_poker.models import PokerRoom, Player
from channels.sessions import SessionMiddlewareStack
from django.contrib.sessions.backends.db import SessionStore
from asgiref.sync import sync_to_async
import asyncio


class PokerConsumerTestCase(TestCase):
    #génère une doc pour doxygen
    """
    Test pour la classe PokerConsumer.

    @param TestCase: Classe de test Django.
    """
    def setUp(self):
        """
        Initialisation du test.
        
        @param self: Instance de la classe.
        """
        print("DEBUG: Initialisation du test.")
        self.room = PokerRoom.objects.create(
            name="test_room",
            creator="test_creator",
            backlog=json.dumps([
                {"feature": "Connexion utilisateur"},
                {"feature": "Recherche avancée"},
                {"feature": "Ajout au panier"}
            ]),
            all_features=json.dumps([])
        )
        print(f"DEBUG: Room créée avec backlog : {self.room.backlog}")

        self.player = Player.objects.create(
            room=self.room,
            name="test_player",
            vote=None
        )
        print(f"DEBUG: Player créé : {self.player.name}")

    async def test_vote_and_reveal(self):
        """
        Test de vote et révélation.

        @param self: Instance de la classe.
        """
        print("DEBUG: Début du test de vote et révélation.")

        session = await sync_to_async(SessionStore)()
        session["pseudo"] = "test_player"
        await sync_to_async(session.save)()

        communicator = WebsocketCommunicator(
            SessionMiddlewareStack(application),
            f"/ws/poker/{self.room.name}/"
        )
        communicator.scope["session"] = session
        print(f"DEBUG: WebsocketCommunicator instancié pour la room {self.room.name}.")

        connected, _ = await communicator.connect()
        print(f"DEBUG: Connexion WebSocket établie : {connected}")
        self.assertTrue(connected)

        player_count = await sync_to_async(Player.objects.filter(room=self.room).count)()
        print(f"DEBUG: Nombre de joueurs dans la room : {player_count}")
        self.assertEqual(player_count, 1)

        vote_message = {
            "type": "vote",
            "player": "test_player",
            "vote": "5"
        }
        print(f"DEBUG: Envoi du vote : {vote_message}")
        await communicator.send_json_to(vote_message)

        response = await communicator.receive_json_from()
        print(f"DEBUG: Première réponse reçue après le vote : {response}")
        self.assertEqual(response["type"], "not_voted_update")

        await asyncio.sleep(0.1)

        response = await communicator.receive_json_from()
        print(f"DEBUG: Réponse après attente : {response}")
        self.assertNotIn("test_player", response["not_voted"])

        reveal_message = {
            "type": "reveal"
        }
        print(f"DEBUG: Envoi de la révélation des votes : {reveal_message}")
        await communicator.send_json_to(reveal_message)

        reveal_response = await communicator.receive_json_from()
        print(f"DEBUG: Réponse reçue après la révélation : {reveal_response}")
        self.assertEqual(reveal_response["type"], "reveal")
        self.assertTrue("votes" in reveal_response)
        self.assertEqual(reveal_response["unanimity"], True)

        next_feature_response = await communicator.receive_json_from()
        print(f"DEBUG: Réponse reçue pour la fonctionnalité suivante : {next_feature_response}")
        self.assertEqual(next_feature_response["type"], "feature_update")
        self.assertEqual(next_feature_response["feature"]["feature"], "Recherche avancée")

        await communicator.disconnect()
        print("DEBUG: Connexion WebSocket fermée.")
