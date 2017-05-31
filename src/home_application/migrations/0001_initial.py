# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Config',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('publish_time', models.DateTimeField(verbose_name='\u53d1\u5e03\u65f6\u95f4')),
                ('publish_status', models.IntegerField(verbose_name='\u53d1\u5e03\u72b6\u6001', choices=[(0, '\u53d1\u5e03\u6210\u529f'), (1, '\u53d1\u5e03\u5931\u8d25'), (2, '\u53d1\u5e03\u4e2d')])),
                ('app_name', models.CharField(max_length=200, verbose_name='\u6240\u5c5e\u4e1a\u52a1\u540d\u79f0')),
                ('ips_source', models.IntegerField(verbose_name='IP\u6765\u6e90', choices=[(0, '\u6a21\u5757'), (1, '\u624b\u52a8')])),
                ('moudles', models.TextField(null=True, verbose_name='\u6a21\u5757\u5217\u8868', blank=True)),
                ('ips', models.TextField(verbose_name='IP\u5217\u8868')),
                ('paths', models.TextField(verbose_name='\u8def\u5f84\u5217\u8868')),
                ('ex_keys', models.TextField(null=True, verbose_name='\u6392\u9664\u5173\u952e\u5b57', blank=True)),
                ('in_keys', models.TextField(null=True, verbose_name='\u5305\u542b\u5173\u952e\u5b57', blank=True)),
                ('ex_files', models.TextField(null=True, verbose_name='\u6392\u9664\u6587\u4ef6', blank=True)),
                ('task_id', models.IntegerField(verbose_name='\u4efb\u52a1ID')),
                ('publish_user', models.ForeignKey(verbose_name='\u53d1\u5e03\u4eba\u5458', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '\u914d\u7f6e\u53d1\u5e03\u5386\u53f2',
                'verbose_name_plural': '\u914d\u7f6e\u53d1\u5e03\u5386\u53f2\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip', models.CharField(max_length=100, verbose_name='IP')),
                ('moudle', models.CharField(max_length=500, verbose_name='\u6240\u5c5e\u6a21\u5757')),
                ('status', models.IntegerField(verbose_name='\u72b6\u6001', choices=[(0, '\u4e0b\u67b6'), (1, '\u4e0b\u67b6\u4e2d')])),
                ('is_get_status', models.BooleanField(verbose_name='\u662f\u5426\u5728\u67e5\u8be2\u4e3b\u673a\u72b6\u6001')),
                ('paths', models.TextField(verbose_name='\u8def\u5f84\u5217\u8868')),
                ('app_name', models.CharField(max_length=200, verbose_name='\u6240\u5c5e\u4e1a\u52a1\u540d\u79f0')),
                ('task_id', models.IntegerField(null=True, verbose_name='\u4efb\u52a1ID', blank=True)),
                ('config', models.ForeignKey(verbose_name='\u6240\u5c5e\u914d\u7f6e', to='home_application.Config')),
            ],
            options={
                'verbose_name': '\u4e3b\u673a\u914d\u7f6e',
                'verbose_name_plural': '\u4e3b\u673a\u914d\u7f6e\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='SearchHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('app_name', models.CharField(max_length=200, verbose_name='\u6240\u5c5e\u4e1a\u52a1\u540d\u79f0')),
                ('search_key', models.TextField(verbose_name='\u641c\u7d22\u5173\u952e\u5b57')),
                ('user', models.ForeignKey(verbose_name='\u7528\u6237', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '\u641c\u7d22\u5386\u53f2\u8bb0\u5f55',
                'verbose_name_plural': '\u641c\u7d22\u5386\u53f2\u8bb0\u5f55\u8868',
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source', models.IntegerField(verbose_name='\u4efb\u52a1\u6765\u6e90', choices=[(0, b'Config'), (1, b'Host')])),
                ('source_id', models.IntegerField(verbose_name='\u6765\u6e90ID')),
                ('status', models.TextField(verbose_name='\u72b6\u6001')),
            ],
            options={
                'verbose_name': 'celery\u4efb\u52a1\u8bb0\u5f55',
                'verbose_name_plural': 'celery\u4efb\u52a1\u8bb0\u5f55\u8868',
            },
        ),
    ]
