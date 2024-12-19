from django.shortcuts import render, redirect, get_object_or_404
from .models import PokerRoom
import json
import logging
from django.urls import reverse

logger = logging.getLogger(__name__)

def create_room(request):
    """
    @brief Permet a un utilisateur de creer une room.

    @param request L'objet HTTP.

    @return Rend la template 'create_room.html' ou redirige vers la room.
    """
    if request.method == "POST":
        room_name = request.POST.get('room_name')
        pseudo = request.POST.get('pseudo')
        mode = request.POST.get('mode')
        backlog = request.POST.get('backlog')

        # verifie que tous les champs sont rempli
        if not room_name or not pseudo or not mode or not backlog:
            return render(request, 'create_room.html', {
                'error': 'Tous les champs sont requis.'
            })

        # valide que le backlog soit un JSON
        try:
            backlog_json = json.loads(backlog)
            #verifie que chaque element a une cle 'feature'
            if not all(isinstance(item, dict) and 'feature' in item for item in backlog_json):
                raise ValueError("Le JSON doit contenir des objets avec une cle 'feature'.")
        except json.JSONDecodeError:
            return render(request, 'create_room.html', {
                'error': "Le backlog doit etre un JSON valide."
            })
        except ValueError as e:
            return render(request, 'create_room.html', {
                'error': str(e)
            })

        # cree ou recuperer la salle et stock le backlog dans la room
        room, created = PokerRoom.objects.get_or_create(
            name=room_name,
            creator=pseudo,
            defaults={'mode': mode, 'backlog': backlog_json}
        )

        request.session['pseudo'] = pseudo
        return redirect('room', room_name=room_name)

    return render(request, 'create_room.html')


def home(request):
    """
    @brief Affiche la page d'accueil.

    @param request Lobjet HTTP request.

    @return Rend la template 'home.html'.
    """
    return render(request, 'home.html')


def join_room(request, room_name):
    """
    @brief Permet a un utilisateur de rejoindre une room existante.

    @param request Lobjet HTTP request.
    @param room_name Le nom de la room a rejoindre.

    @return Rend la template 'join_room.html' ou redirige vers la room.
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

    @param request L'objet HTTP request.
    @param room_name est le nom de la room.

    
    @return Rend la template 'room.html'.
    """
    pseudo = request.session.get('pseudo', None)
    if not pseudo:
        return redirect('create_room')

    try:
        room = PokerRoom.objects.get(name=room_name)
    except PokerRoom.DoesNotExist:
        return redirect('create_room')

    creator = room.creator
    backlog = room.backlog or []

    # Passe le backlog directment a la template
    return render(request, 'room.html', {
        'room_name': room_name,
        'pseudo': pseudo,
        'creator': creator,
        'backlog': backlog,
    })


def final_backlog_view(request, room_name):
    """
    @brief Affiche le backlog final.

    @param request L'objet HTTP.

    @param room_name Le nom de la room.
    """
    #Recuperer la salle selon son nom
    poker_room = get_object_or_404(PokerRoom, name=room_name)

    # Charge le JSON depuis le champ all_features
    final_backlog = json.loads(poker_room.all_features)

    # Passe les donnees a la template
    return render(request, 'final_backlog.html', {'final_backlog': final_backlog})
