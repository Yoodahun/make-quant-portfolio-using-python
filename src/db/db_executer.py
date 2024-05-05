from pandas import DataFrame
import pandas as pd
from src.db.db_cursor import db_executemany, get_db_engine


def insert_crawled_serctor_and_stock_indicator_data(data: DataFrame):
    query = f"""            
        insert into kor_ticker (종목코드, 종목명, 시장구분, 종가, 시가총액, 기준일, EPS, 선행EPS, BPS, 주당배당금, 종목구분)
        values (%s, %s, %s, %s, %s, %s, %s, null, %s, %s, %s) as new 
        on duplicate key update
        종목명=new.종목명, 시장구분=new.시장구분, 종가=new.종가, 시가총액=new.시가총액, EPS=new.EPS, 
        BPS=new.BPS, 주당배당금=new.주당배당금, 종목구분=new.종목구분
        ;
    """

    args = data.values.tolist()
    db_executemany(query, args)


def insert_wics_sector_info_data(data: DataFrame):
    query = """
        insert into kor_sector (IDX_CD, CMP_CD, CMP_KOR, SEC_NM_KOR, 기준일)
        values( %s, %s, %s, %s, %s ) as new
        on duplicate key update
        IDX_CD = new.IDX_CD, CMP_KOR = new.CMP_KOR, SEC_NM_KOR = new.SEC_NM_KOR
        ;
    """

    args = data.values.tolist()
    db_executemany(query, args)


def select_ticker_list_where_max_date() -> DataFrame:
    engine = get_db_engine()
    data = pd.read_sql("""
        select * from kor_ticker
        where 기준일 = (select max(기준일) from kor_ticker)
        and 종목구분 = '보통주'
        ;
    """, con=engine)
    engine.dispose()
    return data

def insert_adjust_stock_price(data:DataFrame):
    query = """
        insert into kor_price (날짜, 시가, 고가, 저가, 종가, 거래량 ,종목코드)
        values (%s,%s,%s,%s,%s,%s,%s) as new
        on duplicate key update 
        시가 = new.시가, 고가 = new.고가, 저가 = new.저가, 종가=new.종가, 거래량=new.거래량
        ;
    """

    args = data.values.tolist()
    db_executemany(query, args)

def insert_financial_statement(data:DataFrame):
    query = """
        insert into kor_fs(계정, 기준일, 값, 종목코드, 공시구분)
        values (%s, %s, %s, %s, %s) as new
        on duplicate key update 
        값=new.값     
"""
    args = data.values.tolist()
    db_executemany(query, args)

def select_quarterly_financial_statement_for_calculate_factor_using_marketcap()->DataFrame:
    """
    분기 재무제표 데이터를 리턴합니다.
    당기순이익', '자본', '영업활동으로인한현금흐름', '매출액', '매출총이익', '영업이익', 'FCF
    :return: DataFrame
    """
    engine = get_db_engine()
    data = pd.read_sql("""
      select * from kor_fs
      where 공시구분 = 'q'
      and 계정 in ('당기순이익', '자본', '영업활동으로인한현금흐름', '매출액', '매출총이익', '영업이익', 'FCF')
    ;
    """, con=engine)
    engine.dispose()
    return data
def select_quarterly_financial_statement_for_calculate_factor_not_using_marketcap()->DataFrame:
    """
    분기 재무제표 데이터를 리턴합니다.
    '당기순이익','매출총이익','영업활동으로인한현금흐름','자산','자본', '유형자산', '부채'
    :return: DataFrame
    """
    engine = get_db_engine()
    data = pd.read_sql("""
      select * from kor_fs
      where 공시구분 = 'q'
      and 계정 in ('당기순이익','매출총이익','영업활동으로인한현금흐름','자산','자본', '유형자산', '부채')
    ;
    """, con=engine)
    engine.dispose()
    return data
def insert_value_factor_date(data:DataFrame ):
    query= """
        insert into kor_value (종목코드, 기준일, 지표, 값)
        values (%s, %s, %s, %s) as new
        on duplicate key update 
        값=new.값
    """

    args = data.values.tolist()
    db_executemany(query, args)

def insert_profitability_factor_date(data:DataFrame ):
    query= """
        insert into kor_profitability (종목코드, 기준일, ROE, GPA, NAV, CFO, 부채비율)
        values (%s, %s, %s, %s, %s, %s, %s) as new
        on duplicate key update 
        기준일=new.기준일, ROE=new.ROE, GPA=new.GPA, NAV=new.NAV, CFO=new.CFO, 부채비율=new.부채비율
    """

    args = data.values.tolist()
    db_executemany(query, args)

def select_value_data_where_max_date()->DataFrame:
    """
    최근 기준일 기준 밸류 데이터를 가져온다.

    :return:
    """
    engine = get_db_engine()
    data = pd.read_sql("""
      select * from kor_value
      where 기준일 = (select max(기준일) from kor_value)
    ;
    """, con=engine)
    engine.dispose()
    return data

def select_price_where_max_date_from_1_year():
    """
    최신날짜로부터 1년전 데이터들을 전부 뽑아온다.

    :return:
    """
    engine = get_db_engine()
    data = pd.read_sql("""
      select 날짜, 종가, 종목코드
      from kor_price
      where 날짜 >= (select (select max(날짜) from kor_price) - interval 1 year)
    ;
    """, con=engine)
    engine.dispose()
    return data

def select_profit_factor_where_max_date():
    """
    수익성지표를 리턴합니다.

    :return:
    """
    engine = get_db_engine()
    data = pd.read_sql("""
      select 종목코드, 기준일, ROE, GPA, CFO, 부채비율
      from kor_profitability
      where 기준일 >= (select max(기준일) from kor_profitability)
    ;
    """, con=engine)
    engine.dispose()
    return data

def select_from_kor_sector_where_max_date()->DataFrame:
    engine = get_db_engine()
    data = pd.read_sql("""
      select *
      from kor_sector
      where 기준일 = (select max(기준일) from kor_sector)
    ;
    """, con=engine)
    engine.dispose()

    return data

def select_max_date_from_kor_price()->DataFrame:
    engine = get_db_engine()
    data = pd.read_sql("""
      select max(날짜)
      from kor_price
    ;
    """, con=engine)
    engine.dispose()

    return data








