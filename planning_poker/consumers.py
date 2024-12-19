import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import PokerRoom, Player


class PokerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"poker_{self.room_name}"  

        self.pseudo = self.scope['session'].get('pseudo', None)
        if not self.pseudo:
            await self.close()
            return

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
        print(f"Nouveau channel connecté {self.channel_name} au grp {self.room_group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"Channel {self.channel_name} retire du groupe {self.room_group_name}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'vote':
            await self.handle_vote(data)
        elif data['type'] == 'reveal':
            print("Appel à reveal_votes") 
            await self.reveal_votes(data)
        elif data['type'] == 'start_feature':
            await self.start_feature_voting()
        else:
            await self.send(text_data=json.dumps({"type": "error", "message": "Événement inconnu"}))

    async def handle_vote(self, data):
        player = await sync_to_async(Player.objects.get)(room=self.room, name=data["player"])
        player.vote = str(data["vote"]).strip()
        await sync_to_async(player.save)()

        not_voted = await self.get_not_voted_players()
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
        print(f"Player {player.name} voted {player.vote}. All voted: {all_voted}")

    async def reveal_votes(self, event=None):
        players = await sync_to_async(list)(Player.objects.filter(room=self.room))
        votes = [{"name": player.name, "vote": str(player.vote).strip()} for player in players]


        if any(vote["vote"] in [None, "None", ""] for vote in votes):
            print("Tous les joueurs n'ont pas encore voté")
            return

        vote_values = [vote["vote"] for vote in votes]
        unanimity = len(set(vote_values)) == 1

        print(f"Votes: {votes}, Unanimity: {unanimity}")


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


                print(f"Unanimité atteinte. Prochaine feature : {next_feature}")
            else:
                print("Backlog vide, fin des votes")
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "final_backlog",
                        "final_backlog": all_features,
                    }
                )
        else:
            print("Pas d'unanimité. Recommencer le vote")
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
        backlog = json.loads(self.room.backlog)
        if backlog:
            current_feature = backlog[0]
            print(f"Debut du vote pour la feature : {current_feature}")
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "feature_update", "feature": current_feature}
            )
        else:
            print("Backlog vide")
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "final_backlog", "final_backlog": []}
            )

    async def player_vote(self, event):
        await self.send(text_data=json.dumps({
            "type": "vote",
            "player": event["player"],
            "vote": event["vote"],
            "all_voted": event["all_voted"],
            "not_voted": event["not_voted"],
        }))

    async def not_voted_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def feature_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "feature_update",
            "feature": event.get("feature"),
            "votes": event.get("votes", []),
            "unanimity": event.get("unanimity", False),
        }))

    async def reset_votes(self):
        players = await sync_to_async(list)(Player.objects.filter(room=self.room))
        for player in players:
            player.vote = None
            await sync_to_async(player.save)()
        print("Votes reinitialiser")

    async def get_not_voted_players(self):
        players = await sync_to_async(list)(Player.objects.filter(room=self.room))
        return [player.name for player in players if player.vote is None]

    async def final_backlog(self, event):
        if event.get("url"):
            await self.send(text_data=json.dumps({
                "type": "final_backlog",
                "url": event["url"],
            }))
            print(f"Redirection vers {event['url']}")
        elif event.get("final_backlog"):
            await self.send(text_data=json.dumps({
                "type": "final_backlog",
                "final_backlog": event["final_backlog"],
            }))
            print(f"Resultat final envoye : {event['final_backlog']}")


    async def reveal(self, event):
        print("Révélation des votes")
        print(event)
        await self.send(text_data=json.dumps({
            "type": "reveal",
            "votes": event.get("votes", []),
            "unanimity": event.get("unanimity"),
        }))
        print("Revelation des votes envoyer")