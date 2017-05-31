# -*- coding: utf-8 -*-
import json

from django.db import models

from account.models import BkUser
from common.log import logger
from constants import INIT_STATUS, HostStatus


class Config(models.Model):
    publish_time = models.DateTimeField(verbose_name=u"发布时间")
    publish_user = models.ForeignKey(BkUser, verbose_name=u"发布人员")
    publish_status = models.IntegerField(u"发布状态", choices=[
        (0, u"发布成功"), (1, u"发布失败"), (2, u"发布中")])
    publish_type = models.IntegerField(u"发布内容", choices=[
        (0, u'新增配置'), (1, u"删除采集项")], default=0)
    app_id = models.IntegerField(verbose_name=u"所属业务ID")
    ips_source = models.IntegerField(u"IP来源",
                                     choices=[(0, u"模块"), (1, u"手动")])
    modules = models.TextField(u"模块列表", blank=True, null=True)
    ips = models.TextField(u"IP列表")
    paths = models.TextField(u"路径列表")
    ex_keys = models.TextField(u"排除关键字", blank=True, null=True)
    in_keys = models.TextField(u"包含关键字", blank=True, null=True)
    ex_files = models.TextField(u"排除文件", blank=True, null=True)

    def __unicode__(self):
        return "%s %s %s" % (self.publish_time, self.publish_user.username,
                             self.publish_status)

    class Meta:
        verbose_name = u'配置发布历史'
        verbose_name_plural = u'配置发布历史列表'

    @classmethod
    def to_json(cls, config_list):
        result_list = []
        for config in config_list:
            try:
                status_dic = json.loads(
                    Task.objects.filter(source_id=config.id)[0].status)
            except Exception as e:
                logger.info(
                    u"status 获取失败 config id:%d, error:%s" % (config.id, e))
                status_dic = INIT_STATUS
            result_list.append({
                "status": {
                    "id": config.id,
                    "status": status_dic
                },
                "publish_time":
                    config.publish_time.strftime('%Y-%m-%d %H:%M:%S'),
                "publish_user": config.publish_user.username,
                "publish_type": config.get_publish_type_display(),
                "publish_status": {
                    "publish_status": config.get_publish_status_display(),
                    "id": config.id},
                "details": {
                    "ips_source": config.ips_source,
                    "modules": config.modules,
                    "ips": config.ips,
                    "paths": config.paths,
                    "ex_files": config.ex_files}
            })
        return result_list


