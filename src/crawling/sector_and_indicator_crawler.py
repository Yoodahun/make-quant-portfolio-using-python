import requests as rq
from io import BytesIO
import pandas as pd
from pandas import DataFrame

from src.crawling.biz_day_crawler import biz_day_crawler


class SectorAndIndicatorCrawler:
    def __init__(self):
        self.gen_otp_url = 'http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd'
        self.header = {
            "Referer":'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader'
        }
        self.down_url = 'http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd'
        self.biz_day = biz_day_crawler()

    def crawling_sector(self)-> DataFrame:
        kospi = self.__crawling_sector_kospi()
        kosdaq = self.__crawling_sector_kosdaq()

        krx_sector = pd.concat([kospi, kosdaq]).reset_index(drop=True)
        krx_sector['종목명'] = krx_sector['종목명'].str.strip()
        krx_sector['기준일'] = self.biz_day

        return krx_sector

    def __crawling_sector_kospi(self):
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

    def crawling_stock_indicator(self)->DataFrame:
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

    def __download_data(self, code:str,):
        downloaded_sector_info = rq.post(self.down_url, {'code': code}, headers=self.header)
        return pd.read_csv(BytesIO(downloaded_sector_info.content), encoding='EUC-KR')

