from src.db.db_executer import *
import pandas as pd
import numpy as np
from pandas import DataFrame
import statsmodels.api as sm
from scipy.stats import zscore
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm

class PortfolioController:
    """
    뽑아 낸 데이터를 대상으로 포트폴리오를 만든다
    """

    def calculate_value_portfolio(self, for_portfolio=False) -> DataFrame:
        """
        밸류포트폴리오 구하기.
        for_portfolio가 True라면 포트폴리오 용도로 상위 20개 갯수만 출력하고, 그렇지 않으면 전체 갯수를 출력한다.

        """

        ticker_list = select_ticker_list_where_max_date()

        value_list = select_value_data_where_max_date()

        value_list.loc[value_list['값'] <= 0, '값'] = np.nan
        value_pivot = value_list.pivot(index="종목코드", columns='지표', values='값')

        data_bind = ticker_list[['종목코드', '종목명']].merge(value_pivot, how='left', on='종목코드')

        if for_portfolio:

            value_list_copy = data_bind.copy()
            value_list_copy['DY'] = 1 / value_list_copy['DY']  # 배당률은 배당률의 역순으로 한다.
            value_list_copy = value_list_copy[['PER', 'PBR', 'PCR', 'PSR', 'POR', 'PFCR', 'DY']]
            # value_list_copy = value_list_copy[['PER', 'PBR', 'PCR', 'PSR', 'POR', 'DY']]

            value_rank_all = value_list_copy.rank(axis=0).apply(zscore, nan_policy='omit')

            value_sum_all = value_rank_all.sum(axis=1, skipna=False).rank()
            return data_bind[value_sum_all<=20]
        else:
            return data_bind

    def calculate_momentum_portfolio(self, for_portfolio=False) -> DataFrame:

        """
        모멘텀 포트폴리오
        K-ratio를 구하는데, 완만하게 상승하는 주식을 계산한다.
        for_portfolio가 True라면 포트폴리오 용도로 상위 20개 갯수만 출력하고, 그렇지 않으면 전체 갯수를 출력한다.

        """
        ticker_list = select_ticker_list_where_max_date()
        price_list = select_price_where_max_date_from_1_year()

        price_pivot = price_list.pivot(index='날짜', columns='종목코드', values='종가')

        ret_list = pd.DataFrame(data=(price_pivot.iloc[-1] / price_pivot.iloc[0]) - 1,
                                columns=['12M'])  # 가장 끝행을 가장 첫행으로 나누어 12개월 수익률을 계산한다.
        data_result_momentum = ticker_list[['종목코드', '종목명']].merge(ret_list, how='left', on='종목코드')

        # K-Ratio 계산
        ret = price_pivot.pct_change().iloc[1:]
        ret_cum = np.log(1 + ret).cumsum()

        x = np.array(range(len(ret)))
        k_ratio = {}

        for i in range(len(ticker_list)):
            ticker = data_result_momentum.loc[i, '종목코드']

            try:
                y = ret_cum.loc[:, price_pivot.columns == ticker]
                reg = sm.OLS(y, x).fit()
                res = float(reg.params / reg.bse)
            except:
                res = np.nan

            k_ratio[ticker] = res

        k_ratio_bind = pd.DataFrame.from_dict(k_ratio, orient='index').reset_index()
        k_ratio_bind.columns = ['종목코드', 'K_ratio']

        data_result_momentum = data_result_momentum.merge(k_ratio_bind, how='left', on='종목코드')

        if for_portfolio:
            k_ratio_rank = data_result_momentum['K_ratio'].rank(axis=0, ascending=False)

            return data_result_momentum[k_ratio_rank <= 20]
        else:
            return data_result_momentum


    def calculate_quality_portfolio(self, for_portfolio=False) -> DataFrame:
        """
        우량성 포트폴리오
        for_portfolio가 True라면 포트폴리오 용도로 상위 20개 갯수만 출력하고, 그렇지 않으면 전체 갯수를 출력한다.

        :return:
        """
        ticker_list = select_ticker_list_where_max_date()
        profit_factor_list = select_profit_factor_where_max_date()

        for factor in ['ROE', 'GPA', 'CFO', '부채비율']:
            profit_factor_list[factor] = profit_factor_list[factor] * 100

        quality_list = ticker_list[['종목코드', '종목명']].merge(profit_factor_list, how='left', on='종목코드').round(4)

        if for_portfolio:

            quality_list_copy = quality_list[['ROE', 'GPA', 'CFO', '부채비율']].copy()
            quality_rank = quality_list_copy.rank(ascending=False, axis=0)

            quality_sum = quality_rank.sum(axis=1, skipna=False).rank()
            return quality_list.loc[quality_sum <= 20]
        else:
            return quality_list

    def calculate_multi_factor_portfolio(self, count:int)->DataFrame:
        """
        멀티팩터 포트폴리오 계산
        :return:
        """
        ticker_list = select_ticker_list_where_max_date()
        sector_list = select_from_kor_sector_where_max_date()

        value_portfolio = self.calculate_value_portfolio(for_portfolio=False)
        momentum_portfolio = self.calculate_momentum_portfolio(for_portfolio=False)
        quality_portfolio = self.calculate_quality_portfolio(for_portfolio=False)

        value_portfolio = value_portfolio.drop(['종목명'], axis=1)
        momentum_portfolio = momentum_portfolio.drop(['종목명'], axis=1)
        quality_portfolio = quality_portfolio.drop(['종목명', '기준일'], axis=1)

        data_bind = ticker_list[['종목코드', '종목명']].merge(
            sector_list[['CMP_CD', 'SEC_NM_KOR']], how='left', left_on='종목코드', right_on='CMP_CD').merge(
            value_portfolio, how='left', on='종목코드'
        ).merge(
            quality_portfolio, how='left', on='종목코드'
        ).merge(
            momentum_portfolio, how='left', on='종목코드'
        )

        data_bind.loc[data_bind['SEC_NM_KOR'].isnull(), 'SEC_NM_KOR'] = '기타'
        data_bind = data_bind.drop(['CMP_CD'], axis=1)

        # 섹터별 그룹화
        data_bind_group = data_bind.set_index(['종목코드', 'SEC_NM_KOR']).groupby('SEC_NM_KOR')

        #수익성
        z_quality = data_bind_group[['ROE', 'GPA', 'CFO']].apply(lambda x: self.clean_outlier(x)).sum(
            axis=1, skipna=False).to_frame('z_quality')

        data_bind = data_bind.merge(z_quality, how='left', on=['종목코드'])

        #밸류
        value_1 = data_bind_group[['PBR', 'PSR', 'PCR', 'PER']].apply(
            lambda x: self.clean_outlier(x, ascending=True))
        value_2 = data_bind_group[['DY']].apply(lambda x: self.clean_outlier(x))

        z_value = value_1.merge(value_2, on=['종목코드']).sum(axis=1, skipna=False).to_frame('z_value')

        data_bind = data_bind.merge(z_value, how='left', on=['종목코드'])

        # 모멘텀의 Z스코어
        z_momentum = data_bind_group[['12M', 'K_ratio']].apply(lambda x: self.clean_outlier(x)).sum(
            axis=1, skipna=False).to_frame("z_momentum")

        data_bind = data_bind.merge(z_momentum, how='left', on=['종목코드'])

        ## 3개 팩터 평균점수 계산
        data_bind_final = data_bind[['종목코드', 'z_quality', 'z_value', 'z_momentum']].set_index('종목코드').apply(zscore,
                                                                                                            nan_policy='omit')
        data_bind_final.columns = ['quality', 'value', 'momentum']

        ## 3개 팩터 평균점수 계산
        data_bind_final = data_bind[['종목코드', 'z_quality', 'z_value', 'z_momentum']].set_index('종목코드').apply(zscore,
                                                                                                            nan_policy='omit')
        data_bind_final.columns = ['quality', 'value', 'momentum']
        #
        wts = [0.3, 0.3, 0.3]  # 가중치
        data_bind_final_sum = (data_bind_final * wts).sum(axis=1, skipna=False).to_frame()
        data_bind_final_sum.columns = ['qvm']
        portfolio = data_bind.merge(data_bind_final_sum, on='종목코드')
        portfolio['invest'] = np.where(portfolio['qvm'].rank() <= count, 'Y', 'N')
        #
        portfolio = portfolio[portfolio['invest'] == 'Y'].round(4)

        self.show_graph(portfolio)

        return portfolio



    def clean_outlier(self, data: DataFrame, cutoff: float = 0.01, ascending: bool = False, ) -> DataFrame:
        """
        극단치를 없애고 평균점수를 계산한다.

        :param data:
        :param cutoff:
        :param ascending:
        :return:
        """

        q_low = data.quantile(cutoff)
        q_high = data.quantile(1 - cutoff)

        # data_trim= data[(data > q_low) & data < q_high]  # 이상치를 제외한 값들만 포함


        data_z_score = data.rank(axis=0, ascending=ascending).apply(zscore, nan_policy='omit')

        return data_z_score

    def show_graph(self, data:DataFrame):
        """
        그래프를 출력한다.

        :param self:
        :param data:
        """
        price_ticker = select_price_where_max_date_from_1_year()
        price_stock = price_ticker[price_ticker['종목코드'].isin(
            data['종목코드']
        )]

        path = '/System/Library/Fonts/AppleSDGothicNeo.ttc'  # 나눔 고딕
        font_name = fm.FontProperties(fname=path, size=10).get_name()  # 기본 폰트 사이즈 : 10
        plt.rc('font', family=font_name)

        g = sns.relplot(data=price_stock, x='날짜', y='종가',col='종목코드', col_wrap=5, kind='line', facet_kws={'sharey':False, 'sharex':True})

        g.set(xticklabels=[])
        g.set(xlabel=None)
        g.set(ylabel=None)
        g.fig.set_figwidth(15)
        g.fig.set_figheight(8)
        plt.subplots_adjust(wspace=0.5, hspace=0.2)
        plt.show()