# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0013_auto_20170224_1034'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchhistory',
            name='search_date',
            field=models.DateField(auto_now=True, null=True),
        ),
    ]
