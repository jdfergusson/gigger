import datetime
from urllib.parse import quote, urlencode

from django.shortcuts import render
from django.http import (
    HttpResponse,
    HttpResponseNotFound,
    JsonResponse,
    QueryDict,
)
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import (
    render,
    get_object_or_404,
    redirect,
)
from django import forms

from .models import *

class CreateGigForm(forms.ModelForm):
    class Meta:
        model = Gig
        fields = ["title", "date"]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class EditGigForm(forms.ModelForm):
    required_instruments = forms.ModelMultipleChoiceField(
        queryset=Instrument.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False)
    
    class Meta:
        model = Gig
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }
        fields = ["status", "date", "title", "location", "contact_name", "contact_email", "contact_method",
                  "handled_by", "start_time", "details", 
                  "paid", "cost_per_player", "permit_custom_fee", "cost_per_car",
                  "number_of_cars", "cost_extras",  "required_instruments"]
        labels = {
            'cost_per_player': 'Default cost per player',
            'permit_custom_fee': 'Allow custom fee',
        }
    

def _get_user_or_none(request):
    # Add user to context if it exists
    try:
        uid = request.session['uid']
        return Player.objects.get(id=uid)
    except (KeyError, Player.DoesNotExist):
        return None


# Create your views here.
def create_gig(request):
    if request.method == "POST":
        form = CreateGigForm(request.POST)
        if form.is_valid():

            new_gig = Gig(**form.cleaned_data)
            new_gig.save()

            new_gig.required_instruments.set([i for i in Instrument.objects.all()])
            new_gig.cost_extras = 10
            new_gig.save()
            return redirect(reverse('edit_gig', args=[new_gig.id]))
    else:
        form = CreateGigForm()

    # A new form, or one that failed validation and now carries its errors
    return render(request, "create_gig.html", {"form": form})


def edit_gig(request, gig_id):
    gig = get_object_or_404(Gig, id=gig_id)

    if request.method == "POST":
        form = EditGigForm(request.POST, instance=gig)
        if form.is_valid():
            form.save()
            return redirect(reverse('view_gig', args=[gig.id]))
        # Validation copies the rejected values onto the gig; reload it so the heading shows the saved title.
        # The form redisplays from the submitted data, so this doesn't lose anything typed.
        gig.refresh_from_db()
    else:
        form = EditGigForm(instance=gig)

    # A fresh form, or one that failed validation and now carries its errors
    return render(request, "edit_gig.html", {"form": form, "gig": gig})
    

def view_gig(request, gig_id):
    gig = get_object_or_404(Gig, id=gig_id)
    availability = AvailabilityResponse.objects.filter(gig=gig).order_by('availability')
    user = _get_user_or_none(request)
    return render(request, "gig.html", {
        "gig": gig, 
        "availability": availability,
        "user": user,    
    })


def _get_custom_fee(gig, player):
    return CustomFee.objects.filter(gig=gig, player=player).first() or CustomFee(gig=gig, player=player)


def _save_custom_fee(gig, player, data):
    """Save a fee choice: data['choice'] is 'default' or 'custom', with an optional data['custom_fee']"""
    defaults = {'wants_standard_fee': data.get('choice') != 'custom'}
    if data.get('custom_fee'):
        # Keep the previous custom fee when switching to the default, so it comes back if they switch again
        defaults['custom_fee'] = int(data['custom_fee'])
    CustomFee.objects.update_or_create(gig=gig, player=player, defaults=defaults)


def custom_fee(request, gig_id):
    gig = get_object_or_404(Gig, id=gig_id)
    player = _get_user_or_none(request)

    if request.method == "POST":
        # Each change is saved via ajax as soon as it is made
        if player is None:
            return JsonResponse({'success': False}, status=403)
        _save_custom_fee(gig, player, request.POST)
        return JsonResponse({'success': True})

    if player is None:
        return redirect(_who_am_i_url(request.path))

    return render(request, "custom_fee.html", {"gig": gig, "player": player, "fee": _get_custom_fee(gig, player)})


