from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create-room/', views.create_room, name='create_room'),
    path('poker/<str:room_name>/', views.join_room, name='join_room'),
]
