from django.urls import path
from planning_poker.consumers import PokerConsumer

websocket_urlpatterns = [
    path('ws/poker/<str:room_name>/', PokerConsumer.as_asgi()),
]
