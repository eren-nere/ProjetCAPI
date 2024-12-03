import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import PokerRoom, Player

class PokerConsumer(AsyncWebsocketConsumer):
    """
    @brief Websocket consumer pour gérer les interactions dans une room.

    Cette classe gère les connexions Websocket, les votes des joueurs, et la
    notification des états aux utilisateurs dans une room.

    @note Utilise Django Channels.
    """

    async def connect(self):
        """
        @brief Gère la connexion d'un utilisateur à une room.

        @details Ajoute l'utilisateur au groupe Websocket correspondant à la room
        et initialise ses informations dans la base de données.

        @exception Ferme la connexion si l'utilisateur n'a pas de pseudo ou si
        la salle n'existe pas.

        @return Aucun retour.
        """
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"poker_{self.room_name}"

        self.pseudo = self.scope['session'].get('pseudo', None)
        if not self.pseudo:
            await self.close()
            return

        try:
            self.room = await sync_to_async(PokerRoom.objects.get)(name=self.room_name)
        except PokerRoom.DoesNotExist:
            await self.close()
            return

        player, created = await sync_to_async(Player.objects.get_or_create)(
            room=self.room,
            name=self.pseudo,
            defaults={'vote': None}
        )
        if not created and player.vote is not None:
            player.vote = None
            await sync_to_async(player.save)()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "not_voted_update",
                "not_voted": await self.get_not_voted_players(),
            }
        )

    async def disconnect(self, close_code):
        """
        @brief Gère la déconnexion d'un utilisateur.

        @details Supprime l'utilisateur de la base de données et notifie
        les autres utilisateurs de la room.

        @param close_code Code de fermeture envoyé par le client.

        @return Aucun retour.
        """
        await sync_to_async(Player.objects.filter(room=self.room, name=self.pseudo).delete)()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "not_voted_update",
                "not_voted": await self.get_not_voted_players(),
            }
        )

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        @brief Gère les messages reçus via Websocket.

        @details Différencie les types de messages ("vote" ou "reveal")
        et exécute les actions correspondantes.

        @param text_data Données JSON envoyées par le client.

        @return Aucun retour.
        """
        data = json.loads(text_data)

        if data['type'] == 'vote':
            player = await sync_to_async(Player.objects.get)(room=self.room, name=data['player'])
            player.vote = data['vote']
            await sync_to_async(player.save)()

            not_voted = await self.get_not_voted_players()
            all_voted = len(not_voted) == 0

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "player_vote",
                    "player": data['player'],
                    "vote": data['vote'],
                    "all_voted": all_voted,
                    "not_voted": not_voted,
                }
            )

        elif data['type'] == 'reveal':
            not_voted = await self.get_not_voted_players()
            if not_voted:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": f"Les joueurs suivants n'ont pas voté : {', '.join(not_voted)}"
                }))
                return

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
        """
        @brief Notifie les utilisateurs lorsqu'un joueur vote.

        @param event Dictionnaire contenant les détails du vote.

        @return Aucun retour.
        """
        await self.send(text_data=json.dumps({
            "type": "vote",
            "player": event["player"],
            "vote": event["vote"],
            "all_voted": event["all_voted"],
            "not_voted": event["not_voted"],
        }))

    async def reveal_votes(self, event):
        """
        @brief Notifie les utilisateurs des votes révélés.

        @param event Dictionnaire contenant la liste des votes.

        @return Aucun retour.
        """
        await self.send(text_data=json.dumps({
            "type": "reveal",
            "votes": event["votes"],
        }))

    async def not_voted_update(self, event):
        """
        @brief Met à jour la liste des joueurs n'ayant pas encore voté.

        @param event Dictionnaire contenant la liste des joueurs.

        @return Aucun retour.
        """
        await self.send(text_data=json.dumps({
            "type": "not_voted_update",
            "not_voted": event["not_voted"],
        }))

    async def get_not_voted_players(self):
        """
        @brief Récupère la liste des joueurs n'ayant pas voté.

        @return Liste des noms des joueurs n'ayant pas voté.
        """
        players = await sync_to_async(list)(self.room.players.all())
        return [player.name for player in players if player.vote is None]
