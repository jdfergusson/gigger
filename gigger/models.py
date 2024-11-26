from django.db import models

# Create your models here.



class Instrument(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.name
    
    
class Player(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    can_play = models.ManyToManyField(Instrument)

    def __str__(self):
        return self.name
    

class Gig(models.Model):
    class Status(models.TextChoices):
        PROPOSED = 'PR', 'Proposed'
        CONFIRMED = 'CO', 'Confirmed'
        CANCELLED = 'CA', 'Cancelled'
        DONE = 'DO', 'Done'
        
    created = models.DateField(auto_now_add=True)
    modified = models.DateField(auto_now=True)
    
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.PROPOSED)
    date = models.DateField(null=True)
    title = models.CharField(max_length=200, blank=False)
    location = models.CharField(max_length=200, blank=True)
    contact_name = models.CharField(max_length=200, blank=True)
    contact_email = models.CharField(max_length=200, blank=True)
    handled_by = models.ForeignKey(Player, null=True, on_delete=models.SET_NULL)
    details = models.TextField(blank=True)
    
    paid = models.BooleanField(default=False)
    
    cost_per_player = models.DecimalField(default=0, max_digits=7, decimal_places=2)
    number_of_charging_players = models.IntegerField(blank=False, default=7)
    cost_per_car = models.DecimalField(default=0, max_digits=7, decimal_places=2)
    number_of_cars = models.IntegerField(blank=False, default=0)
    cost_extras = models.DecimalField(default=0, max_digits=7, decimal_places=2)
    
    required_instruments = models.ManyToManyField(Instrument)

    @property
    def total_cost(self):
        return self.number_of_charging_players * self.cost_per_player \
            + self.number_of_cars * self.cost_per_car \
            + self.cost_extras
    
    def get_status(self):
        return self.Status(self.status).label

    def __str__(self):
        return self.title
    
    
class AvailabilityResponse(models.Model):
    class Availability(models.TextChoices):
        AVAILABLE = 'AV', 'Available'
        IFNEEDBE = 'IF', 'If needs be'
        UNAVAILABLE = 'UN', 'Unavailable'
        
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    availability = models.CharField(max_length=2, choices=Availability.choices, default=Availability.UNAVAILABLE)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('gig', 'player')

    def __str__(self):
        return self.Availability(self.availability).label
    
class PlayingAtGig(models.Model):
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('gig', 'instrument')