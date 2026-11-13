from .models import Player


def current_player(request):
    """Make the player using the site (if we know who they are) available to every template, e.g. for the header"""
    try:
        return {'current_player': Player.objects.get(id=request.session['uid'])}
    except (KeyError, Player.DoesNotExist):
        return {'current_player': None}
