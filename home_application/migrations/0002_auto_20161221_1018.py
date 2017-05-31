# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='config',
            name='app_id',
            field=models.IntegerField(default=1, verbose_name='\u6240\u5c5e\u4e1a\u52a1ID'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='host',
            name='app_id',
            field=models.IntegerField(default=1, verbose_name='\u6240\u5c5e\u4e1a\u52a1ID'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='searchhistory',
            name='app_id',
            field=models.IntegerField(default=1, verbose_name='\u6240\u5c5e\u4e1a\u52a1ID'),
            preserve_default=False,
        ),
    ]
