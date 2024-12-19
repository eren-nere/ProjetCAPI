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
        Connexion au websocket.

        @param self: Instance de la classe.
        """
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"poker_{self.room_name}"

        self.pseudo = self.scope['session'].get('pseudo', None)
        if not self.pseudo:
            print("ERROR: Aucun pseudo dans la session, fermeture de la connexion.")
            await self.close()
            return

        print(f"DEBUG: Pseudo détecté dans la session : {self.pseudo}")

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        try:
            self.room = await sync_to_async(PokerRoom.objects.get)(name=self.room_name)
            await sync_to_async(Player.objects.filter(room=self.room, vote=None).delete)()
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

        if self.pseudo == self.room.creator:
            await self.start_feature_voting()

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "not_voted_update", "not_voted": await self.get_not_voted_players()}
        )
        print(f"DEBUG: Nouveau channel connecté {self.channel_name} au groupe {self.room_group_name}")

    async def disconnect(self, close_code):
        """
        Déconnexion du websocket.

        @param self: Instance de la classe.

        @param close_code: Code de fermeture.
        """
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"DEBUG: Channel {self.channel_name} retiré du groupe {self.room_group_name}")

    async def receive(self, text_data):
        """
        Réception de données.

        @param self: Instance de la classe.

        @param text_data: Données textuelles.
        """
        data = json.loads(text_data)
        if data['type'] == 'vote':
            await self.handle_vote(data)
        elif data['type'] == 'reveal':
            print("DEBUG: Appel à reveal_votes")  # Log pour vérifier l'appel
            await self.reveal_votes(data)
        elif data['type'] == 'start_feature':
            await self.start_feature_voting()
        else:
            await self.send(text_data=json.dumps({"type": "error", "message": "Événement inconnu"}))

    async def handle_vote(self, data):
        """
        Gère le vote d'un joueur et vérifie si tous ont voté.

        @param self: Instance de la classe.

        @param data: Données du vote.
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
        print(f"DEBUG: Player {player.name} voted {player.vote}. All voted: {all_voted}")

    async def reveal_votes(self, event=None):
        """
        Révèle les votes des joueurs et détermine si l'unanimité est atteinte.

        @param self: Instance de la classe.

        @param event: Événement.
        """
        players = await sync_to_async(list)(Player.objects.filter(room=self.room))
        votes = [{"name": player.name, "vote": str(player.vote).strip()} for player in players]

        if any(vote["vote"] in [None, "None", ""] for vote in votes):
            print("DEBUG: Tous les joueurs n'ont pas encore voté.")
            return

        vote_values = [vote["vote"] for vote in votes]
        unanimity = len(set(vote_values)) == 1

        print(f"DEBUG: Votes: {votes}, Unanimité: {unanimity}")

        backlog = json.loads(self.room.backlog)
        all_features = json.loads(self.room.all_features) if self.room.all_features else []

        if unanimity:
            if len(backlog) > 0:
                current_feature = backlog.pop(0)
                current_feature["priority"] = vote_values[0]
                all_features.append(current_feature)

                self.room.backlog = json.dumps(backlog)
                self.room.all_features = json.dumps(all_features)
                await sync_to_async(self.room.save)()

                next_feature = backlog[0] if backlog else False
                await self.reset_votes()
                if not next_feature:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "final_backlog",
                            "url": "/final_backlog/" + self.room_name + "/",
                        }
                    )
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "reveal",
                        "votes": votes,
                        "unanimity": True,
                        "next_feature": next_feature,
                    }
                )
                if next_feature:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {"type": "feature_update", "feature": next_feature}
                    )


                print(f"DEBUG: Unanimité atteinte. Prochaine feature : {next_feature}")
            else:
                print("DEBUG: Backlog vide, fin des votes.")
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "final_backlog",
                        "final_backlog": all_features,
                    }
                )
        else:
            print("DEBUG: Pas d'unanimité. Recommencer le vote.")
            await self.reset_votes()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "reveal",
                    "votes": votes,
                    "unanimity": False,

                }
            )

    async def start_feature_voting(self):
        """
        Démarre le vote pour la première fonctionnalité du backlog.

        @param self: Instance de la classe.
        """
        backlog = json.loads(self.room.backlog)
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
        Envoie le vote d'un joueur à tous les joueurs.
        
        @param self: Instance de la classe.
        
        @param event: Événement.
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
        Met à jour la liste des joueurs sans vote.

        @param self: Instance de la classe.

        @param event: Événement.
        """
        await self.send(text_data=json.dumps(event))

    async def feature_update(self, event):
        """
        Envoie une nouvelle fonctionnalité à tous les joueurs.

        @param self: Instance de la classe.

        @param event: Événement.
        """
        await self.send(text_data=json.dumps({
            "type": "feature_update",
            "feature": event.get("feature"),
            "votes": event.get("votes", []),
            "unanimity": event.get("unanimity", False),
        }))

    async def reset_votes(self):
        """
        Réinitialise les votes de tous les joueurs.

        @param self: Instance de la classe.
        """
        players = await sync_to_async(list)(Player.objects.filter(room=self.room))
        for player in players:
            player.vote = None
            await sync_to_async(player.save)()
        print("DEBUG: Votes réinitialisés.")

    async def get_not_voted_players(self):
        """
        Récupère les joueurs qui n'ont pas encore voté.

        @param self: Instance de la classe.
        """
        players = await sync_to_async(list)(Player.objects.filter(room=self.room))
        print(f"DEBUG: Votes actuels des joueurs : {[{'name': p.name, 'vote': p.vote} for p in players]}")
        return [player.name for player in players if player.vote is None]

    async def final_backlog(self, event):
        """
        Envoie le backlog final avec toutes les fonctionnalités et leurs priorités.

        @param self: Instance de la classe.

        @param event: Événement.
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
        Révèle les votes des joueurs.

        @param self: Instance de la classe.

        @param event: Événement.
        """
        print("DEBUG: Révélation des votes.")
        print(event)
        await self.send(text_data=json.dumps({
            "type": "reveal",
            "votes": event.get("votes", []),
            "unanimity": event.get("unanimity"),
        }))
        print("DEBUG: Révélation des votes envoyée.")