# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0009_auto_20170210_1140'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchhistory',
            name='count',
            field=models.IntegerField(default=0, verbose_name='\u641c\u7d22\u9891\u7387'),
        ),
    ]
