from django.urls import path
from planning_poker.consumers import PokerConsumer

# route pour les rooms
websocket_urlpatterns = [
    path('ws/poker/<str:room_name>/', PokerConsumer.as_asgi()),
]