def assign_player(request, gig_id):
    if request.method != 'POST':
        return HttpResponseNotFound()
    
    player_id = request.POST.get('player_id', -1)
    instrument_id = instrument_id=request.POST['instrument_id']
    try:
        player = Player.objects.get(id=player_id)
        pag, created = PlayingAtGig.objects.update_or_create(
            gig_id=gig_id, 
            instrument_id=instrument_id, 
            defaults={"player": player}
        )
        pag.save()
    except Player.DoesNotExist:
        try:
            pag = PlayingAtGig.objects.get(gig_id=gig_id, instrument_id=instrument_id)
            pag.delete()
        except PlayingAtGig.DoesNotExist:
            # This is fine
            pass

    return JsonResponse({'success': True})



def gigs(request):
    context = {
        'incomplete_gigs': Gig.objects.filter(status__in=[Gig.Status.CONFIRMED, Gig.Status.PROPOSED]).order_by('date'),
        'complete_gigs': Gig.objects.filter(status=Gig.Status.DONE).order_by('-date'),
        'cancelled_gigs': Gig.objects.filter(status=Gig.Status.CANCELLED).order_by('date'),
    }
    return render(request, "gigs.html", context)


def me(request):
    user = _get_user_or_none(request)

    if user is None:
        return redirect(reverse('who_am_i'))

    # Calendar apps subscribe to webcal:// links; Google and Outlook take the feed as a parameter
    feed_url = request.build_absolute_uri(reverse('player_calendar', args=[user.id]))
    webcal_url = 'webcal://' + feed_url.split('://', 1)[1]
    context = {
        'user': user,
        'calendar_url': webcal_url,
        'google_calendar_url': 'https://calendar.google.com/calendar/r?cid=' + quote(webcal_url, safe=''),
        'outlook_calendar_url': 'https://outlook.live.com/calendar/0/addfromweb?url=' + quote(feed_url, safe='')
            + '&name=' + quote(f'NM Gigs - {user.name}', safe=''),
    }
    return render(request, "me.html", context)


def _ical_escape(text):
    return text.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\r\n', '\\n').replace('\n', '\\n')


def _ical_fold(line):
    # iCal lines must be at most 75 octets; continuation lines start with a space
    encoded = line.encode('utf-8')
    parts = []
    while len(encoded) > (75 if not parts else 74):
        cut = 75 if not parts else 74
        # Don't split a multi-byte UTF-8 character
        while cut > 0 and (encoded[cut] & 0xC0) == 0x80:
            cut -= 1
        parts.append(encoded[:cut].decode('utf-8'))
        encoded = encoded[cut:]
    parts.append(encoded.decode('utf-8'))
    return '\r\n '.join(parts)


def dances(request):
    return render(request, "dances.html")


def player_calendar(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    gigs = Gig.objects.filter(
        playingatgig__player=player,
        date__isnull=False,
    ).exclude(
        status=Gig.Status.CANCELLED
    ).distinct().order_by('date')

    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//gigger//gigs//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        f'X-WR-CALNAME:{_ical_escape(f"NM Gigs - {player.name}")}',
        'REFRESH-INTERVAL;VALUE=DURATION:PT6H',
        'X-PUBLISHED-TTL:PT6H',
    ]
    for gig in gigs:
        instruments = ', '.join(
            pag.instrument.name for pag in PlayingAtGig.objects.filter(gig=gig, player=player).order_by('instrument')
        )
        lines += [
            'BEGIN:VEVENT',
            f'UID:gig-{gig.id}@{request.get_host()}',
            f'DTSTAMP:{now}',
            f'DTSTART;VALUE=DATE:{gig.date.strftime("%Y%m%d")}',
            f'DTEND;VALUE=DATE:{(gig.date + datetime.timedelta(days=1)).strftime("%Y%m%d")}',
            f'SUMMARY:{_ical_escape(f"NM Gig - {gig.title} - {instruments}")}',
            f'URL:{request.build_absolute_uri(reverse("view_gig", args=[gig.id]))}',
        ]
        if gig.location:
            lines.append(f'LOCATION:{_ical_escape(gig.location)}')
        description = []
        if gig.start_time:
            description.append(f'Dancing starts at {gig.start_time.strftime("%H:%M")}')
        if gig.details:
            description.append(gig.details)
        if description:
            lines.append('DESCRIPTION:' + _ical_escape('\n'.join(description)))
        lines.append('END:VEVENT')
    lines.append('END:VCALENDAR')

    body = '\r\n'.join(_ical_fold(line) for line in lines) + '\r\n'
    return HttpResponse(body, content_type='text/calendar; charset=utf-8')


