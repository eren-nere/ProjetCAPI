from django.shortcuts import render, redirect, get_object_or_404
from .models import PokerRoom
import json
import logging
from django.urls import reverse
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def create_room(request):
    """
    @brief Permet à un utilisateur de créer une room.

    @param request L'objet HTTP.

    @return Rend la template 'create_room.html' ou redirige vers la room.
    """
    if request.method == "POST":
        room_name = request.POST.get('room_name')
        pseudo = request.POST.get('pseudo')
        mode = request.POST.get('mode')
        backlog = request.POST.get('backlog')

        if not room_name or not pseudo or not mode or not backlog:
            return render(request, 'create_room.html', {
                'error': 'Tous les champs sont requis.'
            })

        try:
            backlog_json = json.loads(backlog)

            if 'backlog' not in backlog_json or not isinstance(backlog_json['backlog'], list):
                raise ValueError("Le JSON doit contenir un champ 'backlog' avec une liste d'objets.")
            if not all(isinstance(item, dict) and 'feature' in item for item in backlog_json['backlog']):
                raise ValueError("Tous les éléments de 'backlog' doivent être des objets avec une clé 'feature'.")

            if 'all_features' in backlog_json:
                if not isinstance(backlog_json['all_features'], list):
                    raise ValueError("Le champ 'all_features', s'il est présent, doit être une liste d'objets.")
                if not all(isinstance(item, dict) and 'feature' in item for item in backlog_json['all_features']):
                    raise ValueError(
                        "Tous les éléments de 'all_features' doivent être des objets avec une clé 'feature'.")
        except json.JSONDecodeError:
            return render(request, 'create_room.html', {
                'error': "Le backlog doit être un JSON valide."
            })
        except ValueError as e:
            return render(request, 'create_room.html', {
                'error': str(e)
            })

        room, created = PokerRoom.objects.get_or_create(
            name=room_name,
            creator=pseudo,
            defaults={
                'mode': mode,
                'backlog': json.dumps(backlog_json['backlog']),
                'all_features': json.dumps(backlog_json.get('all_features', []))
            }
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
    backlog = json.loads(room.backlog) if room.backlog else []
    all_features = json.loads(room.all_features) if room.all_features else []

    return render(request, 'room.html', {
        'room_name': room_name,
        'pseudo': pseudo,
        'creator': creator,
        'backlog': backlog,
        'all_features': all_features,
    })



def final_backlog_view(request, room_name):
    """
    @brief Affiche le backlog final.

    @param request L'objet HTTP.

    @param room_name Le nom de la room.
    """
    poker_room = get_object_or_404(PokerRoom, name=room_name)

    final_backlog = json.loads(poker_room.all_features)

    return render(request, 'final_backlog.html', {'final_backlog': final_backlog})

def export_backlog(request, room_name):
    """
    @brief Exporte le backlog (fonctionnalités passées et à venir) au format JSON.

    @param request L'objet HTTP.
    @param room_name Le nom de la room.

    @return Rend la page 'export_backlog.html' avec le lien de téléchargement.
    """
    poker_room = get_object_or_404(PokerRoom, name=room_name)

    backlog = json.loads(poker_room.backlog) if poker_room.backlog else []
    all_features = json.loads(poker_room.all_features) if poker_room.all_features else []

    export_data = {
        "backlog": backlog,
        "all_features": all_features
    }

    return render(request, 'export_backlog.html', {
        'export_data': json.dumps(export_data, indent=2),
        'room_name': room_name
    })

def create_backlog_view(request):
    """
    @brief Affiche la page de création de backlog.

    @param request: Objet de requête HTTP.

    @return Rend la page HTML de création de backlog.
    """
    return render(request, 'create_backlog.html')


def validate_backlog_view(request):
    """
    @brief Valide le JSON généré par l'utilisateur.

    @param request: Objet de requête HTTP.

    @return Renvoie un message de validation ou d'erreur.
    """
    if request.method == "POST":
        try:
            backlog_data = json.loads(request.body)
            if not all(isinstance(item, dict) and 'feature' in item for item in backlog_data.get('backlog', [])):
                raise ValueError("Le JSON doit contenir des objets avec une clé 'feature'.")

            return JsonResponse({"success": True, "message": "Backlog valide !"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Le JSON est invalide."}, status=400)
        except ValueError as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
    else:
        return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)