class Host(models.Model):
    ip = models.CharField(verbose_name=u"IP", max_length=100)
    module = models.CharField(verbose_name=u"所属模块", max_length=500)
    status = models.IntegerField(u"状态",
                                 choices=[(0, u"发布中"), (1, u"删除中"),
                                          (2, u"采集中"), (3, u"发布异常"),
                                          (4, u"成功"), (5, u"删除异常"),
                                          (6, u"状态异常"), (7, u"等待中")])
    is_get_status = models.BooleanField(u"是否在查询主机状态")
    paths = models.TextField(u"路径列表")
    app_id = models.IntegerField(verbose_name=u"所属业务ID")
    config = models.ForeignKey(Config, verbose_name=u"所属配置")

    def __unicode__(self):
        return "%s %s" % (self.ip, self.status)

    class Meta:
        verbose_name = u'主机配置'
        verbose_name_plural = u'主机配置列表'

    @classmethod
    def to_json(cls, host_list):
        result_list = [
            {
                "module": host.module,
                "paths": host.paths.split(','),
                "ip": host.ip,
                "publish_status": host.get_status_display(),
                "details": {
                    "id": host.id,
                    "task_id": (Task.objects.filter(
                        source_id=host.config_id
                    )[0].id if host.status == 1 else -1),
                    "paths": host.paths,
                    "module": host.module,
                    "ip": host.ip,
                    "publish_status": host.get_status_display(),
                    "ex_files": host.config.ex_files,
                }
            } for host in host_list
            ]
        return result_list


    @classmethod
    def to_module_json(cls, host_list, module_ip_count_list):
        result_dict ={}
        result_list = []

        for host in host_list:
            #host.status=int(host.status)
            host_info = {
                "module": host.module,
                "ip_total": module_ip_count_list[host.module] if host.module in module_ip_count_list else 0,
                "paths": host.paths.split(','),
                "ex_files": host.config.ex_files.split(','),
                "hosts": [
                    {
                        "ip": host.ip,
                        "publish_status": host.get_status_display(),
                        "module": host.module,
                        "id": host.id
                    }],
                "host_count": {
                    "normal_count": 1 if host.status in [int(HostStatus.COLLECTING),
                                                         int(HostStatus.SUCCESS),
                                                         ] else 0,
                    "unnormal_count": 1 if host.status in [int(HostStatus.PUBLISH_EXCEPTION),
                                                           int(HostStatus.DELETE_EXCEPTION),
                                                           int(HostStatus.STATUS_EXCEPTION),
                                                           ] else 0,
                    "publishing_count": 1 if host.status in [int(HostStatus.RELEASING),
                                                             int(HostStatus.REMOVING),
                                                             ] else 0,
                    "total_count": 1,
                }
            }
            if host.module not in result_dict:
                result_dict[host.module] = host_info
            else:
                mudule_info = result_dict[host.module]
                result_dict[host.module].update({
                    "paths": list(set(mudule_info["paths"] + host_info["paths"])),
                    "ex_files": list(set(mudule_info["ex_files"] + host_info["ex_files"])),
                    "hosts": mudule_info["hosts"] + host_info["hosts"],
                    "host_count": {"normal_count": mudule_info["host_count"]["normal_count"] +
                                                   host_info["host_count"]["normal_count"],
                                   "unnormal_count": mudule_info["host_count"]["unnormal_count"] +
                                                     host_info["host_count"]["unnormal_count"],
                                   "publishing_count": mudule_info["host_count"]["publishing_count"] +
                                                       host_info["host_count"]["publishing_count"],
                                   "total_count": mudule_info["host_count"]["total_count"] +
                                                  host_info["host_count"]["total_count"],
                                   }
                })
        for key in result_dict:
            result_list.append(result_dict[key])
        return result_list


class Task(models.Model):
    """
    status写入一个json格式的字符串，形式类似：
    {
        '1':{'status': (success, working,failed),
             'errcode': "ffff",
             'error_message':"105"}
    }
    (‘1’：生成配置文件
    ‘2’：下发配置文件)
    """
    source = models.IntegerField(verbose_name=u"任务来源",
                                 choices=[(0, 'Config'), (1, 'Host')])
    source_id = models.IntegerField(verbose_name=u"来源ID")
    status = models.TextField(verbose_name=u"状态")

    def __unicode__(self):
        return "%s %s" % (self.source, self.source_id)

    class Meta:
        verbose_name = u'celery任务记录'
        verbose_name_plural = u'celery任务记录表'


class SearchHistory(models.Model):
    user = models.ForeignKey(BkUser, verbose_name=u"用户")
    app_name = models.CharField(verbose_name=u"所属业务名称", max_length=200,
                                null=True, blank=True)
    app_id = models.IntegerField(verbose_name=u"所属业务ID")
    search_key = models.TextField(verbose_name=u"搜索关键字")
    search_time = models.DateTimeField(auto_now=True, null=True, blank=True)
    search_date = models.DateField(auto_now=True, null=True, blank=True)
    count = models.IntegerField(verbose_name=u"搜索频率", default=0)
    took = models.TextField(verbose_name=u"查询耗时", null=True)
    total = models.IntegerField(verbose_name=u"返回条数", default=0)

    def __unicode__(self):

        return "%s %s %s" % (
            self.user.username, self.app_id, self.search_key)

    class Meta:
        verbose_name = u'搜索历史记录'
        verbose_name_plural = u'搜索历史记录表'


class DataId(models.Model):
    app_id = models.IntegerField(verbose_name=u"业务ID")
    data_id = models.IntegerField(verbose_name=u"DataID")
    is_create_es = models.BooleanField(verbose_name=u"是否创建es表",
                                       default=False)

    def __unicode__(self):
        return "%s %s" % (
            self.app_id, self.data_id)

    class Meta:
        verbose_name = u'dataID与业务ID'
        verbose_name_plural = u'dataID与业务ID记录表'
