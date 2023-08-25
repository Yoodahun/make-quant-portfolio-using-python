from pandas import DataFrame
import pandas as pd
from src.db.db_cursor import db_executemany, get_db_engine


def insert_crawled_serctor_and_stock_indicator_data(data: DataFrame):
    query = f"""            
        insert into kor_ticker (종목코드, 종목명, 시장구분, 종가, 시가총액, 기준일, EPS, 선행EPS, BPS, 주당배당금, 종목구분)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) as new 
        on duplicate key update
        종목명=new.종목명, 시장구분=new.시장구분, 종가=new.종가, 시가총액=new.시가총액, EPS=new.EPS, 선행EPS=new.선행EPS, 
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




