# -*- coding:utf-8 -*-
import datetime
import json
import random
import time

import pandas as pd
import requests
from lxml import etree
import re
import collections
import math
from fund_rank import fund_code_name
from fund_logger import Log

log = Log(file_name=None, log_name='fund.log').init_logger()


def get_fundcode():
    """获取天天基金所有基金信息"""
    res_fundcode = requests.get("http://fund.eastmoney.com/js/fundcode_search.js")
    fundcode_str = re.findall('var r = (.*])', res_fundcode.text)[0]
    fundcode_list = json.loads(fundcode_str)
    fundcode = pd.DataFrame(fundcode_list, columns=['fund_code', 'fund_abbr', 'fund_name', 'fund_type', 'fund_pinyin'])
    fundcode = fundcode.loc[:, ['fund_code', 'fund_name', 'fund_type']]
    fundcode.to_csv('./fundcode.csv', index=False)


def get_pzgs(fund_code):
    """获取基金当日盘中估算的值"""
    r = requests.get(url=f"http://fundf10.eastmoney.com/jjjz_{fund_code}.html")
    html = etree.HTML(r.text)
    pzgs = html.xpath("//span[@id='fund_gsz']/text()")[0]
    return pzgs


def get_one_page(fundcode, pageIndex=1):
    """获取基金净值某一页的html"""
    cookie = 'st_si=50042120533408; st_asi=delete; qgqp_b_id=75d7da532bb4bf938c20a91c4f8a1118; ' \
             'EMFUND1=null; EMFUND2=null; EMFUND3=null; EMFUND4=null; EMFUND5=null; EMFUND6=null; EMFUND0=null; ' \
             'EMFUND7=07-12%2012%3A39%3A17@%23%24%u4E2D%u822A%u745E%u660E%u7EAF%u503AA@%23%24007555; ' \
             'EMFUND8=07-12%2015%3A35%3A50@%23%24%u534E%u5B89%u6838%u5FC3%u4F18%u9009%u6DF7%u5408@%23%24040011; ' \
             'EMFUND9=07-12 17:04:05@#$%u534E%u590F%u6210%u957F%u6DF7%u5408@%23%24000001; ' \
             'st_pvi=59785459609200; st_sp=2021-02-18%2019%3A09%3A39; st_inirUrl=https%3A%2F%2Fwww.baidu.com%2Flink; ' \
             'st_sn=34; st_psi=20210712170405323-112200305282-1009648685'

    headers = {
        'Cookie': cookie,
        'Host': 'api.fund.eastmoney.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Referer': 'http://fundf10.eastmoney.com/jjjz_%s.html' % fundcode,
    }

    params = {
        'callback': 'jQuery18302946412955619069_1626079645843',
        'fundCode': fundcode,
        'pageIndex': pageIndex,
        'pageSize': 20,
    }

    try:
        r = requests.get(url='http://api.fund.eastmoney.com/f10/lsjz', headers=headers, params=params)
        if r.status_code == 200:
            return r.text
        return None
    except Exception as e:
        return None


def parse_one_page(html):
    """解析网页内容"""
    if html is not None:
        content = re.findall('\((.*?)\)', html)[0]
        lsjz_list = json.loads(content)['Data']['LSJZList']
        total_count = json.loads(content)['TotalCount']
        total_page = math.ceil(total_count / 20)
        lsjz = pd.DataFrame(lsjz_list)
        info = {
            'lsjz': lsjz,
            'total_page': total_page
        }
        return info
    return None


def main(fundcode):
    """将爬取的基金净值数据储存至本地csv文件"""
    html = get_one_page(fundcode)
    info = parse_one_page(html)
    total_page = info['total_page']
    lsjz = info['lsjz']
    lsjz.to_csv(f'./{fundcode}_{datetime.datetime.now().strftime("%Y-%m-%d")}_lsjz.csv', index=False)
    page = 1
    total_page = 2 # 自定义值
    while page < total_page:
        page += 1
        html = get_one_page(fundcode, pageIndex=page)
        info = parse_one_page(html)
        if info is None:
            break
        lsjz = info['lsjz']
        lsjz.to_csv(f'./{fundcode}_{datetime.datetime.now().strftime("%Y-%m-%d")}_lsjz.csv', mode='a', index=False, header=False)
        time.sleep(random.randint(1, 5))


if __name__ == '__main__':

    # get_fundcode()

    fund_code_name()

    time.sleep(random.randint(1, 5))

    fund_codes = pd.read_csv(f'./{datetime.datetime.now().strftime("%Y-%m-%d")}_指数基金.csv')
    for fund_index, row in fund_codes.iterrows():
        fundcode = str(row['基金代码']).zfill(6)
        pzgs = get_pzgs(fundcode)
        main(fundcode)
        fundcodes = pd.read_csv(f'./{fundcode}_{datetime.datetime.now().strftime("%Y-%m-%d")}_lsjz.csv', converters={'fundcode': str})
        for index, dwjz in enumerate(fundcodes.sort_values(by="DWJZ", ascending=True)['DWJZ']):
            if float(pzgs) < float(dwjz):
                jzpm = (0 if (int(index) - 1) < 0 else (int(index) - 1)) / (40 - 1)
                _jzpm = round(jzpm, 5)
                if _jzpm == float(0.00000):
                    log.critical(f"基金排名：{fund_index + 1}")
                    log.critical(f"基金名称: {row['基金简称']}")
                    log.critical(f"基金代码: {fundcode}")
                    log.critical(f"盘中估算: {pzgs}")
                    log.critical(f"净值百分位排名: {jzpm}")
                elif _jzpm >= float(0.80000):
                    log.warning(f"基金排名：{fund_index + 1}")
                    log.warning(f"基金名称: {row['基金简称']}")
                    log.warning(f"基金代码: {fundcode}")
                    log.warning(f"盘中估算: {pzgs}")
                    log.warning(f"净值百分位排名: {jzpm}")
                elif float(0.00000) < _jzpm < float(0.80000):
                    log.info(f"基金排名：{fund_index + 1}")
                    log.info(f"基金名称: {row['基金简称']}")
                    log.info(f"基金代码: {fundcode}")
                    log.info(f"盘中估算: {pzgs}")
                    log.info(f"净值百分位排名: {jzpm}")
                break
            else:
                continue
        else:
            log.error(f"基金排名：{fund_index + 1}")
            log.error(f"基金名称: {row['基金简称']}")
            log.error(f"基金代码: {fundcode}")
            log.error(f"盘中估算: {pzgs}")
            log.error(f"净值百分位排名: -0.0")

        time.sleep(random.randint(1, 5))
