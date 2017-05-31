# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0006_auto_20161230_1419'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataId',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('app_id', models.IntegerField(verbose_name='\u4e1a\u52a1ID')),
                ('data_id', models.IntegerField(verbose_name='DataID')),
            ],
            options={
                'verbose_name': 'dataID\u4e0e\u4e1a\u52a1ID',
                'verbose_name_plural': 'dataID\u4e0e\u4e1a\u52a1ID\u8bb0\u5f55\u8868',
            },
        ),
        migrations.RenameField(
            model_name='host',
            old_name='moudle',
            new_name='module',
        ),
    ]
