# Generated by Django 4.0.6 on 2024-11-27 08:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gigger', '0008_alter_gig_handled_by_alter_gig_start_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gig',
            name='handled_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gigger.player', verbose_name='Band contact'),
        ),
    ]
