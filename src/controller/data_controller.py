import time
import traceback

import pandas as pd
import numpy as np
from pandas import DataFrame
from datetime import date
from dateutil.relativedelta import relativedelta
from src.crawling.sector_and_indicator_crawler import SectorAndIndicatorCrawler
from src.db.db_executer import *
from tqdm import tqdm


class DataController:
    def __init__(self):
        self.sector_and_indicator_crawler = SectorAndIndicatorCrawler()

    def merge_and_insert_crawled_sector_and_stock_indicator_data(self):
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
                                                                np.where(korean_ticker_data["종목명"].isin(diff), '기타',
                                                                         '보통주'))))

        korean_ticker_data = korean_ticker_data.reset_index(drop=True)
        korean_ticker_data.columns = korean_ticker_data.columns.str.replace(" ", "")
        korean_ticker_data = korean_ticker_data[
            ["종목코드", "종목명", "시장구분", "종가", "시가총액", "기준일", "EPS", "선행EPS", "BPS", "주당배당금", "종목구분"]
        ]
        korean_ticker_data = korean_ticker_data.replace({np.nan: None})
        korean_ticker_data['기준일'] = pd.to_datetime(korean_ticker_data["기준일"])

        insert_crawled_serctor_and_stock_indicator_data(korean_ticker_data)

    def insert_wics_sector_info_data(self):
        sector_data = self.sector_and_indicator_crawler.crawling_wics_sector_info()
        insert_wics_sector_info_data(sector_data)

    def insert_adjust_stock_price(self):
        ticker_list = select_ticker_list_where_max_date()

        from_date = (date.today() + relativedelta(days=-8)).strftime("%Y%m%d")

        to_date = (date.today()).strftime("%Y%m%d")

        print(f"{from_date} ~ {to_date}")

        for i in tqdm(range(len(ticker_list))):
            try:
                price = self.sector_and_indicator_crawler.crawling_adjust_stock_price(
                    ticker_list["종목코드"][i], from_date, to_date
                )
                insert_adjust_stock_price(price)
            except Exception:

                print(f"수정주가 조회 혹은 삽입 실패 : {ticker_list['종목코드'][i]} {ticker_list['종목명'][i]}")
                traceback.print_exc()

            time.sleep(0.6)

    def merge_and_insert_financial_statement_data(self):
        ticker_list = select_ticker_list_where_max_date()

        for i in tqdm(range(len(ticker_list))):
            try:
                ticker_code = ticker_list["종목코드"][i]
                data = self.sector_and_indicator_crawler.crawling_financial_statement(ticker_code)
                fiscal_month = self.sector_and_indicator_crawler.crawling_fiscal_date(ticker_code)

                data_fs_y = self.filtering_financial_statement_annual_or_quarterly(data, "y")
                data_fs_y = data_fs_y.loc[:, (data_fs_y.columns == '계정') | (
                    data_fs_y.columns.str[-2:].isin(fiscal_month))]  # 결산월에 해당하는 데이터와 계정과목만 추려냄
                data_fs_q = self.filtering_financial_statement_annual_or_quarterly(data, "q")

                data_fs_y_after_cleansing = self.clean_fs_column(data_fs_y, ticker_code, "y")
                data_fs_q_after_cleansing = self.clean_fs_column(data_fs_q, ticker_code, "q")

                data_merged = pd.concat([data_fs_y_after_cleansing, data_fs_q_after_cleansing])

                # data_merged = data_merged.where(pd.notnull(data_merged), None)
                insert_financial_statement(data_merged)
            except Exception:
                print(f"재무제표 조회 실패 : {ticker_list['종목코드'][i]} {ticker_list['종목명'][i]}")

            time.sleep(0.5)

    def calculate_and_insert_value_factor_data(self):
        """
        가치 지표 계산

        :return:
        """
        ticker_list = select_ticker_list_where_max_date()

        fs_data_value_factor = select_quarterly_financial_statement_for_calculate_factor_using_marketcap()
        fs_data_profit_factory = select_quarterly_financial_statement_for_calculate_factor_not_using_marketcap()

        fs_data_value_factor = self.__calculate_ttm(fs_data_value_factor)
        fs_data_profit_factory = self.__calculate_ttm(fs_data_profit_factory)

        # 시가총액을 이용한 밸류지표 계산하기
        fs_data_value_factor = self.__calculate_value_factor_using_market_cap(fs_data_value_factor, ticker_list)
        # 수익성지표 계산하기
        fs_data_profit_factory = self.__calculate_profitability_factor(fs_data_profit_factory, ticker_list)

        # 시가총액을 이용한 팩터데이터 계산 후 저장
        insert_value_factor_date(fs_data_value_factor)
        # 수익성지표 저장
        insert_profitability_factor_date(fs_data_profit_factory)
        # 배당수익률 계산 후 저장
        insert_value_factor_date(self.__calculate_dy(ticker_list))

    def __calculate_ttm(self, fs_data: DataFrame) -> DataFrame:
        fs_data = fs_data.sort_values(['종목코드', '계정', '기준일'])
        # 각 계정의 ttm 값 구하기
        fs_data['ttm'] = fs_data.groupby(['종목코드', '계정'], as_index=False)['값'].rolling(window=4, min_periods=4).sum()[
            '값']

        # 자본의 평균구하기
        fs_data['ttm'] = np.where(fs_data['계정'].isin(['자본', '자산', '부채', '유형자산']), fs_data['ttm'] / 4, fs_data['ttm'])
        fs_data = fs_data.groupby(['계정', '종목코드']).tail(1)

        return fs_data

    def __calculate_value_factor_using_market_cap(self, fs_data: DataFrame, ticker_list: DataFrame) -> DataFrame:
        """

        :param data:
        :return:
        """
        ##티커 리스트와 합치기
        fs_data = fs_data[['계정', '종목코드', 'ttm']].merge(
            ticker_list[['종목코드', '시가총액', '기준일']], on='종목코드'
        )

        fs_data['시가총액'] = fs_data['시가총액'] / 100000000  # 시가총액 단위를 억 으로 맞춘다.

        fs_data['value'] = fs_data['시가총액'] / fs_data['ttm']
        fs_data['value'] = fs_data['value'].round(4)

        # 지표명을 입력한다.
        fs_data['지표'] = self.__calculate_value_factor_name(fs_data)

        fs_data.rename(columns={'value': '값'}, inplace=True)

        fs_data_merged = fs_data[['종목코드', '기준일', '지표', '값']]
        fs_data_merged = fs_data_merged.replace([np.inf, -np.inf, np.nan], None)

        return fs_data_merged

    def __calculate_value_factor_name(self, data: DataFrame) -> DataFrame:
        """
        팩터데이터의 이름을 정해서 입력
        :param data:
        :return:
        """
        data = np.where(data['계정'] == '매출액', 'PSR',
                        np.where(data['계정'] == '영업활동으로인한현금흐름', 'PCR',
                                 np.where(data['계정'] == '자본', 'PBR',
                                          np.where(data['계정'] == '당기순이익', 'PER',
                                                   np.where(data['계정'] == "매출총이익", "PGPR",
                                                            np.where(data['계정'] == '영업이익', 'POR',
                                                                     np.where(data['계정'] == 'FCF', 'PFCR', None)
                                                                     )
                                                            )
                                                   )
                                          )
                                 )
                        )

        return data

    def __calculate_profitability_factor(self, fs_data: DataFrame, ticker_list: DataFrame) -> DataFrame:
        """

        수익성지표 계산
        :param fs_data:
        :param ticker_list:
        :return:
        """
        ticker_list.sort_values(['종목코드'])
        fs_data_pivot = fs_data.pivot(index='종목코드', columns='계정', values='ttm')
        fs_data_pivot['ROE'] = fs_data_pivot['당기순이익'] / fs_data_pivot['자본']
        fs_data_pivot['GPA'] = fs_data_pivot['매출총이익'] / fs_data_pivot['자산']
        fs_data_pivot['CFO'] = fs_data_pivot['영업활동으로인한현금흐름'] / fs_data_pivot['자산']
        fs_data_pivot['부채비율'] = fs_data_pivot['부채'] / fs_data_pivot['자본']

        quality_fs_data = ticker_list[['종목코드', '기준일', '시가총액']].merge(fs_data_pivot, how='left', on='종목코드')

        quality_fs_data['NAV'] = (quality_fs_data['유형자산'] - quality_fs_data['부채']) / quality_fs_data['시가총액']

        quality_fs_data = quality_fs_data[['종목코드', '기준일', 'ROE', 'GPA', 'NAV', 'CFO', '부채비율']]
        quality_fs_data = quality_fs_data.replace([np.inf, -np.inf, np.nan], None)

        quality_fs_data = quality_fs_data.where(pd.notnull(quality_fs_data), None)

        return quality_fs_data

    def __calculate_dy(self, data: DataFrame) -> DataFrame:
        """
        배당수익률을 계산
        :param data:
        :return:
        """
        data['값'] = data['주당배당금'] / data['종가']
        data['값'] = data['값'].round(4)
        data['지표'] = 'DY'
        dy_list = data[['종목코드', '기준일', '지표', '값']]
        dy_list = dy_list.replace([np.inf, -np.inf, np.nan], None)

        dy_list = dy_list[dy_list['값'] != 0]

        return dy_list

    def filtering_financial_statement_annual_or_quarterly(self, data: DataFrame, frequency: str) -> DataFrame:
        """
        연간데이터 혹은 분기데이터를 구분한다.
        :param data:
        :param frequency:
        :return:
        """

        if frequency == "y":
            data = pd.concat(
                [data[0].iloc[:, ~data[0].columns.str.contains('전년동기')], data[2], data[4]]
            )  # 연간 연결재무제표
        else:
            data = pd.concat(
                [data[1].iloc[:, ~data[1].columns.str.contains('전년동기')], data[3], data[5]]
            )  # 분기 연결재무제표

        data = data.rename(columns={data.columns[0]: "계정"})
        return data

    def winsorize_data(self, value_data:DataFrame)->DataFrame:
        """
        이상치데이터를 극단값으로 대치하는 메소드

        :return:
        """



    def clean_fs_column(self, data: DataFrame, ticker: str, frequency: str) -> DataFrame:
        """
        불필요한 컬럼을 제거하고, 필요한 컬럼을 만들고 정제한다.

        :param data:
        :param ticker: 티커
        :param frequency: 연간/분기
        :return: DataFrame
        """

        data = data[
            ~data.loc[:, ~data.columns.isin(["계정"])].isna().all(axis=1)
        ]

        data = data.drop_duplicates(["계정"], keep='first')  # 계정 컬럼명이 중복되면 첫번쨰꺼만 남긴다.

        data = pd.melt(data, id_vars='계정', var_name='기준일',
                       value_name='값')  # 계정컬럼을 제외한 나머지 컬럼을 로우로 바꾸고, 해당 컬럼의 값을 로우의 옆으로 붙인다.

        data = data[~pd.isnull(data["값"])]  # 값 컬럼이 널값이면 없앤다

        data["계정"] = data["계정"].replace({"계산에 참여한 계정 펼치기": ""}, regex=True)  # 해당 계정값을 공란으로 없앤다.

        data['기준일'] = pd.to_datetime(data['기준일'],
                                     format='%Y/%m') + pd.tseries.offsets.MonthEnd()

        data["종목코드"] = ticker
        data["공시구분"] = frequency
        fcf_rows = []
        fcf_row = {}

        if frequency == "q":
            try:
                cash_flow_row = data[data['계정'] == '영업활동으로인한현금흐름']
                for row in range(len(cash_flow_row)):
                    asset_increase = data[data['계정'] == '유형자산의증가']

                    fcf_row = {
                        "계정": "FCF",
                        "기준일": cash_flow_row['기준일'].values[row],
                        "값": cash_flow_row['값'].values[row] - asset_increase['값'].values[row],
                        "종목코드": cash_flow_row['종목코드'].values[row],
                        "공시구분": frequency
                    }
                    fcf_rows.append(fcf_row)

            except IndexError:
                fcf_row = {
                    "계정": "FCF",
                    "기준일": data['기준일'].values[-1],
                    "값": 0,
                    "종목코드": data['종목코드'].values[-1],
                    "공시구분": frequency
                }
                fcf_rows.append(fcf_row)

            data = pd.concat([data, pd.DataFrame(fcf_rows)], ignore_index=False)


        return data
