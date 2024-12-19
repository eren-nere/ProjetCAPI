from django.test import TestCase
from planning_poker.models import PokerRoom

class PokerRoomModelTest(TestCase):
    """
    Test pour la classe PokerRoom.
    
    @param TestCase: Classe de test Django.
    """
    def test_create_room(self):
        """
        Test de création de salle.

        @param self: Instance de la classe.
        """
        room = PokerRoom.objects.create(
            name="TestRoom",
            creator="TestCreator",
            backlog="[]",
        )
        self.assertEqual(room.name, "TestRoom")
        self.assertEqual(room.creator, "TestCreator")
