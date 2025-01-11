from django.urls import re_path
from . import views

urlpatterns = [
    re_path('^$', views.gigs, name='home'),
    re_path('^gig/?$', views.gigs, name='gigs'),
    re_path('^gig/create/?$', views.create_gig, name='create_gig'),
    re_path('^gig/(?P<gig_id>[0-9]+)/edit/?$', views.edit_gig, name='edit_gig'),
    re_path('^gig/(?P<gig_id>[0-9]+)/?$', views.view_gig, name='view_gig'),
    re_path('^gig/(?P<gig_id>[0-9]+)/assign_player/?$', views.assign_player, name='assign_player'),
    re_path('^gig/(?P<gig_id>[0-9]+)/availability/?$', views.availability_entry_point, name='availability_entry_point'),
    re_path('^gig/(?P<gig_id>[0-9]+)/availability/(?P<player_id>[0-9]+)/?$', views.availability_form, name='availability_form'),
    re_path('^gig/(?P<gig_id>[0-9]+)/availability/(?P<player_id>[0-9]+)/set/?$', views.availability_set, name='availability_set'),
    re_path('^me/gigs$', views.my_gigs, name='my_gigs'),
    re_path('^me/availability$', views.my_missing_availability, name='my_missing_availability'),
    re_path('^whoami$', views.who_am_i, name='who_am_i'),
    re_path('^iam/(?P<player_id>[0-9]+)$', views.i_am, name='i_am'),
]