from pandas import DataFrame
from src.db.db_cursor import db_executemany


class DbExecuter:
    def __init__(self):
        pass

    def insert_crawled_serctor_and_stock_indicator_data(self, data:DataFrame):

        query = f"""            
            insert into kor_ticker (종목코드, 종목명, 시장구분, 종가, 시가총액, 기준일, EPS, 선행EPS, BPS, 주당배당금, 종목구분)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) as new 
            on duplicate key update
            종목명=new.종목명, 시장구분=new.시장구분, 종가=new.종가, 시가총액=new.시가총액, EPS=new.EPS, 선행EPS=new.선행EPS, 
            BPS=new.BPS, 주당배당금=new.주당배당금, 종목구분=new.종목구분;
        """

        args = data.values.tolist()
        db_executemany(query, args)

