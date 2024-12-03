from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('poker/create/', views.create_room, name='create_room'),
    path('poker/<str:room_name>/join/', views.join_room, name='join_room'),
    path('poker/<str:room_name>/', views.room, name='room'),
]
