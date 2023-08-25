import requests as rq
import re
from bs4 import BeautifulSoup


def biz_day_crawler() -> str:
    """
    최근 영업일 계산기 2영업일 이전 영업일
    :return:
    """
    url = 'https://finance.naver.com/sise/sise_deposit.nhn'
    data = rq.get(url)

    data_html = BeautifulSoup(data.content)
    parse_day = data_html.select_one(
        'div.subtop_sise_graph2 > ul.subtop_chart_note > li > span.tah'
    ).text

    biz_day = re.findall('[0-9]+', parse_day)
    biz_day = ''.join(biz_day)

    return biz_day
