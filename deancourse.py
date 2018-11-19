#!/usr/bin/env python3

"""
deancourse

用于从 http://dean.pku.edu.cn 抓取北京大学课程表的小程序
作者 myxxxsquared https://github.com/myxxxsquared

依赖：
python3
BeautifulSoup

使用方法：
直接运行

许可协议：GPLv3

"""

import urllib.parse
import csv
from http.client import HTTPConnection
from bs4 import BeautifulSoup

DEAN_HOST = 'dean.pku.edu.cn'
REQUEST_HEADER = {'User-Agent':'Mozilla/5.0'}
POST_HEADER = {'Content-Type':'application/x-www-form-urlencoded', 'User-Agent':'Mozilla/5.0'}
DEAN_ENCODING = 'gb2312'

def dean_request(url, method='GET', data=None) -> BeautifulSoup:
    if data is not None:
        if not isinstance(data, str):
            data = urllib.parse.urlencode(data)
        if method == 'GET':
            url = url + '?' + data
            data = None
    conn = HTTPConnection(DEAN_HOST)
    conn.request(
        method,
        url,
        headers=REQUEST_HEADER if method != 'POST' else POST_HEADER,
        body=data)
    response = conn.getresponse()
    if response.status != 200:
        raise Exception('HTTP request failed', response.status, url, method, data)
    result = response.read().decode(encoding=DEAN_ENCODING, errors='ignore')
    conn.close()
    response.close()
    soup = BeautifulSoup(result, "html5lib")
    return soup

def dean_xnxq():
    soup = dean_request('/pkudean/course/kcb.php', 'GET')
    for select in soup.find_all('select'):
        if select['name'] == 'xnxq':
            for option in select.find_all('option'):
                yield option['value']

def dean_dep():
    for xnxq in dean_xnxq():
        soup = dean_request('/pkudean/course/kcb.php', 'GET', {'xnxq': xnxq})
        table = soup.find('table')
        if not table:
            continue
        for tr in table.find_all('tr'):
            a = tr.find('a')
            if a is None:
                continue
            params = a['href'].split('?')[1]
            yield urllib.parse.parse_qsl(params), ' '.join(tr.stripped_strings)

def dean_coruses():
    for dep, dep_name in dean_dep():
        depinfo = dict(dep)
        print((dep_name, depinfo['xn'], depinfo['xq']))
        dep.append(('zy', '%'))
        dep.append(('nj', '%'))
        soup = dean_request('/pkudean/course/kcbxs.php', 'POST', dep)
        table = soup.find('table')
        head_tr = table.find('tr')
        heads = []
        for th in head_tr.find_all('th'):
            heads.append(' '.join(th.stripped_strings))

        for tr in table.find_all('tr'):
            resultinfo = []
            link = None
            resultinfo.append(('学年学期', '-'.join((depinfo['xn'], depinfo['xq']))))
            resultinfo.append(('系所名称(Schools)', dep_name))
            for name, td in zip(heads, tr.find_all('td')):
                resultinfo.append((name, ' '.join(td.stripped_strings)))
                a = td.find('a')
                if a is not None:
                    link = a['href']
            if len(resultinfo) == 2:
                continue
            resultinfo.append(('课程链接', link))
            yield resultinfo

def return_double_first(it):
    it = iter(it)
    data = next(it)
    yield data
    yield data
    for data in it:
        yield data

def main():
    course_iter = iter(return_double_first(dean_coruses()))

    with open('classes.csv', 'w', newline='\n') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=[name for name, _ in next(course_iter)])
        writer.writeheader()
        for _, course in enumerate(course_iter):
            writer.writerow(dict(course))

if __name__ == '__main__':
    main()
