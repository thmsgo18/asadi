# Generated by Django 5.1.7 on 2025-04-17 13:28

import documents.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Document",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nom", models.CharField(max_length=255)),
                (
                    "fichier",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to=documents.models.get_upload_path,
                    ),
                ),
                ("type", models.CharField(max_length=50)),
                ("date_ajout", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
