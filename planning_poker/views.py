from django.shortcuts import render, redirect
from .models import PokerRoom
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

def home(request):
    """
    @brief Affiche la page d'accueil.

    @param request L'objet HTTP request.

    @return Rend le template 'home.html'.
    """
    return render(request, 'home.html')


def create_room(request):
    """
    @brief Gère la création d'une room.

    @details Cette fonction permet à un utilisateur de créer une nouvelle room ou
    de rejoindre une room existante. Elle enregistre le pseudo de l'utilisateur dans la session.

    @param request L'objet HTTP request.

    @return Rend le template 'create_room.html' ou redirige vers la room créée.
    """
    if request.method == "POST":
        room_name = request.POST.get('room_name')
        pseudo = request.POST.get('pseudo')

        logger.info(f"Création de la room: {room_name} avec le pseudo: {pseudo}")

        if not room_name or not pseudo:
            return render(request, 'create_room.html', {'error': 'Nom de room et pseudo requis.'})

        room, created = PokerRoom.objects.get_or_create(name=room_name, creator=pseudo)

        logger.info(f"Room {'créée' if created else 'existante'} : {room.name}, créateur : {room.creator}")

        request.session['pseudo'] = pseudo
        logger.info(f"Pseudo enregistré dans la session: {request.session.get('pseudo')}")

        return redirect('room', room_name=room_name)

    return render(request, 'create_room.html')


def join_room(request, room_name):
    """
    @brief Permet à un utilisateur de rejoindre une room existante.

    @details Si un pseudo est fourni, il est enregistré dans la session. Sinon,
    un message d'erreur est affiché.

    @param request L'objet HTTP request.
    @param room_name Le nom de la room à rejoindre.

    @return Rend le template 'join_room.html' ou redirige vers la room.
    """
    if request.method == "POST":
        pseudo = request.POST.get('pseudo')
        if not pseudo:
            return render(request, 'join_room.html', {'error': 'Un pseudo est requis.'})

        request.session['pseudo'] = pseudo
        return redirect(reverse('room', kwargs={'room_name': room_name}))

    return render(request, 'join_room.html', {'room_name': room_name})


def room(request, room_name):
    """
    @brief Affiche la room.

    @details Cette vue affiche la room à l'utilisateur. Si le pseudo n'est pas dans la session
    ou si la room n'existe pas, elle redirige vers la page de création.

    @param request L'objet HTTP request.
    @param room_name Le nom de la room.

    @return Rend le template 'room.html'.
    """
    pseudo = request.session.get('pseudo', None)
    if not pseudo:
        return redirect('create_room')

    try:
        room = PokerRoom.objects.get(name=room_name)
    except PokerRoom.DoesNotExist:
        return redirect('create_room')

    creator = room.creator

    return render(request, 'room.html', {
        'room_name': room_name,
        'pseudo': pseudo,
        'creator': creator,
    })
