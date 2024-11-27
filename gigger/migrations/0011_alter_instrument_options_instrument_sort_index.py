# Generated by Django 4.0.6 on 2024-11-27 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gigger', '0010_alter_gig_required_instruments'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='instrument',
            options={'ordering': ['sort_index']},
        ),
        migrations.AddField(
            model_name='instrument',
            name='sort_index',
            field=models.IntegerField(default=0),
        ),
    ]