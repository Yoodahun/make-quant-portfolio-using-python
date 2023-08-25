import pymysql
from src.utilities import get_config

def db_executemany(query, args):
    db_config = get_config("db_config")["DB_CONFIG"]

    con = pymysql.connect(
        user=db_config["ROOT"],
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

