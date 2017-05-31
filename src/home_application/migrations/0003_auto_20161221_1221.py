# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0002_auto_20161221_1018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='config',
            name='app_name',
            field=models.CharField(max_length=200, null=True, verbose_name='\u6240\u5c5e\u4e1a\u52a1\u540d\u79f0', blank=True),
        ),
        migrations.AlterField(
            model_name='host',
            name='app_name',
            field=models.CharField(max_length=200, null=True, verbose_name='\u6240\u5c5e\u4e1a\u52a1\u540d\u79f0', blank=True),
        ),
        migrations.AlterField(
            model_name='searchhistory',
            name='app_name',
            field=models.CharField(max_length=200, null=True, verbose_name='\u6240\u5c5e\u4e1a\u52a1\u540d\u79f0', blank=True),
        ),
    ]
