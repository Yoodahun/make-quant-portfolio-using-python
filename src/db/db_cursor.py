import pymysql
from src.utilities import get_config
from sqlalchemy import create_engine, Engine
import os


def get_db_info() -> dict:
    is_action = False
    db_config = {}
    try:
        is_action = bool(os.environ["IS_GITHUB_ACTION"])
    except KeyError:
        pass

    if is_action:
        db_config["USER"] = os.environ["DB_USER"]
        db_config["PW"] = os.environ["DB_PW"]
        db_config["HOST"] = os.environ["DB_HOST"]
        db_config["PORT"] = os.environ["DB_PORT"]
        db_config["DB"] = os.environ["DB"]

    else:
        db_config["USER"] = get_config('db_config')['DB_CONFIG']["USER"]
        db_config["PW"] = get_config('db_config')['DB_CONFIG']["PW"]
        db_config["HOST"] = get_config('db_config')['DB_CONFIG']["HOST"]
        db_config["PORT"] = get_config('db_config')['DB_CONFIG']["PORT"]
        db_config["DB"] = get_config('db_config')['DB_CONFIG']["DB"]

    return db_config


def get_db_engine() -> Engine:
    db_config = get_db_info()

    engine_info = f'mysql+pymysql://{db_config["USER"]}:{db_config["PW"]}@{db_config["HOST"]}:{db_config["PORT"]}/{db_config["DB"]}'

    return create_engine(engine_info)


def db_executemany(query, args):
    db_config = get_db_info()

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
