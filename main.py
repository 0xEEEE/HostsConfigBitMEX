# -*- coding: utf-8 -*-
# @Author: Yitao
# @Date:   2019-04-11 23:14:51
# @Last Modified by:   Yitao
# @Last Modified time: 2019-04-14 11:20:08

import os
import platform
import time
import urllib.request
import re
import threading

domain_set = {'sentry.services.bitmex.com', 'static.bitmex.com', 'www.bitmex.com', 'bitmex.com', 
              'public.bitmex.com', 'blog.bitmex.com', 'testnet.bitmex.com', 'testnet-static.bitmex.com', 
              'ts.bitmex.com', 'status.bitmex.com', 'research.bitmex.com', 'analytics.bitmex.com'}
domain_suffix = 'bitmex.com'
dns_check_url = 'https://who.is/dns/'
hosts_dic = {}

def time_stamp():
    localtime = time.localtime(time.time())
    return time.strftime('%Y%m%d%H%M%S', localtime)

def path_check():
    global hosts_path
    global hosts_backup_path
    global hosts_new_path
    if platform.system() == 'Windows':
        hosts_path = os.environ['SYSTEMROOT']+'/System32/drivers/etc/hosts'
        hosts_backup_path = os.environ['SYSTEMROOT']+'/System32/drivers/etc/hosts.bak'+time_stamp()
        hosts_new_path = os.environ['SYSTEMROOT']+'/System32/drivers/etc/hosts.new'
    else:
        hosts_path = '/etc/hosts'
        hosts_backup_path = '/etc/hosts.bak'+time_stamp()
        hosts_new_path = '/etc/hosts.new'

def ip_check(domain):
    reg = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
    response = urllib.request.urlopen(dns_check_url + domain).read()
    html = bytes(response).decode('ascii')
    ip_addrs = re.findall(reg, html)
    hosts_dic[domain] = ip_addrs
    print('查询到'+domain+' IP地址为%s' %ip_addrs)

def hosts_update():
    with open(hosts_path, 'r+', encoding='utf-8') as host, \
    open(hosts_backup_path, 'w+', encoding='utf-8') as bak, \
    open(hosts_new_path, 'a+', encoding='utf-8') as new:
        lines = host.readlines()
        for line in lines:
            bak.write(line)
            if domain_suffix in line :
                continue
            new.write(line)
        print('已备份原hosts为%s' % hosts_backup_path)
        for key,value in hosts_dic.items():
            record = str(value[0]) + ' ' + str(key) + '\n'
            new.write(record)
    os.remove(hosts_path)
    os.rename(hosts_new_path,hosts_path)
    print('hosts更新完成！')

if __name__ == '__main__':
    path_check()
    print('开始查询IP地址……')
    threads = []
    for domain in domain_set:
        thread = threading.Thread(target=ip_check,args=(domain,))
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print('查询完毕，开始更新hosts文件……')
    hosts_update()
