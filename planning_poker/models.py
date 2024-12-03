from django.db import models

class PokerRoom(models.Model):
    """
    @brief Modèle représentant une room.

    @details Une room contient un nom unique, un créateur, et une date de création.
    Elle est associée à plusieurs joueurs via le modèle Player.
    """
    name = models.CharField(max_length=50, unique=True)
    """@var name
    @brief Nom unique de la room.
    """

    creator = models.CharField(max_length=50)
    """@var creator
    @brief Nom ou identifiant du créateur de la room.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    """@var created_at
    @brief Date et heure de création de la room.
    """


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
