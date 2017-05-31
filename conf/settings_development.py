# -*- coding: utf-8 -*-
"""
用于本地开发环境的全局配置
"""
from settings import APP_ID
# ===============================================================================
# 数据库设置, 本地开发数据库设置
# ===============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # 我们默认用mysql
        'NAME': 'cloud-log-search',                        # 数据库名 (默认与APP_ID相同)
        'USER': 'root',                            # 你的数据库user
        'PASSWORD': 'oneoaas@2A',                        # 你的数据库password
        'HOST': '10.0.2.47',                       # 数据库HOST
        'PORT': '3306',                        # 默认3306
    },
}
# 'HOST': '127.0.0.1',  # 开发的时候，使用localhost



