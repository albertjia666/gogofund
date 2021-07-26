# encoding=utf-8
import pandas as pd
import requests
from lxml import etree
import re
import collections
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


cookie = 'st_si=50042120533408; st_asi=delete; qgqp_b_id=75d7da532bb4bf938c20a91c4f8a1118; ' \
             'EMFUND1=null; EMFUND2=null; EMFUND3=null; EMFUND4=null; EMFUND5=null; EMFUND6=null; EMFUND0=null; ' \
             'EMFUND7=07-12%2012%3A39%3A17@%23%24%u4E2D%u822A%u745E%u660E%u7EAF%u503AA@%23%24007555; ' \
             'EMFUND8=07-12%2015%3A35%3A50@%23%24%u534E%u5B89%u6838%u5FC3%u4F18%u9009%u6DF7%u5408@%23%24040011; ' \
             'EMFUND9=07-12 17:04:05@#$%u534E%u590F%u6210%u957F%u6DF7%u5408@%23%24000001; ' \
             'st_pvi=59785459609200; st_sp=2021-02-18%2019%3A09%3A39; st_inirUrl=https%3A%2F%2Fwww.baidu.com%2Flink; ' \
             'st_sn=34; st_psi=20210712170405323-112200305282-1009648685'

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36'


def fund_code_name():
    """ 筛选天天基金，最近三个月收益率排在前50强的指数型基金"""

    header = {
        'User-Agent': user_agent,
        'Referer': 'http://fund.eastmoney.com/data/fundranking.html',
        'Cookie': cookie

    }

    d = datetime.strptime(datetime.now().strftime("%Y-%m-%d"), "%Y-%m-%d")
    time_range = f"sd={str((d - relativedelta(years=1)).strftime('%Y-%m-%d'))}&ed={str(datetime.now().strftime('%Y-%m-%d'))}"

    response = requests.get(
        url='http://fund.eastmoney.com/data/rankhandler.aspx?op=ph&dt=kf&ft=zs&rs=&gs=0&sc=3yzf&st=desc&%s&qdii=|&tabSubtype=,,,,,&pi=1&pn=50&dx=1&v=0.942965085964089' % time_range,
        headers=header)
    text = response.text
    content = re.findall('\\[(.*?)]', text)[0]
    replace_quota = content.replace('"', "")
    quota_arrays = replace_quota.split(",")
    intervals = [[i * 25, (i + 1) * 25] for i in range(50)]

    narrays = []
    for k in intervals:
        narrays.append(quota_arrays[k[0]:k[1]])

    header = ["基金代码", "基金简称", "基金条码", "日期",
              "单位净值", "累计净值", "日增长率", "近1周增长率", "近1月增长率", "近3月", "近半年", "近1年", "近2年", "近3年",
              "今年来", "成立来", "其他1", "其他2", "其他3", "其他4", "其他5", "其他6", "其他7", "其他8", "其他9"]
    df = pd.DataFrame(narrays, columns=header)

    df_part = df[["基金代码", "基金简称", "日期", "单位净值", "累计净值", "日增长率", "近1周增长率", "近1月增长率", "近3月", "近半年"]]
    df_part.to_csv(f"{datetime.now().strftime('%Y-%m-%d')}_50强基金收益.csv", encoding="utf_8_sig")

    rank_fund_code = df_part.head(50)["基金代码"]
    fund_codes_list = rank_fund_code.values.tolist()
    print("前50指数型强基金: ", fund_codes_list)
    return fund_codes_list


def get_one_fund_stocks(fund_code):
    """根据基金码,获取每一支基金的最新一季度所有持仓股票池前10支股票"""

    header = {
        'User-Agent': user_agent,
        'Cookie': cookie
    }

    response = requests.get(
        url="http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={}&topline=10&year=&month=&rt=0.5032668912422176".format(fund_code),
        headers=header)
    text = response.text
    div = re.findall('content:\\"(.*)\\",arryear', text)[0]
    html_body = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>test</title></head><body>%s</body></html>' % (div)
    html = etree.HTML(html_body)

    stock_info = html.xpath('//div[1]/div/table/tbody/tr/td/a')
    stock_money = html.xpath('//div[1]/div/table/tbody/tr/td')
    stock_one_fund = []
    for stock in stock_info:
        if stock.text and stock.text.isdigit():
            stock_one_fund.append(stock.text)
    if len(stock_one_fund) > 1:
        print("基金代码：{}".format(fund_code), "基金持有前10股票池", stock_one_fund)
    return stock_one_fund

    # stock_info = html.xpath("//div[1]/div/table/tbody/tr")
    # stock_one_fund = []
    # for item_tr in stock_info:
    #     stock_item = []
    #     item_td_a = item_tr.xpath("td/a")
    #     for td_a in item_td_a:
    #         if td_a.text not in ["变动详情","股吧","行情", "档案", None]:
    #             stock_item.append(td_a.text)
    #     item_td = item_tr.xpath("td")
    #     for td in item_td:
    #         if td.text not in ["1","2","3","4","5","6","7","8","9","10", None]:
    #             stock_item.append(td.text)
    #     stock_one_fund.append(stock_item)
    #
    # header = ["股票代码", "股票名称", "占净值比例", "持股数(万股)", "持仓市值(万元)"]
    # df = pd.DataFrame(stock_one_fund, columns=header)
    # print(df)


def static_best_stock(rank=20):
    """ 统计收益最佳前50机构共同持有股票代码情况,修改rank数量可调整展示股票排名数目"""
    rank_codes = fund_code_name()
    stocks_array = []
    for index, code in enumerate(rank_codes):
        if index < 1:
            print("<" * 30 + " FBI WARNING 近1周收益最高基金的排名高到低排序以及股票池情况 " + ">" * 30)
        stocks = get_one_fund_stocks(code)
        if len(stocks) > 1 and stocks:
            stocks_array.extend(stocks)
    print(stocks_array)
    count_each_stock = collections.Counter(stocks_array)
    print(count_each_stock)
    print("<" * 30 + "FBI WARNING,{}".format(static_best_stock.__doc__) + ">" * 30)
    print("#" * 30 + "本季度基金机构共同持有股票数目排行前{}股票代码情况".format(rank) + "#" * 30)
    df = pd.DataFrame.from_dict(count_each_stock, orient='index', columns=["持有该股机构数目"])
    df = df.reset_index().rename(columns={"index": "股票代码"})
    # for k, v in count_each_stock.items():
    #     print("股票代码: ", k, "持有该股票机构数量: ", v)
    df = df.sort_values(by="持有该股机构数目", ascending=False)
    print(df.head(rank))


if __name__ == '__main__':
    fund_code_name()
    # get_one_fund_stocks('501057')
    # static_best_stock()
