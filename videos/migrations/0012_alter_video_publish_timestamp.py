# Generated by Django 3.2.16 on 2023-01-20 20:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0011_alter_video_video_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='publish_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
