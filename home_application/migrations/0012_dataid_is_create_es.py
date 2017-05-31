# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0011_auto_20170220_1501'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataid',
            name='is_create_es',
            field=models.BooleanField(default=False, verbose_name='\u662f\u5426\u521b\u5efaes\u8868'),
        ),
    ]
