import pymysql
from src.utilities import get_config
from sqlalchemy import create_engine, Engine
import os


def get_db_engine() -> Engine:
    is_action = False
    engine_info = ""
    try:
        is_action = bool(os.environ["IS_GITHUB_ACTION"])
    except KeyError:
        pass

    if is_action:
        engine_info = f'mysql+pymysql://{os.environ["DB_USER"]}:{os.environ["DB_PW"]}@{os.environ["DB_HOST"]}:{os.environ["DB_PORT"]}/{os.environ["DB"]}'
    else:
        db_config = get_config('db_config')['DB_CONFIG']
        engine_info = f'mysql+pymysql://{db_config["USER"]}:{db_config["PW"]}@{db_config["HOST"]}:{db_config["PORT"]}/{db_config["DB"]}'

    return create_engine(engine_info)


def db_executemany(query, args):
    db_config = get_config('db_config')['DB_CONFIG']

    con = pymysql.connect(
        user=db_config["USER"],
        password=db_config["PW"],
        host=db_config["HOST"],
        port=int(db_config["PORT"]),
        db=db_config["DB"],
        charset='utf8'
    )

    mycursor = con.cursor()
    mycursor.executemany(query, args)

    con.commit()
    con.close()
