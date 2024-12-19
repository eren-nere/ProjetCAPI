from django.db import models
import json

class PokerRoom(models.Model):
    # Modele representant une salle de poker
    name = models.CharField(max_length=50, unique=True)
    creator = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    mode = models.CharField(max_length=20, choices=[('unanimity', 'Unanimité'), ('absolute_majority', 'Majorité absolue')], default='unanimity')
    backlog = models.TextField()  #stock  le backlog sous forme JSON
    all_features = models.TextField(default="[]")  # stock toutes les fonctionnalité finales

    def save(self, *args, **kwargs):
        # Converti backlog en JSON si backlog est une liste
        if isinstance(self.backlog, list):
            self.backlog = json.dumps(self.backlog)
        super().save(*args, **kwargs)

# Modele representant un joueur dans une room
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
