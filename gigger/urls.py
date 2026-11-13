from django.urls import re_path
from . import views

urlpatterns = [
    re_path('^$', views.gigs, name='home'),
    re_path('^gig/?$', views.gigs, name='gigs'),
    re_path('^gig/create/?$', views.create_gig, name='create_gig'),
    re_path('^gig/(?P<gig_id>[0-9]+)/edit/?$', views.edit_gig, name='edit_gig'),
    re_path('^gig/(?P<gig_id>[0-9]+)/?$', views.view_gig, name='view_gig'),
    re_path('^gig/(?P<gig_id>[0-9]+)/fee/?$', views.custom_fee, name='custom_fee'),
    re_path('^gig/(?P<gig_id>[0-9]+)/assign_player/?$', views.assign_player, name='assign_player'),
    re_path('^gig/(?P<gig_id>[0-9]+)/availability/?$', views.availability, name='availability'),
    re_path('^me/?$', views.me, name='me'),
    re_path('^me/gigs$', views.my_gigs, name='my_gigs'),
    re_path('^me/history$', views.my_history, name='my_history'),
    re_path('^me/availability$', views.my_missing_availability, name='my_missing_availability'),
    re_path('^players$', views.manage_players, name='manage_players'),
    re_path('^players/(?P<player_id>[0-9]+)/calendar.ics$', views.player_calendar, name='player_calendar'),
    re_path('^dances$', views.dances, name='dances'),
    re_path('^whoami$', views.who_am_i, name='who_am_i'),
    re_path('^iam/(?P<player_id>[0-9]+)$', views.i_am, name='i_am'),
]