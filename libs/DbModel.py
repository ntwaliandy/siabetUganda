import select

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.sql import select


class DbModel:
    def __init__(self):
        self.Base = automap_base()
        self.engine = create_engine("mysql+pymysql://root:@localhost/2021_sia?charset=utf8mb4")

    def get_users(self):
        return self.engine.execute("select * from sia_user")


db = DbModel()
if __name__ == '__main__':
    db().get_users()
