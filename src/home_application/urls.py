# -*- coding: utf-8 -*-
from django.conf.urls import patterns

urlpatterns = patterns('home_application.views',
                       # 公共接口
                       (r'^app_list/$', 'get_app_list'),
                       (r'^get_modules/$', 'get_modules'),
                       (r'^check_app_config/$', 'check_app_config'),
                       (r'^check_publish_ips/$', 'check_publish_ips'),
                       # 日志检索部分接口
                       (r'^search_log/$', 'search_log'),
                       (r'^get_history_keys/$', 'get_history_keys'),
                       (r'^get_all_history_keys/$', 'get_all_history_keys'),
                       (r'^get_chart_data/$', 'get_chart_data'),
                       (r'^export_log/$', 'export_log'),
                       # 配置部分接口
                       (r'^query_config/$', 'query_config'),
                       (r'^publish_config/$', 'publish_config'),
                       (r'^get_config_status/$', 'get_config_status'),
                       (r'^query_config_status/$', 'query_config_status'),
                       # 主机管理部分接口
                       (r'^query_host/$', 'query_host'),
                       (r'^query_module_config/$', 'query_module_config'),
                       (r'^host_off/$', 'host_off'),
                       (r'^host_module_off', 'host_module_off'),
                       (r'^query_host_status/$', 'query_host_status'),
                       (r'^get_host_status/$', 'get_host_status'),
                       # 前端调试路由
                       (r'^$', 'index'),
                       )
