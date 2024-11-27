from django.shortcuts import render
from django.http import (
    HttpResponse,
    HttpResponseNotFound,
    JsonResponse,
    QueryDict,
)
from django.urls import reverse
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
        fields = ["status", "date", "title", "location", "contact_name", "contact_email", 
                  "handled_by", "start_time", "details", 
                  "paid", "cost_per_player", "number_of_charging_players", "cost_per_car", 
                  "number_of_cars", "cost_extras",  "required_instruments"]
    


# Create your views here.
def create_gig(request):
    if request.method == "POST":
        form = CreateGigForm(request.POST)
        if form.is_valid():

            new_gig = Gig(**form.cleaned_data)
            new_gig.save()

            new_gig.required_instruments .set([i for i in Instrument.objects.all()])
            new_gig.save()
        return redirect(reverse('edit_gig', args=[new_gig.id]))
    else:
        form = CreateGigForm()
        return render(request, "create_gig.html", {"form": form})


def edit_gig(request, gig_id):
    gig = get_object_or_404(Gig, id=gig_id)

    if request.method == "POST":
        form = EditGigForm(request.POST, instance=gig)
        if not form.is_valid():
            print(form.errors.as_data())
        form.save()
        return redirect(reverse('view_gig', args=[gig.id]))
    else:

        form = EditGigForm(instance=gig)
        return render(request, "edit_gig.html", {"form": form, "gig": gig})
    

def view_gig(request, gig_id):
    gig = get_object_or_404(Gig, id=gig_id)
    availability = AvailabilityResponse.objects.filter(gig=gig).order_by('availability')
    return render(request, "gig.html", {"gig": gig, "availability": availability})


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


def availability_entry_point(request, gig_id):
    gig = get_object_or_404(Gig, id=gig_id)
    return render(request, "availability_entry_point.html", {"gig": gig, "players": Player.objects.all().order_by('name')})


def availability_form(request, gig_id, player_id):
    context = {
        'gig': get_object_or_404(Gig, id=gig_id),
        'player': get_object_or_404(Player, id=player_id),
        'availability_choices': AvailabilityResponse.Availability.choices,
    }
    return render(request, "availability_choice.html", context)


def availability_set(request, gig_id, player_id):
    gig = get_object_or_404(Gig, id=gig_id)
    player = get_object_or_404(Player, id=player_id)
    print(request.POST)
    ar, created = AvailabilityResponse.objects.update_or_create(
        gig=gig, 
        player=player, 
        defaults={
            'availability': request.POST['availability'],
            'notes': request.POST['notes']
        }
    )
    ar.save()
    return JsonResponse({'redirect': reverse('view_gig', args=[gig.id])})