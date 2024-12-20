from django.urls import path
from . import views

# routes 
urlpatterns = [
    path('', views.home, name='home'),
    path('poker/create/', views.create_room, name='create_room'),
    path('poker/<str:room_name>/join/', views.join_room, name='join_room'),
    path('poker/<str:room_name>/', views.room, name='room'),
    path('final_backlog/<str:room_name>/', views.final_backlog_view, name='final_backlog'),
    path('export/<str:room_name>/', views.export_backlog, name='export_backlog'),
    path('create-backlog/', views.create_backlog_view, name='create_backlog'),
    path('validate-backlog/', views.validate_backlog_view, name='validate_backlog'),

]