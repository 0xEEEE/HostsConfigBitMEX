# -*- coding: utf-8 -*-
# @Author: Yitao
# @Date:   2019-04-11 23:14:51
# @Last Modified by:   Yitao
# @Last Modified time: 2019-04-16 21:15:26

import os
import platform
import time
import urllib.request
import re
import threading
import subprocess

domain_set = {'sentry.services.bitmex.com', 'static.bitmex.com', 'www.bitmex.com', 'bitmex.com', 
              'public.bitmex.com', 'blog.bitmex.com', 'testnet.bitmex.com', 'testnet-static.bitmex.com', 
              'ts.bitmex.com', 'status.bitmex.com', 'research.bitmex.com', 'analytics.bitmex.com'}
domain_suffix = 'bitmex.com'
dns_check_url = 'https://who.is/dns/'
dns_dic = {}
 
def time_stamp():
    localtime = time.localtime(time.time())
    return time.strftime('%Y%m%d%H%M%S', localtime)

def path_check():
    global hosts_path
    global hosts_backup_path
    global hosts_new_path
    global is_windows 
    is_windows = True if platform.system() == 'Windows' else False
    if is_windows:
        hosts_path = os.environ['SYSTEMROOT']+'/System32/drivers/etc/hosts'
        hosts_backup_path = os.environ['SYSTEMROOT']+'/System32/drivers/etc/hosts.bak'+time_stamp()
        hosts_new_path = os.environ['SYSTEMROOT']+'/System32/drivers/etc/hosts.new'
    else:
        hosts_path = '/etc/hosts'
        hosts_backup_path = '/etc/hosts.bak'+time_stamp()
        hosts_new_path = '/etc/hosts.new'

def dns_check(domain):
    reg = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
    response = urllib.request.urlopen(dns_check_url + domain).read()
    html = bytes(response).decode('ascii')
    ip_addrs = reg.findall(html)
    dns_dic[domain] = ip_addrs
    print('查询到'+domain+' IP地址为%s' %ip_addrs)

def ping(ip, ping_count='10'):
    # 默认ping的次数为10次
    print('正在ping测试%s连通性……' % ip)
    ping_c = '-n' if is_windows else '-c'
    p = subprocess.Popen(['ping', ping_c, ping_count, ip], stdin = subprocess.PIPE, stdout=subprocess.PIPE)
    decode_str = 'gbk' if is_windows else 'utf-8'
    ping_result = p.stdout.read().decode(decode_str)
    return ping_result

def get_ping_rtt(ping_result):
    rtt = 100000.0
    if is_windows:
        reg_min = re.compile(r'最短\s?=\s?\d+ms|Minimum\s?=\s?\d+ms')
        reg_max = re.compile(r'最长\s?=\s?\d+ms|Maximum\s?=\s?\d+ms')
        reg_avg = re.compile(r'平均\s?=\s?\d+ms|Average\s?=\s?\d+ms')
        minimum, maximum, average = reg_min.findall(win_result), reg_max.findall(win_result), reg_avg.findall(win_result)
        if minimum and maximum and average:
            minimum, maximum, average = [re.sub(r'[MinimumMaximumAverage最短最长平均= ms]', '',x)  for x in [minimum[0], maximum[0], average[0]]]
            rtt = float(average)
            print('平均延迟%sms\n' % average)
        else:
            print('无法连通！\n')
    else:
        reg_key = re.compile(r'\w*\D/\w*\D/\w*\D/\D\w*')
        reg_value = re.compile(r'\d*\.?\d*\/\d*\.?\d*\/\d*\.?\d*\/\d*\.?\d*')
        ping_key, ping_value = reg_key.findall(ping_result), reg_value.findall(ping_result)
        str_break = '/'
        if ping_key and ping_value:
            ping_key, ping_value = ping_key[0].split(str_break), ping_value[0].split(str_break)
            ping_dic = dict(zip(ping_key, ping_value))
            avg = 'avg'
            stddev = 'mdev' if 'mdev' in ping_dic else 'stddev'
            rtt = float(ping_dic[avg]) + float(ping_dic[stddev])
            print('平均延迟%sms\n标准差%sms\n' % (ping_dic[avg], ping_dic[stddev]))
        else:
            print('无法连通！\n')
    return rtt

def set_dns_record():
    for domain in dns_dic:
        rtt_dic = {}
        if len(dns_dic[domain]) != 1:
            for ip in dns_dic[domain]:
                ping_result = ping(ip)
                rtt_dic[ip] = get_ping_rtt(ping_result)
            key_min = key_min = min(rtt_dic, key=rtt_dic.get)
            dns_dic[domain] = key_min
        else:
            dns_dic[domain] = dns_dic[domain][0]

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
        for key,value in dns_dic.items():
            record = str(value) + ' ' + str(key) + '\n'
            new.write(record)
    os.remove(hosts_path)
    os.rename(hosts_new_path,hosts_path)
    print('hosts更新完成！')

if __name__ == '__main__':
    path_check()
    print('开始查询IP地址……')
    threads = []
    for domain in domain_set:
        thread = threading.Thread(target=dns_check,args=(domain,))
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print('查询完毕，开始测试IP地址连通性……')
    set_dns_record()
    print('测试完毕，开始更新hosts文件……')
    hosts_update()
