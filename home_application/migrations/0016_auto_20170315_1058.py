# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0015_auto_20170314_1546'),
    ]

    operations = [
        migrations.AlterField(
            model_name='config',
            name='publish_type',
            field=models.IntegerField(default=0, verbose_name='\u53d1\u5e03\u5185\u5bb9', choices=[(0, '\u65b0\u589e\u914d\u7f6e'), (1, '\u5220\u9664\u4e3b\u673a')]),
        ),
    ]
