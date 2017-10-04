#coding=utf-8
from componet.urlfetcher.filter_route_map import set_default_interval,set_netloc_interval
"""
这里来设置全局默认的域名过滤器，
使用来设置单个域名最小访问间隔，
当在该请求没有任何过滤方案时，会调用全局域名过滤器，来限制访问频繁度
"""
# 设置 全局路由过滤器的默认过滤时间 为5s
set_default_interval(5)

# 设置某域名下过滤时间
set_netloc_interval('www.tuicool.com',7)