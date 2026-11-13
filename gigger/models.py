from django.db import models

# Create your models here.



class Instrument(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    icon = models.CharField(max_length=5, null=False, blank=False, default="?")
    sort_index = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['sort_index',]
    
    
class Player(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    can_play = models.ManyToManyField(Instrument)
    is_admin = models.BooleanField(default=False, verbose_name="Administrator")

    def __str__(self):
        return self.name
    

class Gig(models.Model):
    class Status(models.TextChoices):
        PROPOSED = 'PR', 'Proposed'
        CONFIRMED = 'CO', 'Confirmed'
        CANCELLED = 'CA', 'Cancelled'
        DONE = 'DO', 'Done'

    class ContactMethod(models.TextChoices):
        EMAIL = 'EM', 'Email'
        FACEBOOK = 'FB', 'Facebook'
        IN_PERSON = 'IP', 'In person'
        OTHER = 'OT', 'Other'

    created = models.DateField(auto_now_add=True)
    modified = models.DateField(auto_now=True)
    
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.PROPOSED)
    date = models.DateField(null=True)
    title = models.CharField(max_length=200, blank=False)
    location = models.CharField(max_length=200, blank=True)
    contact_name = models.CharField(max_length=200, blank=True)
    contact_email = models.CharField(max_length=200, blank=True)
    contact_method = models.CharField(max_length=2, choices=ContactMethod.choices, default=ContactMethod.OTHER)
    handled_by = models.ForeignKey(Player, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Band contact")
    start_time = models.TimeField(blank=True, null=True, verbose_name="Dancing start time")
    details = models.TextField(blank=True)
    
    paid = models.BooleanField(default=False)
    
    cost_per_player = models.DecimalField(default=0, max_digits=7, decimal_places=2)
    number_of_charging_players = models.IntegerField(blank=False, default=7)
    cost_per_car = models.DecimalField(default=0, max_digits=7, decimal_places=2)
    number_of_cars = models.IntegerField(blank=False, default=0)
    cost_extras = models.DecimalField(default=0, max_digits=7, decimal_places=2)
    permit_custom_fee = models.BooleanField(default=False)
    
    
    required_instruments = models.ManyToManyField(Instrument, null=True)

    def _custom_fees(self):
        """{player_id: fee} for players who have chosen a custom fee, if custom fees are allowed"""
        if not self.permit_custom_fee:
            return {}
        return {
            cf.player_id: cf.custom_fee
            for cf in CustomFee.objects.filter(gig=self, wants_standard_fee=False)
        }

    def fee_for(self, player):
        """What this player would charge for this gig, using their custom fee if they've set one"""
        return self._custom_fees().get(player.id, self.cost_per_player)

    def player_fees(self):
        """(player, fee) for each player selected to play, using their custom fee if they've set one"""
        players = Player.objects.filter(playingatgig__gig=self).distinct().order_by('name')
        custom_fees = self._custom_fees()
        return [(player, custom_fees.get(player.id, self.cost_per_player)) for player in players]

    @property
    def cars_cost(self):
        return self.number_of_cars * self.cost_per_car

    def unassigned_instruments(self):
        """Required instruments with nobody selected to play them yet"""
        return self.required_instruments.exclude(playingatgig__gig=self)

    @property
    def total_cost(self):
        # Instruments nobody has been selected for yet are costed at the default fee
        return sum(fee for _, fee in self.player_fees()) \
            + self.unassigned_instruments().count() * self.cost_per_player \
            + self.cars_cost \
            + self.cost_extras
    
    def get_status(self):
        return self.Status(self.status).label
    
    def get_status_icon(self):
        icons = {
            'PR': '🟨',
            'CO': '✔️',
            'CA': '❌',
            'DO': '✔️',
        }
        return icons.get(self.status, "?")

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

    def get_availability_icon(self):
        icons = {
            'AV': '🟩',
            'IF': '🟨',
            'UN': '🟥',
        }
        return icons.get(self.availability, "?")

    def __str__(self):
        return self.Availability(self.availability).label
    
class PlayingAtGig(models.Model):
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('gig', 'instrument')


class CustomFee(models.Model):
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    custom_fee = models.IntegerField(default=0)
    wants_standard_fee = models.BooleanField(default=True)