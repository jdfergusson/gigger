# Generated by Django 4.2.16 on 2024-11-26 20:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gigger', '0003_gig_number_of_charging_players'),
    ]

    operations = [
        migrations.AddField(
            model_name='gig',
            name='handled_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='gigger.player'),
        ),
    ]