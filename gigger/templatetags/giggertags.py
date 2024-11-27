from ..models import *

from django import template


register = template.Library()

@register.simple_tag
def get_player_availability(player_id, gig_id):
    return AvailabilityResponse.objects.filter(player_id=player_id, gig_id=gig_id).first() or "Availability unknown"

@register.simple_tag
def get_player_assigned_to_instrument(gig_id, instrument_id):
    pag = PlayingAtGig.objects.filter(gig_id=gig_id, instrument_id=instrument_id).first()
    if pag is None:
        return -1
    else:
        return pag.player.id

@register.simple_tag   
def get_players_on_gig(gig_id):
    return PlayingAtGig.objects.filter(gig_id=gig_id).order_by('instrument')

@register.simple_tag(takes_context=True)
def absolute_url(context, relative_url):
  request = context['request']
  return request.build_absolute_uri(relative_url)

@register.simple_tag
def emoji_from_bool(b):
    return '✅' if b else '❌'