import re
import time

import requests as rq
from io import BytesIO
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from pandas import DataFrame

from src.crawling.biz_day_crawler import biz_day_crawler


class SectorAndIndicatorCrawler:
    """
    크롤링을 하기위한 클래스

    """
    def __init__(self):
        self.gen_otp_url = 'http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd'
        self.header = {
            "Referer": 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader'
        }
        self.down_url = 'http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd'
        self.biz_day = biz_day_crawler()

        print(self.biz_day)

    def crawling_sector(self) -> DataFrame:
        kospi = self.__crawling_sector_kospi()
        kosdaq = self.__crawling_sector_kosdaq()

        krx_sector = pd.concat([kospi, kosdaq]).reset_index(drop=True)
        krx_sector['종목명'] = krx_sector['종목명'].str.strip()
        krx_sector['기준일'] = self.biz_day

        return krx_sector

    def __crawling_sector_kospi(self):
        """
        코스피 섹터 종목,업종 크롤링

        :return:
        """
        gen_otp_stock = {
            'mktId': 'STK',
            'trdDd': self.biz_day,
            'money': '1',
            'csvxls_isNo': 'false',
            'name': 'fileDown',
            'url': 'dbms/MDC/STAT/standard/MDCSTAT03901'
        }

        otp_kospi = rq.post(self.gen_otp_url, gen_otp_stock, headers=self.header).text
        return self.__download_data(otp_kospi)

    def __crawling_sector_kosdaq(self):
        """
        코스닥 섹터 종목,업종 크롤링
        :return:
        """
        gen_otp_stock = {
            'mktId': 'KSQ',
            'trdDd': self.biz_day,
            'money': '1',
            'csvxls_isNo': 'false',
            'name': 'fileDown',
            'url': 'dbms/MDC/STAT/standard/MDCSTAT03901'
        }

        otp_kosdaq = rq.post(self.gen_otp_url, gen_otp_stock, headers=self.header).text

        return self.__download_data(otp_kosdaq)

    def crawling_stock_indicator(self) -> DataFrame:
        """
        주식 전 종목 기본지표 크롤링
        종목코드, 종목명, 종가, 등락률, eps, per, 선행 eps, 선행 per, bps, pbr, 주당배당금, 배당수익률

        :return:
        """
        gen_otp_stock_info_for_request = {
            'searchType': '1',
            'mktId': 'ALL',
            'trdDd': self.biz_day,
            'csvxls_isNo': 'false',
            'name': 'fileDown',
            'url': 'dbms/MDC/STAT/standard/MDCSTAT03501'
        }

        otp = rq.post(self.gen_otp_url, gen_otp_stock_info_for_request, headers=self.header).text

        data = self.__download_data(otp)

        data['종목명'] = data['종목명'].str.strip()
        data['기준일'] = self.biz_day

        return data

    def __download_data(self, code: str):
        downloaded_sector_info = rq.post(self.down_url, {'code': code}, headers=self.header)
        return pd.read_csv(BytesIO(downloaded_sector_info.content), encoding='EUC-KR')

    def crawling_wics_sector_info(self) -> DataFrame:
        """
        WICS 섹터정보 크롤링

        :return:
        """
        sector_code = ["G25", "G35", "G50", "G40", "G10", "G20", "G55", "G30", "G15", "G45"]

        data_sector = []
        for i in tqdm(sector_code):
            url = f"http://www.wiseindex.com/Index/GetIndexComponets?ceil_yn=0&dt={self.biz_day}&sec_cd={i}"
            data = rq.get(url).json()
            data_pd = pd.json_normalize(data["list"])

            data_sector.append(data_pd)
            time.sleep(1)

        korea_sector = pd.concat(data_sector, axis=0)  # 리스트안에는 데이터프레임 객체들이 들어있는데 그걸 다 합침
        korea_sector = korea_sector[['IDX_CD', 'CMP_CD', 'CMP_KOR', 'SEC_NM_KOR']]  # 섹터 코드, 티커, 종목명, 섹터명
        korea_sector['기준일'] = self.biz_day
        korea_sector['기준일'] = pd.to_datetime(korea_sector['기준일'])

        return korea_sector

    def crawling_adjust_stock_price(self, ticker: str, from_date:str, to_date:str) -> DataFrame:
        """
        수정주가 크롤링

        :param ticker:
        :param from_date:
        :param to_date:
        :return:
        """

        url = f"https://fchart.stock.naver.com/siseJson.nhn?symbol={ticker}&requestType=1&startTime={from_date}&endTime={to_date}&timeframe=day"

        data = rq.get(url).content
        data_price = pd.read_csv(BytesIO(data))

        price: DataFrame = data_price.iloc[:, 0:6]
        price.columns = ["날짜", "시가", "고가", "저가", "종가", "거래량"]

        price = price.dropna()

        price["날짜"] = price["날짜"].str.extract('(\d+)')

        price["날짜"] = pd.to_datetime(price["날짜"])
        price["종목코드"] = ticker

        return price

    def crawling_financial_statement(self, ticker:str)->DataFrame:
        """
        재무제표 크롤링

        :param ticker:
        :return:
        """
        url = f"https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A{ticker}"
        data = pd.read_html(url, displayed_only=False)

        return data

    def crawling_fiscal_date(self, ticker:str)->list:
        """
        결산월 리턴

        :param ticker:
        :return:
        """
        url = f"https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A{ticker}"
        page_data = rq.get(url)
        page_data_html = BeautifulSoup(page_data.content,'html.parser')

        fiscal_data = page_data_html.select('div.corp_group1>h2')
        fiscal_data_text = re.findall('[0-9]+', fiscal_data[1].text)

        return fiscal_data_text

