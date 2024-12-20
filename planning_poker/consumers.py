import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import PokerRoom, Player
import asyncio

class PokerConsumer(AsyncWebsocketConsumer):
    """
    Consommateur pour le planning poker.

    @param AsyncWebsocketConsumer: Classe de consommateur asynchrone.
    """

    async def connect(self):
        """
        @brief Connexion au WebSocket.
        """
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"poker_{self.room_name}"

        self.pseudo = self.scope['session'].get('pseudo', None)
        if not self.pseudo:
            print("ERROR: Aucun pseudo dans la session, fermeture de la connexion.")
            await self.close()
            return

        print(f"DEBUG: Pseudo détecté dans la session : {self.pseudo}")

        try:
            self.room = await sync_to_async(PokerRoom.objects.get)(name=self.room_name)

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

            not_voted = await self.get_not_voted_players()
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "not_voted_update", "not_voted": not_voted}
            )

            backlog = json.loads(self.room.backlog) if self.room.backlog else []
            current_feature = backlog[0] if backlog else None
            if current_feature:
                await self.send(text_data=json.dumps({
                    "type": "feature_update",
                    "feature": current_feature
                }))

            print(f"DEBUG: Nouveau joueur connecté : {self.pseudo} dans {self.room_group_name}")
        except PokerRoom.DoesNotExist:
            await self.close()
            return

    async def disconnect(self, close_code):
        """
        @brief Déconnexion du websocket.

        @param self: Instance de la classe.

        @param close_code: Code de fermeture.

        @return Rien.
        """
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"DEBUG: Channel {self.channel_name} retiré du groupe {self.room_group_name}")

    async def receive(self, text_data):
        """
        @brief Réception de données.

        @param self: Instance de la classe.

        @param text_data: Données textuelles.

        @return Rien.
        """
        data = json.loads(text_data)
        if data['type'] == 'vote':
            await self.handle_vote(data)
        elif data['type'] == 'reveal':
            print("DEBUG: Appel à reveal_votes")
            await self.reveal_votes(data)
        elif data['type'] == 'start_feature':
            await self.start_feature_voting()
        else:
            await self.send(text_data=json.dumps({"type": "error", "message": "Événement inconnu"}))

    async def handle_vote(self, data):
        """
        @brief Gère le vote d'un joueur et vérifie si tous ont voté.

        @param self: Instance de la classe.

        @param data: Données du vote.

        @return Rien.
        """
        player = await sync_to_async(Player.objects.get)(room=self.room, name=data["player"])
        print(f"DEBUG: Avant mise à jour, vote pour {player.name} = {player.vote}")

        player.vote = str(data["vote"]).strip()
        await sync_to_async(player.save)()
        print(f"DEBUG: Après mise à jour, vote pour {player.name} = {player.vote}")

        await asyncio.sleep(0.1)

        not_voted = await self.get_not_voted_players()
        print(f"DEBUG: Liste des joueurs sans vote après mise à jour : {not_voted}")

        all_voted = len(not_voted) == 0

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "player_vote",
                "player": player.name,
                "vote": player.vote,
                "all_voted": all_voted,
                "not_voted": not_voted,
            }
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "not_voted_update",
                "not_voted": not_voted,
            }
        )

        print(f"DEBUG: Player {player.name} voted {player.vote}. All voted: {all_voted}")

    async def reveal_votes(self, event=None):
        """
        Révèle les votes des joueurs et détermine si la condition (majorité ou unanimité) est atteinte.

        @param self: Instance de la classe.
        @param event: Événement.

        @return Rien.
        """
        players = await sync_to_async(list)(Player.objects.filter(room=self.room))
        votes = [{"name": player.name, "vote": str(player.vote).strip()} for player in players]

        if any(vote["vote"] in [None, "None", ""] for vote in votes):
            print("DEBUG: Tous les joueurs n'ont pas encore voté.")
            return

        vote_values = [vote["vote"] for vote in votes]
        mode = self.room.mode

        if mode == 'unanimity':
            condition_met = len(set(vote_values)) == 1
        elif mode == 'absolute_majority':
            if len(vote_values) == 1:
                condition_met = True
            else:
                condition_met = any(vote_values.count(v) > len(vote_values) / 2 for v in set(vote_values))
        else:
            condition_met = False

        print(f"DEBUG: Votes: {votes}, Condition atteinte: {condition_met}")

        backlog = json.loads(self.room.backlog) if self.room.backlog else []
        all_features = json.loads(self.room.all_features) if self.room.all_features else []

        if condition_met:
            if vote_values[0] == "200":
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "redirect",
                        "url": f"/export/{self.room_name}/",
                    }
                )
                return

            if backlog:
                current_feature = backlog.pop(0)
                current_feature["priority"] = vote_values[0]
                all_features.append(current_feature)

                self.room.backlog = json.dumps(backlog)
                self.room.all_features = json.dumps(all_features)
                await sync_to_async(self.room.save)()

                next_feature = backlog[0] if backlog else None
                await self.reset_votes()

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "reveal",
                        "votes": votes,
                        "unanimity": True,
                    }
                )
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "not_voted_update",
                        "not_voted": await self.get_not_voted_players(),
                    }
                )

                if next_feature:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "feature_update",
                            "feature": next_feature,
                        }
                    )
                else:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "final_backlog",
                            "final_backlog": all_features,
                        }
                    )
        else:
            await self.reset_votes()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "not_voted_update",
                    "not_voted": await self.get_not_voted_players(),
                }
            )

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "reveal",
                    "votes": votes,
                    "unanimity": False,
                    "next_feature": backlog[0],
                }
            )

    async def start_feature_voting(self):
        """
        @brief Démarre le vote pour la première fonctionnalité du backlog.
        """
        backlog = json.loads(self.room.backlog) if self.room.backlog else []
        if backlog:
            current_feature = backlog[0]
            print(f"DEBUG: Début du vote pour la feature : {current_feature}")
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "feature_update", "feature": current_feature}
            )
        else:
            print("DEBUG: Backlog vide.")
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "final_backlog", "final_backlog": []}
            )


    async def player_vote(self, event):
        """
        @brief Envoie le vote d'un joueur à tous les joueurs.
        
        @param self: Instance de la classe.
        
        @param event: Événement.

        @return Rien.
        """
        await self.send(text_data=json.dumps({
            "type": "vote",
            "player": event["player"],
            "vote": event["vote"],
            "all_voted": event["all_voted"],
            "not_voted": event["not_voted"],
        }))

    async def not_voted_update(self, event):
        """
        @brief Met à jour la liste des joueurs sans vote.

        @param self: Instance de la classe.

        @param event: Événement.

        @return Rien.
        """
        await self.send(text_data=json.dumps(event))

    async def feature_update(self, event):
        """
        @brief Envoie une nouvelle fonctionnalité à tous les joueurs.

        @param self: Instance de la classe.

        @param event: Événement.

        @return Rien.
        """
        await self.send(text_data=json.dumps({
            "type": "feature_update",
            "feature": event.get("feature"),
            "votes": event.get("votes", []),
            "unanimity": event.get("unanimity", False),
        }))

    async def reset_votes(self):
        """
        @brief Réinitialise les votes de tous les joueurs.

        @param self: Instance de la classe.

        @return Rien.
        """
        players = await sync_to_async(list)(Player.objects.filter(room=self.room))
        for player in players:
            player.vote = None
            await sync_to_async(player.save)()
        print("DEBUG: Votes réinitialisés.")

    async def get_not_voted_players(self):
        """
        @brief Récupère les joueurs qui n'ont pas encore voté.

        @return Liste des noms des joueurs sans vote.
        """
        players = await sync_to_async(list)(Player.objects.filter(room=self.room))
        return [player.name for player in players if player.vote is None]

    async def final_backlog(self, event):
        """
        @brief Envoie le backlog final avec toutes les fonctionnalités et leurs priorités.

        @param self: Instance de la classe.

        @param event: Événement.

        @return Rien.
        """
        if event.get("url"):
            await self.send(text_data=json.dumps({
                "type": "final_backlog",
                "url": event["url"],
            }))
            print(f"DEBUG: Redirection vers {event['url']}")
        elif event.get("final_backlog"):
            await self.send(text_data=json.dumps({
                "type": "final_backlog",
                "final_backlog": event["final_backlog"],
            }))
            print(f"DEBUG: Résultat final envoyé : {event['final_backlog']}")


    async def reveal(self, event):
        """
        @brief Révèle les votes des joueurs.

        @param self: Instance de la classe.

        @param event: Événement.

        @return Rien.
        """
        print("DEBUG: Révélation des votes.")
        print(event)
        await self.send(text_data=json.dumps({
            "type": "reveal",
            "votes": event.get("votes", []),
            "unanimity": event.get("unanimity"),
        }))
        print("DEBUG: Révélation des votes envoyée.")

    async def redirect(self, event):
        """
        @brief Redirige tous les joueurs vers la page d'exportation JSON.

        @param self: Instance de la classe.
        @param event: Événement contenant l'URL de redirection.

        @return Rien.
        """
        await self.send(text_data=json.dumps({
            "type": "redirect",
            "url": event["url"],
        }))
