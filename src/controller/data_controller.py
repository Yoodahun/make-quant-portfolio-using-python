import pandas as pd
import numpy as np
from pandas import DataFrame

from src.crawling.sector_and_indicator_crawler import SectorAndIndicatorCrawler
from src.db.db_executer import DbExecuter

class DataController:
    def __init__(self):
        self.sector_and_indicator_crawler = SectorAndIndicatorCrawler()
        self.db_executor = DbExecuter()


    def merge_and_insert_crawled_sector_and_stock_indicator_data(self)->DataFrame:
        sector_data = self.sector_and_indicator_crawler.crawling_sector()
        indicator_data = self.sector_and_indicator_crawler.crawling_stock_indicator()

        diff = list(set(sector_data['종목명']).symmetric_difference(set(indicator_data['종목명'])))

        korean_ticker_data = pd.merge(sector_data, indicator_data,
                                      on=sector_data.columns.intersection(indicator_data.columns).tolist(),
                                      how='outer'
                                      )

        korean_ticker_data['종목구분'] = np.where(korean_ticker_data["종목명"].str.contains('스팩|제[0-9+]호'), "스팩",
                                              np.where(korean_ticker_data["종목코드"].str[-1:] != '0', "우선주",
                                                       np.where(korean_ticker_data["종목명"].str.endswith("리츠"), '리츠',
                                                                np.where(korean_ticker_data["종목명"].isin(diff), '기타','보통주'))))

        korean_ticker_data = korean_ticker_data.reset_index(drop=True)
        korean_ticker_data.columns = korean_ticker_data.columns.str.replace(" ", "")
        korean_ticker_data = korean_ticker_data[
            ["종목코드", "종목명", "시장구분", "종가", "시가총액", "기준일", "EPS", "선행EPS", "BPS", "주당배당금", "종목구분"]
        ]
        korean_ticker_data = korean_ticker_data.replace({np.nan:None})
        korean_ticker_data['기준일'] = pd.to_datetime(korean_ticker_data["기준일"])

        self.db_executor.insert_crawled_serctor_and_stock_indicator_data(korean_ticker_data)




