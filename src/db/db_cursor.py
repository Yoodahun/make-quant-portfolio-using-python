import pymysql
from src.utilities import get_config
from sqlalchemy import create_engine, Engine


def get_db_engine()->Engine:
    db_config = get_config("db_config")["DB_CONFIG"]
    engine_info = f'mysql+pymysql://{db_config["USER"]}:{db_config["PW"]}@{db_config["HOST"]}:{db_config["PORT"]}/{db_config["DB"]}'
    print(engine_info)
    return create_engine(engine_info)


def db_executemany(query, args):
    db_config = get_config("db_config")["DB_CONFIG"]

    con = pymysql.connect(
        user=db_config["USER"],
        password=db_config["PW"],
        host=db_config["HOST"],
        port=int(db_config["PORT"]),
        db=db_config["DB"],
        charset='utf8'
    )

    mycursor = con.cursor()
    mycursor.executemany(query,args)

    con.commit()
    con.close()

