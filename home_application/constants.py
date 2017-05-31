# -*- coding: utf-8 -*-
from conf.default import APP_ID, APP_TOKEN


def enum(**enums):
    return type("Enum", (), enums)


PUBLISH_STATUS = [u"发布成功", u"发布失败", u"发布中"]
IPS_SOURCE = [u"模块", u"手动"]
DATA_SET = "%s_log_search_app" % APP_ID.replace('-', '')
REQUEST_CREATE_DATA_ID = {
    'app_code': APP_ID,
    'op_platform': APP_ID,
    'app_secret': APP_TOKEN,
    "data_format_id": "2",
    "notice": "self",
    "data_encode": "UTF8",
    "tags": [],
    "data_set": DATA_SET,
    "biz_id": '',
    "appenv": "ieod",
    "sensitive": "1",
    "user": '',
    # "username": "admin",
    "data_desc": u"服务日志",
    "data_src_type": "svrlog",
    "sep": "",
    "file_frequency": 3600,
    "log_path": '[[host-specific]]',
    "fields": [
        {
            "index": "1",
            "checked": "1",
            "name": "message",
            "orig_index": "1",
            "report_index": 1,
            "time_zone": "8",
            "time_format": "5",
            "alis": "",
            "type": "string",
            "description": u"日志"
        }
    ]
}
REQUEST_RESULT_TABLE = {
    "count_freq": 0,
    "description": "log_test",
    "biz_id": '',
    "storages_args": "{\"es\": {\"cluster\": \"default\"}}",
    "table_name": "",
    "storages": "es",
    "project_id": '',
    "fields": [
        {
            "default_value": "{\"value\":null}",
            "description": u"timestamp时间戳",
            "origins": None,
            "is_dimension": False,
            "field": "timestamp",
            "type": "timestamp"
        },
        {
            "default_value": "{\"value\":null}",
            "description": u"主机IP",
            "origins": None,
            "is_dimension": False,
            "field": "ip",
            "type": "string"
        },
        {
            "default_value": "{\"value\": null}",
            "description": u"模块",
            "origins": None,
            "is_dimension": False,
            "field": "module",
            "type": "string"
        },
        {
            "default_value": "{\"value\": null}",
            "description": u"日志内容",
            "origins": None,
            "is_dimension": False,
            "field": "log",
            "type": "string"
        },
        {
            "default_value": "{\"value\": null}",
            "description": u"路径",
            "origins": None,
            "is_dimension": False,
            "field": "path",
            "type": "string"
        }
    ]
}

REQUEST_GET_PRO_STATUS = {
    "app_code": "",
    "app_secret": "",
    "bk_token": "",
    "username": "admin",
    "app_id": "",
    "operate_type": 2,
    "proc_list": [
        {
            "proc_info": {
                "base_info": {
                    "proc_name": "bk_gse_unifyTlogc",
                    "setup_path": "/usr/local/gse/gseagent/plugins/unifyTlogc/sbin",
                    "cfg_path": "/usr/local/gse/gseagent/plugins/unifyTlogc/conf",
                    "log_path": "/usr/local/gse/gseagent/plugins/unifyTlogc/log",
                    "pid_path": "/usr/local/gse/gseagent/plugins/unifyTlogc/log/unifyTlogc.pid",
                    "contact": "mapleleaf",
                    "start_cmd": "./bk_gse_unifyTlogc &",
                    "stop_cmd": "./bk_gse_unifyTlogc --stop",
                    "restart_cmd": "./bk_gse_unifyTlogc --reload",
                    "reload_cmd": "./bk_gse_unifyTlogc --reload",
                    "kill_cmd": "bash",
                    "func_id": "null",
                    "instance_id": "null",
                    "value_key": "/usr/local/gse/gseagent/plugins/unifyTlogc/sbin/bk_gse_unifyTlogc",
                },
            },
            "ip_list": [
                {
                    "ip": "",
                    "source": 1,
                    "auth_user": "root",
                    "auth_pwd": "null",
                }
            ],
        }
    ]
}

HEADERS = {'Content-type': 'application/json'}

ES_KEYS = ["log", "moduleName", "serverIp"]
# , "localTime"

ConfigStatus = enum(
    SUCCESS=0,
    FAILED=1,
    WORKING=2
)
PublishType = enum(
    PUBLUSH_CONFIG=0,
    HOST_OFF=1,
)

HostStatus = enum(
    RELEASING=0,
    REMOVING=1,
    COLLECTING=2,
    PUBLISH_EXCEPTION=3,
    SUCCESS=4,
    DELETE_EXCEPTION=5,
    STATUS_EXCEPTION=6,
    WAITING=7
)

BODY_DATA = {
    "highlight": {
        "pre_tags": [
            "<em>"
        ],
        "post_tags": [
            "</em>"
        ],
        "fields": {
            "*": {"number_of_fragments": 0},
        },
        "require_field_match": False,
    },
    "query": {
        "query_string": {
            "fields": ["log", "serverIp", "moduleName", "localTime"],
            "lenient": True,
            "query": {},
            "analyze_wildcard": True,
        },
    },
    "sort": [
        {
            "localTime": "desc"
        }
    ],
}

ERROR_STATUS = {"1": {"status": "failed", "errcode": "",
                      "error_message": ""}}

INIT_STATUS = {"1": {"status": "working", "errcode": "",
                     "error_message": ""}}