def availability(request, gig_id):
    gig = get_object_or_404(Gig, id=gig_id)
    player = _get_user_or_none(request)

    if request.method == "POST":
        if player is None:
            return JsonResponse({'success': False}, status=403)
        _save_availability(gig, player, request.POST)
        return JsonResponse({'success': True})

    if player is None:
        return redirect(_who_am_i_url(request.path))

    context = {
        'gig': gig,
        'player': player,
        'availability_choices': AvailabilityResponse.Availability.choices,
        'fee': _get_custom_fee(gig, player),
        'response': AvailabilityResponse.objects.filter(gig=gig, player=player).first(),
    }
    return render(request, "availability_choice.html", context)


def _save_availability(gig, player, data):
    if data.get('availability'):
        AvailabilityResponse.objects.update_or_create(
            gig=gig,
            player=player,
            defaults={
                'availability': data['availability'],
                'notes': data.get('notes', ''),
            }
        )
    elif 'notes' in data:
        # Notes alone only update an existing answer; with no answer yet the page
        # sends them along once an availability is chosen
        AvailabilityResponse.objects.filter(gig=gig, player=player).update(notes=data['notes'])

    if gig.permit_custom_fee and 'choice' in data:
        _save_custom_fee(gig, player, data)


def _who_am_i_url(next_url):
    """The "who are you?" page, which sends the user on to next_url once they've chosen"""
    return reverse('who_am_i') + '?' + urlencode({'next': next_url})


def _safe_next(request):
    """The ?next= URL if it's a page on this site, otherwise the user page"""
    next_url = request.GET.get('next', '')
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return reverse('me')


def who_am_i(request):
    context = {
        "players": Player.objects.all().order_by('name'),
        "user": _get_user_or_none(request),
        "next": _safe_next(request),
    }
    return render(request, 'whoami.html', context)


def i_am(request, player_id):
    try:
        player = Player.objects.get(id=player_id)
        request.session['uid'] = player.id
    except Player.DoesNotExist:
        # Remove old player
        request.session.pop('uid', None)

    return redirect(_safe_next(request))

def my_gigs(request):
    user = _get_user_or_none(request)
    
    if user is None:
        return redirect(reverse('who_am_i'))
    
    my_gigs = Gig.objects.filter(playingatgig__player=user, status__in=[Gig.Status.CONFIRMED, Gig.Status.PROPOSED]).distinct().order_by('date')
    
    return render(request, "my_gigs.html", {'user': user, 'gigs': my_gigs})


def my_history(request):
    user = _get_user_or_none(request)

    if user is None:
        return redirect(reverse('who_am_i'))

    gigs = Gig.objects.filter(playingatgig__player=user, status=Gig.Status.DONE).distinct().order_by('-date')
    history = [(gig, gig.fee_for(user)) for gig in gigs]

    return render(request, "my_history.html", {'user': user, 'history': history})


def my_missing_availability(request):
    user = _get_user_or_none(request)
    
    if user is None:
        return redirect(reverse('who_am_i'))
    
    gigs = Gig.objects.filter(
        status__in=[Gig.Status.CONFIRMED, Gig.Status.PROPOSED]
    ).exclude(
        availabilityresponse__player=user
    ).order_by('date')

    return render(request, "my_missing_availability.html", {
        'user': user,
        'gigs': gigs,
        'availability_choices': AvailabilityResponse.Availability.choices,
    })


def manage_players(request):
    if request.method == "POST":
        if 'new_player_name' in request.POST:
            name = request.POST['new_player_name'].strip()
            if name:
                Player.objects.create(name=name)
            return redirect(reverse('manage_players'))

        # Instrument changes are saved via ajax as each checkbox changes
        player = get_object_or_404(Player, id=request.POST['player_id'])
        player.can_play.set(request.POST.getlist('can_play'))
        return JsonResponse({'success': True})

    return render(request, "manage_players.html", {
        'players': Player.objects.all().order_by('name'),
        'instruments': Instrument.objects.all(),
    })