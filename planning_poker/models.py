from django.db import models
import json


class PokerRoom(models.Model):
    name = models.CharField(max_length=50, unique=True)
    creator = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    mode = models.CharField(max_length=20, choices=[('unanimity', 'Unanimité'), ('absolute_majority', 'Majorité absolue')], default='unanimity')
    backlog = models.TextField()
    all_features = models.TextField(default="[]")



    def save(self, *args, **kwargs):
        if isinstance(self.backlog, list):
            self.backlog = json.dumps(self.backlog)
        super().save(*args, **kwargs)

class Player(models.Model):
    """
    @brief Modèle représentant un joueur dans une room.

    @details Un joueur est associé à une room, possède un nom et un vote (optionnel).
    """
    room = models.ForeignKey(PokerRoom, on_delete=models.CASCADE, related_name='players')
    """@var room
    @brief Référence à la room à laquelle appartient le joueur.
    """

    name = models.CharField(max_length=50)
    """@var name
    @brief Nom ou pseudo du joueur.
    """

    vote = models.IntegerField(null=True, blank=True)
    """@var vote
    @brief Vote du joueur, peut être `null` si le joueur n'a pas encore voté.
    """
