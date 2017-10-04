#coding=utf-8

# 数据库连接池配置

JSON_STORE_DIR ='../SpiderXStore/store/json'
TMP_FILES_DIR = '../SpiderXStore/store/tmpfiles'
HOT_RENEW = True


DB_SETTING_DICT={
    "default" : {          # dblogger会被配置到默认db路由
        "type": "mysql",
        "conf": {
            "host": "default_conn_host",
            "user": "default_conn_user",
            "pass": "default_conn_passwd",
            "db": "default_db_name",
            "port": 3306,
            "max": 2,      # 根据使用设置最大数量
            "min": 1
        }
    },
    "your_conn_name" : {
        "type": "mysql",
        "conf": {
            "host": "your_conn_host",
            "user": "your_conn_user",
            "pass": "your_conn_passwd",
            "db": "your_db_name",
            "port": 3306,
            "max": 2,
            "min": 1
        }
    },
}